# Silent liveness watchdog for one Feishu bot's `event +subscribe` daemon.
#
# Why this exists: the in-session liveness rules (see feishu-bot-runtime.md)
# only catch a dead daemon while somebody is actively chatting with Claude —
# they rely on an inbound task-notification or a "stream ended" event to
# surface. If nobody opens a Claude Code session for hours, a dead daemon
# goes unnoticed until the next real message silently vanishes. This script
# is meant to run OUTSIDE any Claude Code session, on a plain Windows
# scheduled task, so it keeps checking even when no session is open.
#
# Behavior each run:
#   - Check whether the `event +subscribe` process for -Bot (matched by
#     --profile, or "no --profile" for the default bot) is alive.
#   - Alive  -> do nothing, print nothing, send nothing. (Never turn this
#               into a periodic heartbeat — that becomes alert spam.)
#   - Dead   -> send ONE Feishu alert to that bot's own chat via lark-cli,
#               then exit. The alert tells the human to say anything to
#               Claude (triggers SessionStart / the startup self-check,
#               which self-heals) or restart manually.
#
# Usage:
#   feishu-watchdog.ps1 -Bot <bot1|coding|finance|...> [-Profile <profile>] [-ChatId <oc_xxx>]
#
# Chat-id resolution when -ChatId is not passed explicitly:
#   1. Look up -Bot in <USER_HOME>\.lark-cli\daemon\bot-registry.json under
#      the `bots` map.
#   2. Fall back to the registry's `default` entry.
#   3. Fall back to the hardcoded placeholder below (fill in your own before
#      relying on this in production).
#
# Register as a Windows scheduled task every ~30 minutes, one task per bot
# you want watched (adjust the path and -Bot/-Profile to your setup):
#
#   schtasks /Create /TN "FeishuBotWatchdog-bot1" /SC MINUTE /MO 30 ^
#     /TR "powershell.exe -ExecutionPolicy Bypass -File <USER_HOME>\.lark-cli\daemon\feishu-watchdog.ps1 -Bot bot1" ^
#     /RL LIMITED /F
#
#   schtasks /Create /TN "FeishuBotWatchdog-coding" /SC MINUTE /MO 30 ^
#     /TR "powershell.exe -ExecutionPolicy Bypass -File <USER_HOME>\.lark-cli\daemon\feishu-watchdog.ps1 -Bot coding -Profile <profile-name>" ^
#     /RL LIMITED /F
#
# List / remove:
#   schtasks /Query /TN "FeishuBotWatchdog-bot1"
#   schtasks /Delete /TN "FeishuBotWatchdog-bot1" /F

param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$Bot,
    [string]$Profile = '',
    [string]$ChatId = ''
)

$ErrorActionPreference = 'SilentlyContinue'
$env:PATH = "$env:PATH;$env:APPDATA\npm"
$env:LARK_CLI_NO_PROXY = '1'

$daemonDir = "$env:USERPROFILE\.lark-cli\daemon"
$registry  = Join-Path $daemonDir 'bot-registry.json'

function Test-IsThisBotsSubscribe {
    param([string]$CmdLine)
    if ($CmdLine -notlike '*event*subscribe*') { return $false }
    if ($Profile) { return ($CmdLine -like "*--profile $Profile*") }
    # No -Profile => the default bot => process must NOT carry a --profile flag
    return ($CmdLine -notlike '*--profile*')
}

# Resolve the alert chat_id: explicit -ChatId wins, else consult the registry.
if (-not $ChatId -and (Test-Path $registry)) {
    try {
        $reg = Get-Content -LiteralPath $registry -Raw -Encoding utf8 | ConvertFrom-Json
        if ($reg.bots -and ($reg.bots.PSObject.Properties.Name -contains $Bot)) {
            $ChatId = $reg.bots.$Bot.chat_id
        } elseif ($reg.default) {
            $ChatId = $reg.default.chat_id
        }
    } catch { }
}
if (-not $ChatId) { $ChatId = 'oc_REPLACE_WITH_YOUR_CHAT_ID' }

$alive = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { Test-IsThisBotsSubscribe -CmdLine $_.CommandLine }

if (-not $alive) {
    $ts = Get-Date -Format 'MM-dd HH:mm'
    $text = "⚠️ $ts 检测到 bot（$Bot）长连接已断。请在电脑前向 Claude Code 敲一句话（或重启会话），我会自检恢复。"
    $cliArgs = @('im', '+messages-send', '--chat-id', $ChatId, '--text', $text, '--as', 'bot')
    if ($Profile) { $cliArgs = @('--profile', $Profile) + $cliArgs }
    & lark-cli @cliArgs | Out-Null
}
# else: daemon is alive — stay completely silent, no heartbeat spam.
