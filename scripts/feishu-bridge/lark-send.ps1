<#
lark-send.ps1 — reliably send a (multi-line) text message to Feishu.

WHY THIS EXISTS: calling `lark-cli.cmd --text <multiline>` on Windows truncates
the message at the FIRST newline (the .cmd batch wrapper / cmd.exe mangles
newline-containing arguments) — the server receives only line 1. Confirmed
2026-06-12 via messages-mget. This helper invokes the lark-cli node entry
DIRECTLY (node.exe is a real PE, argv newlines survive), so full multi-line text
is delivered.

Usage:
    powershell -ExecutionPolicy Bypass -File lark-send.ps1 -TextFile <utf8.txt> [-ChatId oc_xxx] [-Profile work-profile]

Default ChatId = Bot1 (oc_REPLACE_WITH_YOUR_CHAT_ID).
Reads the file as UTF-8 (-Raw). Returns lark-cli JSON on stdout.
#>
param(
    [Parameter(Mandatory = $true)][string]$TextFile,
    [string]$ChatId = 'oc_REPLACE_WITH_YOUR_CHAT_ID',
    [string]$Profile
)

$ErrorActionPreference = 'Stop'
$run = (Join-Path $env:APPDATA 'npm/node_modules/@larksuite/cli/scripts/run.js')

if (-not (Test-Path -LiteralPath $TextFile)) { Write-Error "text file not found: $TextFile"; exit 1 }
if (-not (Test-Path -LiteralPath $run))      { Write-Error "lark-cli run.js not found: $run"; exit 1 }

$t = Get-Content -Raw -Encoding UTF8 $TextFile
# Defensive: ASCII double-quotes in the text break PowerShell->native-exe arg
# passing (the " is treated as a quote delimiter -> "positional arguments" error).
# Replace with full-width ＂ — harmless for Feishu prose, bulletproof for sending.
$t = $t -replace '"', [char]0xFF02
$cliArgs = @('im', '+messages-send', '--chat-id', $ChatId, '--text', $t, '--as', 'bot')
if ($Profile) { $cliArgs += @('--profile', $Profile) }

& node $run @cliArgs
exit $LASTEXITCODE
