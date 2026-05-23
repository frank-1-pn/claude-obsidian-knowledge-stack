# Auto-patch claude-mem worker-service.cjs after plugin upgrades.
#
# Idempotent: safe to run on every SessionStart. No-op if already patched.
# Logs to ~/.claude-mem/logs/autopatch.log
#
# Why this exists:
#   - claude-mem auto-updates from its marketplace on every Claude Code restart
#   - If you redirect summarization traffic from OpenRouter to another
#     OpenAI-compatible provider (e.g. by rewriting the chat-completions URL),
#     each upgrade overwrites your patch with the upstream openrouter.ai URL
#   - Without re-patching, every call returns 401 and your observation history
#     stops growing silently
#
# What this template patches (you adapt to your needs):
#   1. URL rewrite: openrouter.ai/api/v1/chat/completions  →  api.<your-provider>/v1/chat/completions
#   2. Optional: a truncation guard that prevents keptMessages=0 → 400
#      cascade. The needle below is for v13.x; verify against your version
#      before deploying
#
# Adapt the constants at top to match your provider and skip patches you
# don't need.

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $env:USERPROFILE '.claude-mem\logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir 'autopatch.log'

function Write-Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

# === ADAPT THESE ====================================================
$urlOld = 'openrouter.ai/api/v1/chat/completions'
$urlNew = 'api.<your-provider>/v1/chat/completions'

# Truncation-guard needle for claude-mem v13.x OpenRouter path.
# Verify with: rg "this.estimateTokens\(c.content\);if\(s.length>=n" against
# your installed worker-service.cjs. If absent, drop this whole block.
$truncOld = 'this.estimateTokens(c.content);if(s.length>=n||o+l>i){'
$truncNew = 'this.estimateTokens(c.content);if(s.length>0&&(s.length>=n||o+l>i)){'
# ====================================================================

# Locate every cached copy of worker-service.cjs. npx caches a separate copy
# under AppData\Local\npm-cache\_npx\<hash>\... whose hash changes per version
# — so 'find by name' is more robust than hard-coded paths.
$roots = @(
    (Join-Path $env:USERPROFILE '.claude\plugins'),
    (Join-Path $env:LOCALAPPDATA 'npm-cache\_npx')
)
$files = @()
foreach ($root in $roots) {
    if (Test-Path $root) {
        $files += Get-ChildItem -Path $root -Recurse -Filter 'worker-service.cjs' -ErrorAction SilentlyContinue |
                  Select-Object -ExpandProperty FullName
    }
}

if ($files.Count -eq 0) {
    Write-Log "no worker-service.cjs found, nothing to patch"
    exit 0
}

$patched = 0
$skipped = 0

foreach ($f in $files) {
    try {
        $raw = Get-Content -LiteralPath $f -Raw
        $changed = $false

        # URL patch
        if ($urlOld -and $urlNew -and $raw.Contains($urlOld)) {
            $raw = $raw.Replace($urlOld, $urlNew)
            $changed = $true
        }

        # Truncation-guard patch (optional; skip if needle absent)
        if ($truncOld -and $truncNew -and $raw.Contains($truncOld)) {
            $raw = $raw.Replace($truncOld, $truncNew)
            $changed = $true
        }

        if ($changed) {
            # Back up once per upgrade so you can compare diffs
            $backup = "$f.pre-autopatch"
            if (-not (Test-Path $backup)) { Copy-Item -LiteralPath $f -Destination $backup -Force }
            Set-Content -LiteralPath $f -Value $raw -NoNewline -Encoding utf8
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
