# Feishu (Lark) bridge — runnable scripts

This folder ships the **actual working scripts** for the Feishu ⇆ Claude Code
long-connection bridge described in [`../../setup/03-feishu-bot.md`](../../setup/03-feishu-bot.md).
Copy them to `~/.lark-cli/daemon/`, replace the placeholders, and you have the
same mobile-capture system this stack runs on — no need to rebuild from spec.

> **All real IDs are placeholders.** Every `oc_REPLACE_*` / `ou_REPLACE_*` and
> every value in `bot-registry.template.json` must be filled with your own
> before anything works. Nothing here contains live credentials. Bot
> app-id/secret never live in these files — they stay in `lark-cli`'s own
> config (OS keychain).

Platform: **Windows** (PowerShell 5.1+ for the `.ps1`, Git Bash for
`monitor-bot.sh`). The bridge drives Windows-only pieces (`SendKeys`, window
capture). The rest of the stack is cross-platform; only this bridge is tied to
Windows today.

---

## Mental model (read this first)

Three layers, each with a different lifetime:

```
┌─ daemon ────────────┐   per bot, PERSISTENT (survives /compact, session
│ lark-cli event      │   restart, terminal close). Subscribes to Feishu over
│  +subscribe --force │   WebSocket, appends every event to an NDJSON file in
│  → %TEMP%/...ndjson │   %TEMP%. Started/healed by start-bot.ps1 / ensure-bot.ps1.
└─────────┬───────────┘
          │ tails the NDJSON by byte offset
┌─────────▼───────────┐   per Claude Code session. A Monitor watch runs
│ monitor-bot.sh      │   monitor-bot.sh, which tails the daemon's NDJSON and
│ → task-notification │   surfaces each new message into the conversation.
└─────────┬───────────┘   Dies with the session; the daemon does NOT.
          │ writes/reads
┌─────────▼───────────┐   per session. binding-<claude_pid>.json maps THIS
│ binding + registry  │   Claude process → which bot it owns, so outbound
│ → routes notify     │   hooks (notify-once.ps1) reply on the right bot.
└─────────────────────┘
```

Why the split: the daemon must outlive `/compact` (which resets the Claude
session) so inbound messages are never dropped; the Monitor is cheap and
per-session; the binding file lets N concurrent sessions each own a different
bot without crosstalk.

---

## File inventory

| File | Runtime | Job |
| --- | --- | --- |
| `start-bot.ps1` | PowerShell | Spawn the detached `lark-cli event +subscribe` daemon for one bot. stdout→`%TEMP%/lark-<bot>-events.ndjson`, stderr→`...err.log`, pid→`...pid`. Idempotent. Forces `LARK_CLI_NO_PROXY=1` so bot traffic never transits a local proxy. |
| `ensure-bot.ps1` | PowerShell | Health-check + heal the daemon. Rotates the NDJSON (>50 MB) and err log (>10 MB), prunes dead `binding-*.json` and stale notify dedup locks, restarts the daemon if unhealthy, and writes this session's binding. **Safe to run at every SessionStart / after /compact.** This is the one command you call to "make sure the connection is up". |
| `monitor-bot.sh` | Git Bash | Tail the daemon's NDJSON by saved byte offset (so a restart resumes exactly, never replays). Lets only real `{"chat_id"...}` messages through; emits a `[COMPACT_TRIGGER]` marker when the operator sends exactly `/compact!`. Run as a persistent Monitor watch. |
| `write-binding.ps1` | PowerShell | Walk the parent-process chain to find this `claude.exe`, look the bot up in `bot-registry.json`, and write `binding-<claude_pid>.json`. Usually called for you by `ensure-bot.ps1`. |
| `notify-once.ps1` | PowerShell | Bot-aware outbound notifier with dedup. `-AutoBot` resolves the right bot via (1) binding file → (2) `CLAUDE_PROJECT_DIR` match in registry → (3) registry `default`. Used by the `PostCompact` hook. |
| `lark-send.ps1` | PowerShell | Send a (multi-line) text message reliably. Calls the `lark-cli` Node entry directly because the `.cmd` wrapper truncates multi-line args at the first newline on Windows. Reads the body from a UTF-8 file. |
| `find-claude.ps1` / `screenshot-window.ps1` / `send-keys.ps1` | PowerShell | The `/compact!` keyboard-macro trio: find the foreground claude.exe window, screenshot it, and `SendKeys` into it — with a foreground guard that refuses to type into the wrong window. |
| `bot-registry.template.json` | config | Routing config. Copy to `bot-registry.json`, fill real `chat_id`s. `bots` = per-bot config; `default` + `projects` = AutoBot fallback for `notify-once.ps1`. |

Generated at runtime (not shipped): `binding-<pid>.json` per session, and in
`%TEMP%`: `lark-<bot>-events.ndjson`, `...-daemon.err.log`, `...pid`,
`lark-<bot>-monitor.offset`, `lark-notify-once/<chat>.<tag>.last`.

---

## Setup (≈10 min once you have a bot)

