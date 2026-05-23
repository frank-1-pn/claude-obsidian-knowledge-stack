# Auto-patch claude_agent_sdk (Python) subprocess_cli.py on Windows so
# subagent spawns don't pop a console window per invocation. Idempotent
# — safe on every SessionStart. No-op if upstream changes the file in a
# way that loses our needle (writes a log line so you know to refresh).
#
# Bug: anyio.open_process is called without creationflags. On Windows
# this lets each subagent CLI spawn flash a Windows Terminal tab titled
# "claude" (empty, persistent after process exits).
#
# Logs to ~/.claude-agent-sdk/logs/autopatch.log
#
# Wire into ~/.claude/settings.json SessionStart hook:
#   {
#     "type": "command",
#     "command": "powershell.exe -ExecutionPolicy Bypass -File '~/.claude/scripts/claude-agent-sdk-autopatch.ps1' >/dev/null 2>&1 || true",
#     "timeout": 20
#   }

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $env:USERPROFILE '.claude-agent-sdk\logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir 'autopatch.log'

function Write-Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

# Find every subprocess_cli.py shipped with claude_agent_sdk
$roots = @(
    (Join-Path $env:USERPROFILE 'AppData\Roaming\Python'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python')
)
$files = @()
foreach ($root in $roots) {
    if (Test-Path $root) {
        $files += Get-ChildItem -Path $root -Recurse -Filter 'subprocess_cli.py' -ErrorAction SilentlyContinue |
                  Where-Object { $_.FullName -like '*claude_agent_sdk*' } |
                  Select-Object -ExpandProperty FullName
    }
}

if ($files.Count -eq 0) {
    Write-Log "no claude_agent_sdk subprocess_cli.py found, nothing to patch"
    exit 0
}

# Two patch sites: the main spawn (~line 474) and the version check (~line 728).

$mainOld = @'
            self._process = await anyio.open_process(
                cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=stderr_dest,
                cwd=self._cwd,
                env=process_env,
                user=self._options.user,
            )
'@.Replace("`r`n", "`n")

$mainNew = @'
            _open_kwargs = dict(
                stdin=PIPE,
                stdout=PIPE,
                stderr=stderr_dest,
                cwd=self._cwd,
                env=process_env,
                user=self._options.user,
            )
            if sys.platform == "win32":
                _CREATE_NO_WINDOW = 0x08000000
                _open_kwargs["creationflags"] = _CREATE_NO_WINDOW
            self._process = await anyio.open_process(cmd, **_open_kwargs)
'@.Replace("`r`n", "`n")

$verOld = @'
            with anyio.fail_after(2):  # 2 second timeout
                version_process = await anyio.open_process(
                    [self._cli_path, "-v"],
                    stdout=PIPE,
                    stderr=PIPE,
                )
'@.Replace("`r`n", "`n")

$verNew = @'
            with anyio.fail_after(2):  # 2 second timeout
                _v_kwargs = dict(stdout=PIPE, stderr=PIPE)
                if sys.platform == "win32":
                    _v_kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
                version_process = await anyio.open_process(
                    [self._cli_path, "-v"],
                    **_v_kwargs,
                )
'@.Replace("`r`n", "`n")

$importOld = "import shutil`nimport signal`n"
$importNew = "import shutil`nimport signal`nimport sys`n"

$patched = 0
$skipped = 0
foreach ($f in $files) {
    try {
        $raw = Get-Content -LiteralPath $f -Raw -Encoding utf8
        $norm = $raw.Replace("`r`n", "`n")
        $changed = $false

        if ($norm.Contains($mainNew)) {
            # already patched main
        } elseif ($norm.Contains($mainOld)) {
            $norm = $norm.Replace($mainOld, $mainNew); $changed = $true
        } else {
            Write-Log "main-spawn needle missing in $f"
        }

        if ($norm.Contains($verNew)) {
            # already patched version check
        } elseif ($norm.Contains($verOld)) {
            $norm = $norm.Replace($verOld, $verNew); $changed = $true
        } else {
            Write-Log "version-check needle missing in $f"
        }

        if ($changed -and -not $norm.Contains("import sys`n")) {
            $norm = $norm.Replace($importOld, $importNew)
        }

        if ($changed) {
            Set-Content -LiteralPath $f -Value $norm -Encoding utf8 -NoNewline
            $patched++
            Write-Log "patched $f"
        } else {
            $skipped++
        }
    } catch {
        Write-Log ("error patching {0}: {1}" -f $f, $_.Exception.Message)
    }
}

Write-Log "done: patched=$patched skipped=$skipped total=$($files.Count)"
exit 0
