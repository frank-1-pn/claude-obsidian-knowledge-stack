# 03 — Feishu (Lark) bot bridge

This stack's mobile capture surface. **Optional** — skip if you only ever work
at your desktop.

**The runnable scripts are shipped in [`../scripts/feishu-bridge/`](../scripts/feishu-bridge/)**
— copy them to `~/.lark-cli/daemon/`, fill the placeholders, done (that folder's
`README.md` has a ~10-minute setup). The spec below explains what each script
does and the contracts the rest of this stack relies on — read it to understand
or modify the bridge, not because you must build it from scratch.

## What you'll end up with

- A long-running `lark-cli event +subscribe` daemon per bot, detached from
  any Claude Code session — survives `/compact`, session restart, terminal
  close.
- A per-session `Monitor` task in Claude Code that tails the daemon's NDJSON
  output file and pushes each new message into your conversation as a
  `task-notification`.
- A `notify-once.ps1` wrapper that routes outbound notifications back to the
  right bot (so finance-agent's `/compact` notice goes to its own chat, not
  the catch-all bot).
- A `/compact!` keyboard-macro flow: send `/compact!` from your phone, get a
  screenshot + confirmation, type-it + confirm again, then Enter. Two human
  checkpoints, no accidental fires.

## What you'll need before starting

- A Feishu developer account (free) and at least one self-built bot. If you
  want per-project routing (e.g. one bot per project), build as many as you
  want; the routing system in this spec scales to N.
- `lark-cli` installed globally: `npm install -g @larksuite/cli`
- `lark-cli auth login --as bot` to grant the bot the message read / send /
  recall permissions.

## Scope mapping vs this stack

| Capability you'll build | Where it shows up in *this* stack |
| --- | --- |
| daemon + monitor (offset-tracked tail) | Drives Pattern 2 (Feishu-driven ingest) in `ARCHITECTURE.md` |
| `notify-once.ps1 -AutoBot` | Routes `PostCompact` etc. to the right bot per session |
| `/compact!` macro | Lets you trigger context compaction from phone safely |
| `bot-registry.json` | Maps cwd / project to bot — useful for N projects |
| `binding-<pid>.json` | Per-session bot identity; written by `write-binding.ps1` |

---

# Bridge spec (what the shipped scripts do)

What the bridge *must do* and the file layout it must expose so the rest of
this stack's hooks (referenced from `config/settings-json.template.json`)
can find it. Build any way you like; the names below are what the templates
in this repo assume.

## Eight scripts (one-liner each)

Drop these under `~/.lark-cli/daemon/`:

| Script | Inputs | Job |
| --- | --- | --- |
| `start-bot.ps1` | `-Bot <name> [-Profile <profile>]` | Spawn detached `lark-cli event +subscribe --force ...` whose stdout goes to `%TEMP%\lark-<bot>-events.ndjson`, stderr to `%TEMP%\lark-<bot>-daemon.err.log`, PID to `%TEMP%\lark-<bot>.pid`. Idempotent (skip if pid file points to a live subscribe with matching `--profile`). Always sets `LARK_CLI_NO_PROXY=1` so bot secrets never transit a local HTTP proxy. On an unhealthy/orphaned daemon: kill the orphan matching this bot's `--profile`, `Start-Sleep -Seconds 3` (lets the Feishu service side release the old WebSocket connection), then reconnect with `--force` |
| `ensure-bot.ps1` | `-Bot <name> [-Profile <profile>]` | Health-check + heal. Rotate ndjson if >50MB (kill + rename + restart, also reset the offset file). Rotate err log if >10MB (same path). Prune `binding-*.json` whose PID is dead. Prune `lark-notify-once/*.last` >7 days old. Call `start-bot.ps1` if daemon unhealthy. Safe to run at every SessionStart, /compact, stream-ended |
| `monitor-bot.sh` | `<bot>` positional | `tail -c +OFFSET -F` the ndjson with offset bookkeeping per consumed line. Awk filter `^{"chat_id"` lets only real messages through. Add a `[COMPACT_TRIGGER]` marker line when message body is exactly `/compact!` and `sender_id` equals the operator's open_id |
| `write-binding.ps1` | `-Bot <name> [-ChatId ...] [-Profile ...] [-Alias ...] [-MonitorTaskId ...]` | Walk parent process chain to find `claude.exe`, look up the bot in `bot-registry.json` (`bots` map by short name), write `binding-<claude_pid>.json` with `claude_pid / bot / bot_alias / chat_id / profile / bound_at / monitor_task_id / source` |
| `notify-once.ps1` | `-AutoBot \| -ChatId ... [-Profile ...] -Text ... [-Tag <key>] [-MinIntervalSec 30]` | Bot-aware Feishu notifier with dedup. Resolution order for `-AutoBot`: (1) walk parent chain to `claude.exe` then read `binding-<pid>.json`; (2) match `$env:CLAUDE_PROJECT_DIR` against `bot-registry.json` `projects[].match_dir_contains`; (3) fall back to `registry.default`. Skip silently if same `chat_id + tag` was notified within the dedup window |
| `lark-send.ps1` | `-ChatId <oc_xxx> -BodyFile <path> [-Profile ...]` | Send a (possibly multi-line) text message reliably by calling the `lark-cli` Node entry (`run.js`) directly instead of the `.cmd` wrapper, which truncates multi-line args at the first newline on Windows. Reads the message body from a UTF-8 file so callers never fight PowerShell quoting |
| `find-claude.ps1`, `screenshot-window.ps1`, `send-keys.ps1` | various | For the `/compact!` macro — find the foreground claude.exe-rooted window, screenshot it, SendKeys into it with foreground-guard. Refuse to fire if foreground hwnd doesn't match the passed hwnd |