### 0. Prereqs
- A Feishu self-built bot (free dev account). For N projects, build N bots.
- `npm install -g @larksuite/cli`, then `lark-cli auth login --as bot` to grant
  message read / send / recall. Per-bot credentials live in `lark-cli`'s config
  (and, for extra bots, a named `--profile`).

### 1. Install the scripts
Copy everything in this folder to `~/.lark-cli/daemon/`:
```bash
mkdir -p ~/.lark-cli/daemon
cp start-bot.ps1 ensure-bot.ps1 monitor-bot.sh write-binding.ps1 \
   notify-once.ps1 lark-send.ps1 find-claude.ps1 screenshot-window.ps1 \
   send-keys.ps1 ~/.lark-cli/daemon/
cp bot-registry.template.json ~/.lark-cli/daemon/bot-registry.json
```

### 2. Fill the placeholders (required)
Replace every placeholder with your real values:

| Placeholder | Where | What it is |
| --- | --- | --- |
| `oc_REPLACE_WITH_YOUR_CHAT_ID` | `bot-registry.json`, `notify-once.ps1`, `lark-send.ps1` | The **p2p chat_id** between you and the bot (from a message event, or `lark-cli im chats list`). |
| `oc_REPLACE_WITH_CHAT_ID_FOR_BOT2` | `bot-registry.json` | chat_id for a second bot (delete the `work` entry if you only have one). |
| `ou_REPLACE_WITH_YOUR_OPEN_ID` | `monitor-bot.sh` (`MY_OPEN_ID`) | **Your** Feishu open_id — the only sender allowed to fire `/compact!`. |
| `work-profile` | `bot-registry.json` (+ examples) | A `lark-cli --profile` name for an extra bot; empty string `""` = default config. |

The `.ps1` scripts resolve paths from `$env:APPDATA` / `$env:USERPROFILE`, and
`monitor-bot.sh` resolves `%TEMP%` automatically (override with `LARK_TMP` if
your daemon writes elsewhere) — so no hard-coded home paths to edit.

### 3. Start the daemon (persistent)
```bash
powershell -ExecutionPolicy Bypass -File ~/.lark-cli/daemon/ensure-bot.ps1 -Bot bot1
# extra bot with its own lark-cli profile:
# ...ensure-bot.ps1 -Bot work -Profile work-profile
```
> ⚠️ Pass `-File` with **forward slashes** (`C:/Users/...`) — Git Bash mangles
> backslashes in the argument.

### 4. Start the Monitor (per session, in Claude Code)
Start a persistent Monitor watch running:
```bash
bash ~/.lark-cli/daemon/monitor-bot.sh bot1
```
New Feishu messages now arrive in the session as `task-notification`s.

### 5. Wire the PostCompact hook (optional but recommended)
In `~/.claude/settings.json`, add a `PostCompact` hook that calls
`notify-once.ps1 -AutoBot -Text '...' -Tag postcompact -MinIntervalSec 30`
(see `../../config/settings-json.template.json`). This pings the right bot when
a session compacts.

---

## Hard rules (load-bearing — don't "fix" these away)

1. **The daemon must outlive the session.** It's spawned detached
   (`Start-Process -WindowStyle Hidden`), NOT under the Monitor's process
   group. After `/compact` the Monitor dies but the daemon keeps receiving —
   re-attach a Monitor, don't restart the daemon.
2. **Restarting the daemon truncates the NDJSON**, so `start-bot.ps1` resets
   the offset file on (re)start; otherwise live Monitors point past EOF and go
   silent until the next restart.
3. **`send-keys.ps1` refuses non-foreground targets.** If the foreground
   window ≠ the passed window handle it exits without typing. This is the
   safety interlock for `/compact!`.
4. **Outbound hooks must be rate-limited** via `notify-once.ps1` (dedup by
   `chat_id + tag`). A naive always-send hook once produced a 286-message
   bombardment.
5. **Liveness is about INBOUND, not outbound.** `messages-send ok=true` and
   "daemon process alive" only prove you can *send*. The trustworthy signal
   that messages *reach* Claude is an inbound `task-notification` whose task-id
   matches this session's Monitor — or the absence of a `Monitor "..." stream
   ended` notice. After `/compact`, assume the old Monitor is dead and
   re-attach.

---

## How an operator (or AI) drives it

- **"Is the connection up?"** → don't trust send/heartbeat. Check for a recent
  inbound `task-notification` on this session's Monitor id, or that no
  `stream ended` notice fired. If unsure, run `ensure-bot.ps1` and re-attach a
  Monitor.
- **New session / after /compact** → run `ensure-bot.ps1 -Bot <bot>` then start
  `monitor-bot.sh <bot>`; the binding + heartbeat are handled.
- **Reply to a Feishu-originated message** → always send back via the bot
  (`lark-send.ps1` for long text, `lark-cli im +messages-send` for short), not
  only into the terminal — otherwise the phone user thinks it's down.

See [`../../setup/03-feishu-bot.md`](../../setup/03-feishu-bot.md) for the full
rationale, the NDJSON event schema, and the `/compact!` two-checkpoint flow.
