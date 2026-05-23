# Sanity-check that every piece of the claude-obsidian knowledge stack is
# in place after you follow setup/*.md. Prints a checklist with ✓ / ✗.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/check-bootstrap.ps1
#
# Override the vault path with -VaultPath:
#   ... -VaultPath 'D:\my-vault'

param(
    [string]$VaultPath = (Join-Path $env:USERPROFILE 'Documents\knowledge-vault')
)

$ErrorActionPreference = 'Continue'

function Check([string]$name, [scriptblock]$test, [string]$hint = '') {
    try {
        $ok = & $test
        $mark = if ($ok) { '✓' } else { '✗' }
        Write-Host "$mark $name"
        if (-not $ok -and $hint) { Write-Host "    → $hint" -ForegroundColor Yellow }
    } catch {
        Write-Host "✗ $name (error: $($_.Exception.Message))"
        if ($hint) { Write-Host "    → $hint" -ForegroundColor Yellow }
    }
}

Write-Host ""
Write-Host "=== Prereqs (setup/01) ===" -ForegroundColor Cyan
Check "Node 20+ installed" { (node -v 2>$null) -match '^v(2\d|[3-9]\d)' } "Install Node 20 LTS from nodejs.org"
Check "npm available" { (npm -v 2>$null).Length -gt 0 } "Comes with Node"
Check "Python 3.12+ installed" { (python --version 2>$null) -match 'Python 3\.(1[2-9]|[2-9]\d)' } "Install from python.org; tick 'Add to PATH'"
Check "Git installed" { (git --version 2>$null).Length -gt 0 } "Install from git-scm.com/download/win"
Check "Windows Terminal present" { Test-Path "$env:LOCALAPPDATA\Microsoft\WindowsApps\wt.exe" } "Install from Microsoft Store"

Write-Host ""
Write-Host "=== Claude Code (setup/02) ===" -ForegroundColor Cyan
Check "claude CLI installed" { (claude --version 2>$null).Length -gt 0 } "npm install -g @anthropic-ai/claude-code"
Check "~/.claude/CLAUDE.md exists" { Test-Path (Join-Path $env:USERPROFILE '.claude\CLAUDE.md') } "Copy from config/global-claude-md.template.md and fill placeholders"
Check "~/.claude/settings.json exists" { Test-Path (Join-Path $env:USERPROFILE '.claude\settings.json') } "Created on first claude run"
Check "~/.claude/scripts/ exists" { Test-Path (Join-Path $env:USERPROFILE '.claude\scripts') } "mkdir; helpers like genimg.py + autopatches go here"
Check "claude-agent-sdk-autopatch.ps1 in place" { Test-Path (Join-Path $env:USERPROFILE '.claude\scripts\claude-agent-sdk-autopatch.ps1') } "Copy from config/claude-agent-sdk-autopatch.ps1"

Write-Host ""
Write-Host "=== Obsidian vault (setup/04) ===" -ForegroundColor Cyan
Check "Vault folder exists" { Test-Path $VaultPath } "Default: $env:USERPROFILE\Documents\knowledge-vault; override -VaultPath"
Check "  wiki/ exists" { Test-Path (Join-Path $VaultPath 'wiki') } "mkdir wiki"
Check "  wiki/sources/ exists" { Test-Path (Join-Path $VaultPath 'wiki\sources') } "mkdir wiki\sources"
Check "  wiki/meta/ exists" { Test-Path (Join-Path $VaultPath 'wiki\meta') } "mkdir wiki\meta"
Check "  wiki/_attachments/ exists" { Test-Path (Join-Path $VaultPath 'wiki\_attachments') } "mkdir wiki\_attachments"
Check "  .raw/ exists" { Test-Path (Join-Path $VaultPath '.raw') } "mkdir .raw"
Check "  wiki/hot.md exists" { Test-Path (Join-Path $VaultPath 'wiki\hot.md') } "Copy from vault/skeletons/hot.template.md"
Check "  wiki/index.md exists" { Test-Path (Join-Path $VaultPath 'wiki\index.md') } "Copy from vault/skeletons/index.template.md"
Check "  wiki/log.md exists" { Test-Path (Join-Path $VaultPath 'wiki\log.md') } "Copy from vault/skeletons/log.template.md"
Check "  wiki/meta/notes-graph.md exists" { Test-Path (Join-Path $VaultPath 'wiki\meta\notes-graph.md') } "Copy from vault/skeletons/notes-graph.template.md"
Check "  vault CLAUDE.md exists" { Test-Path (Join-Path $VaultPath 'CLAUDE.md') } "Copy from config/vault-claude-md.template.md and fill placeholders"

Write-Host ""
Write-Host "=== WeChat MCP (setup/05; OPTIONAL) ===" -ForegroundColor Cyan
$wechatReachable = $false
try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:4545/mcp' -Method POST -Body '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}' -ContentType 'application/json' -Headers @{Accept = 'application/json,text/event-stream'} -TimeoutSec 3 -ErrorAction Stop
    $wechatReachable = $resp.StatusCode -eq 200
} catch {}
Check "wechatDownload MCP reachable on :4545" { $wechatReachable } "Start the wechatDownload desktop app (tray icon)"
Check "wechatDownload registered in ~/.claude.json" { (Get-Content (Join-Path $env:USERPROFILE '.claude.json') -Raw -ErrorAction SilentlyContinue) -match 'wechatDownload' } "Add the entry from config/mcp-config.example.json"

Write-Host ""
Write-Host "=== Image generation (setup/06; OPTIONAL) ===" -ForegroundColor Cyan
Check "API key file exists" { Test-Path (Join-Path $env:USERPROFILE 'Desktop\openai_api.txt') } "Drop sk-... on line 1 of ~/Desktop/openai_api.txt"
Check "genimg.py in ~/.claude/scripts/" { Test-Path (Join-Path $env:USERPROFILE '.claude\scripts\genimg.py') } "Copy from config/genimg.py; replace DEFAULT_BASE_URL"

Write-Host ""
Write-Host "=== claude-mem (setup/07; OPTIONAL) ===" -ForegroundColor Cyan
Check "claude-mem plugin cache exists" { (Get-ChildItem (Join-Path $env:USERPROFILE '.claude\plugins\cache\thedotmack\claude-mem') -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0 } "Install via claude /plugins; restart session"
Check "~/.claude-mem/ exists" { Test-Path (Join-Path $env:USERPROFILE '.claude-mem') } "Auto-created on first run"
Check "claude-mem worker running" {
    $port = 37777..37800 | Where-Object {
        (Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue) -ne $null
    } | Select-Object -First 1
    $port -ne $null
} "Run: powershell -File ~/.claude/scripts/claude-mem-start.ps1"

Write-Host ""
Write-Host "=== Feishu bridge (setup/03; OPTIONAL) ===" -ForegroundColor Cyan
Check "~/.lark-cli/ exists" { Test-Path (Join-Path $env:USERPROFILE '.lark-cli') } "lark-cli config init"
Check "~/.lark-cli/daemon/ exists" { Test-Path (Join-Path $env:USERPROFILE '.lark-cli\daemon') } "Clone github.com/<user>/feishu-claude-code-bridge and copy daemon/"
Check "lark-cli on PATH" { (Get-Command lark-cli -ErrorAction SilentlyContinue) -ne $null } "npm install -g @larksuite/cli; add %APPDATA%\npm to PATH"

Write-Host ""
Write-Host "Done. Anything marked ✗ means the next step is either install or 'copy from this repo's templates and fill placeholders'." -ForegroundColor Green