See [`feishu-bot-runtime.md`](../scripts/feishu-bridge/feishu-bot-runtime.md) for the
operating manual you reach for *after* the bridge is up — send/receive norms,
failure-symbol lookup, orphan-subscribe recovery, and the risk-operation
confirmation flow. It is meant to be loaded as a skill once a session has a
bot bound, not read up front.

## File layout under `~/.lark-cli/daemon/`

```
start-bot.ps1
ensure-bot.ps1
monitor-bot.sh
write-binding.ps1
notify-once.ps1
lark-send.ps1
find-claude.ps1
screenshot-window.ps1
send-keys.ps1
bot-registry.json                   # routing config; see schema below
binding-<claude_pid>.json           # generated per session by write-binding
```

Runtime files under `%TEMP%`:

```
lark-<bot>-events.ndjson            # daemon stdout
lark-<bot>-daemon.err.log           # daemon stderr (SDK noise lives here)
lark-<bot>.pid                      # current daemon PID
lark-<bot>-monitor.offset           # monitor's resume position
lark-notify-once/<chat>.<tag>.last  # dedup state for notify-once
```

## `bot-registry.json` schema

```json
{
  "_doc": "Bot registry. 'bots' = per-bot config for daemon scripts. 'default' + 'projects' = AutoBot fallback for notify-once.",
  "bots": {
    "<short-name-1>": {
      "chat_id": "oc_<your-p2p-chat-id>",
      "profile": "",
      "alias": "<human-readable name>"
    },
    "<short-name-2>": {
      "chat_id": "oc_<...>",
      "profile": "<lark-cli profile name>",
      "alias": "<...>"
    }
  },
  "default": {
    "chat_id": "oc_<your-p2p-chat-id>",
    "profile": "",
    "alias": "<human-readable name>"
  },
  "projects": [
    {
      "match_dir_contains": "<substring of CLAUDE_PROJECT_DIR>",
      "chat_id": "oc_<...>",
      "profile": "<...>",
      "alias": "<...>"
    }
  ]
}
```

## NDJSON event format

Each line written by `lark-cli event +subscribe --compact --as bot` is a
single-line JSON object that starts with `{"chat_id":"oc_..."`. The fields
you care about:

```json
{
  "chat_id": "oc_xxx",
  "chat_type": "p2p",
  "content": "<user message>",
  "create_time": "1779511380879",
  "id": "om_xxx",
  "message_id": "om_xxx",
  "message_type": "text",
  "sender_id": "ou_xxx",
  "timestamp": "1779511381313",
  "type": "im.message.receive_v1"
}
```

`monitor-bot.sh` should let only these `{"chat_id"...}`-prefixed lines
through; everything else from `lark-cli` is connection / SDK noise.

## Hook wiring

`~/.claude/settings.json` `PostCompact` hook calls `notify-once.ps1
-AutoBot ... -Tag postcompact -MinIntervalSec 30` (template in
`config/settings-json.template.json`). The rest of the bridge runs out of
band as a daemon + per-session Monitor.

## Hard rules (load-bearing)

1. **The daemon survives /compact and session restart.** Implement as
   `Start-Process -WindowStyle Hidden -RedirectStandardOutput ...
   -RedirectStandardError ...`. Do NOT spawn under the Monitor task's
   process group.
2. **Restarting the daemon truncates the ndjson** (Start-Process redirect
   is write-truncate). `start-bot.ps1` must therefore reset the offset
   file when it (re)starts. Otherwise live Monitors point past EOF and
   miss events until next restart.
