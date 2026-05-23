# Idempotent claude-mem worker autostart.
#
# Wire into a Windows scheduled task (Logon trigger) so the cross-session
# memory worker is up as soon as you sign in. Also safe to run from a
# SessionStart hook or by hand.
#
# Behavior:
#   1. Run claude-mem-autopatch.ps1 first (re-apply URL / truncation patches
#      in case CC just auto-upgraded the plugin)
#   2. If the worker port is already bound, exit silently
#   3. Otherwise, inject HTTPS_PROXY (if your provider needs it) and
#      run `npx -y claude-mem start`
#   4. Verify the port is listening after a short wait
#
# Logs to ~/.claude-mem/logs/autostart.log
#
# Adapt the constants at top to match your local setup.

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $env:USERPROFILE '.claude-mem\logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir 'autostart.log'

function Write-Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

# === ADAPT THESE ====================================================
$WorkerPort = 37783                   # match CLAUDE_MEM_WORKER_PORT in ~/.claude-mem/settings.json
$Npx        = 'C:\Program Files\nodejs\npx.cmd'
$Proxy      = ''                      # set to 'http://127.0.0.1:<port>' if your provider is unreachable without it; otherwise leave empty
# ====================================================================

try {
    Write-Log "autostart triggered"

    # Re-apply patches if available. Runs even if worker is up — so the next
    # restart picks up patched copies.
    $autopatch = Join-Path $PSScriptRoot 'claude-mem-autopatch.ps1'
    if (Test-Path $autopatch) {
        try { & $autopatch | Out-Null; Write-Log "autopatch ran (see autopatch.log)" }
        catch { Write-Log "autopatch errored: $_" }
    } else {
        Write-Log "autopatch script absent at $autopatch (skipping)"
    }

    # Already running?
    $existing = Get-NetTCPConnection -LocalPort $WorkerPort -State Listen -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Log "worker already listening on $WorkerPort (pid=$($existing.OwningProcess))"
        exit 0
    }

    if (-not (Test-Path $Npx)) { throw "npx not found at $Npx" }

    if ($Proxy) {
        $env:HTTPS_PROXY = $Proxy
        $env:HTTP_PROXY  = $Proxy
        $env:NO_PROXY    = '127.0.0.1,localhost'
        Write-Log "proxy injected: $Proxy"
    }

    $output = & $Npx '-y' 'claude-mem' 'start' 2>&1 | Out-String
    Write-Log "start output: $($output.Trim())"

    Start-Sleep -Seconds 3
    $check = Get-NetTCPConnection -LocalPort $WorkerPort -State Listen -ErrorAction SilentlyContinue
    if ($check) {
        Write-Log "worker up (pid=$($check.OwningProcess))"
    } else {
        Write-Log "WARN: worker did not bind $WorkerPort within 3s"
    }
} catch {
    Write-Log "ERROR: $_"
    exit 1
}