3. **`send-keys.ps1` must refuse non-foreground targets.** If
   `GetForegroundWindow()` ≠ the passed hwnd, exit with
   `{error: "not_foreground"}` and do not send. This is the load-bearing
   safety for `/compact!`.
4. **External-side-effect hooks must be rate-limited.** Use
   `notify-once.ps1` (or equivalent) for any hook that sends Feishu
   messages. A naive SessionEnd hook caused a 286-message bombardment in
   2026-05 because Claude Code mis-fires SessionEnd repeatedly when
   PostCompact's JSON output validation fails.
5. **PostCompact hook JSON output schema:** Claude Code's hook validator
   only allows `hookSpecificOutput.additionalContext` for `UserPromptSubmit
   / PostToolUse / PostToolBatch`. Do NOT emit that shape from PostCompact
   — it fails validation and triggers cascade misbehaviors. Either emit
   `{"continue":true,"suppressOutput":true}` or no JSON at all.
6. **Bot secrets live in OS keychain via `lark-cli`'s config**, never in
   committed files. If you have a sync-to-git workflow for the bridge
   scripts, put real values in a host-local `~/.lark-cli/sync-secrets.local.json`
   and have your sync script substitute them before commit.

## Liveness rules (operator-facing)

`messages-send ok=true` and "daemon process alive" both lie about whether
*inbound* messages reach Claude Code. The only positive signals:

1. **An inbound `task-notification` just arrived** whose `task-id`
   matches the Monitor task this session started → link is alive.
2. **A `Monitor "..." stream ended` notification appeared** for this
   session's Monitor task → link is dead. Restart Monitor immediately;
   the offset file means you don't lose events from while it was down.

Necessary-but-not-sufficient: a `node.exe ... event +subscribe` process
matching this bot's `--profile` exists. Orphan scenario: process alive,
Monitor dead → events vanish silently.

Default behavior on any `/compact` or new session: assume orphan, run
`ensure-bot.ps1` + restart Monitor + rewrite `binding-<pid>.json`.

**Caveat — tool-based liveness checks that look reasonable but are not**:
`TaskList` / `TaskGet` do **not** track Monitor watches. `TaskGet
<monitor-task-id>` returns `"Task not found"` even while the Monitor is
alive and healthy — an empty `TaskList` is not evidence of death, so never
use either tool to judge liveness. Likewise, a heartbeat `messages-send`
returning `ok=true` only proves the *outbound* path works; it says nothing
about whether inbound events are reaching Claude. Use only the two signals
above (inbound task-notification id-match, or a `stream ended` notice).

For the full ranked liveness signal table, the orphan-subscribe danger
scenario, and the reconnect flow, see
[`feishu-bot-runtime.md`](../scripts/feishu-bridge/feishu-bot-runtime.md).

### External Watchdog (defense in depth)

Register `feishu-watchdog.ps1` (shipped alongside the other scripts in
`scripts/feishu-bridge/`) as a Windows scheduled task that runs every ~30
minutes. It silently checks whether the bot's `event +subscribe` process is
alive and only sends a Feishu alert on death — no heartbeat spam. This
catches the case where nobody is actively chatting with Claude and would
otherwise not notice the daemon died. See the header comment in the script
for the exact `schtasks` registration command.

---

## Wiring back into this stack

1. The bridge's notion of "global CLAUDE.md" overlaps with this stack's
   `config/global-claude-md.template.md`. Merge — the template here is
   designed to be the canonical "global" CLAUDE.md with a startup self-check
   that calls `ensure-bot.ps1` + `monitor-bot.sh` + `write-binding.ps1`.
2. The PostCompact hook from the template in
   `config/settings-json.template.json` already points at
   `notify-once.ps1 -AutoBot` — no change needed.
3. Decide your routing convention:
   - Per-project bots → register each in `~/.lark-cli/config.json`, add an
     entry under `bots` in `bot-registry.json`, and add a `projects[]` entry
     if a specific working directory should auto-resolve to that bot
   - One catch-all bot → just keep the default

## Mobile-side setup

On your phone:

1. Install **Feishu (Lark)** app, sign in, find your bot in Contacts.
2. Open a 1-1 chat with the bot (P2P). The `chat_id` for that conversation
   goes in your `bot-registry.json`.
3. Test by sending "hi" — your desktop Claude Code session should see a
   `task-notification` within a couple of seconds.

If it doesn't, walk the liveness rules above to diagnose.

## Done when

- A message from your phone arrives in Claude Code as a `task-notification`
- A `messages-send` from Claude returns `ok=true` and you see the message
  on your phone
- `/compact!` from phone screenshots → confirm → types → confirm → Enter,
  all via Feishu

Now you have a mobile inbox into the vault.

Move on to `setup/05-wechat-mcp.md`.
