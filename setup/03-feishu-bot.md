# 03 — Feishu (Lark) bot bridge

This stack's mobile capture surface. **Optional** — skip if you only ever work
at your desktop.

The mechanism is implemented in a sibling repo:

> **`<your-github-user>/feishu-claude-code-bridge`** — the companion repo
> that implements the daemon + monitor + /compact macro + per-session bot
> routing. Each operator builds their own from the architecture in this
> stack's `ARCHITECTURE.md` and the bridge repo's `ARCHITECTURE.md` (which
> in turn extends from `feishu-bot-runtime` patterns + the seven fixes
> documented in `daemon/PLAN.md`).

This file is the bridge between this stack and that one. Read this first,
then follow that repo's `README.md` start-to-finish.

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

- A Feishu developer account (free) and one self-built bot per "channel" you
  want. Three feels useful: a primary inbox, a per-project bot, a project-2
  bot. You can start with one.
- `lark-cli` installed globally: `npm install -g @larksuite/cli`
- `lark-cli auth login --as bot` to grant the bot the message read/send/recall
  permissions.

## Scope mapping vs this stack

| Capability in `feishu-claude-code-bridge` | Where it shows up in *this* stack |
| --- | --- |
| daemon + monitor (v4) | Drives Pattern 2 (Feishu-driven ingest) in `ARCHITECTURE.md` |
| `notify-once.ps1 -AutoBot` | Routes `PostCompact` etc. to the right bot per session |
| `/compact!` macro | Lets you trigger context compaction from phone safely |
| `bot-registry.json` | Maps cwd / project to bot — useful if you have N projects |
| `binding-<pid>.json` | Per-session bot identity; written by `write-binding.ps1` |

## Wiring back into this stack

After you follow the bridge repo's setup:

1. The bridge's `claude-config/CLAUDE.md` overlaps with this stack's
   `config/global-claude-md.template.md`. Pick one as source of truth and
   merge — the templates here are designed to be the canonical "global"
   CLAUDE.md and reference Feishu sections from the bridge by hyperlink.
2. The `PostCompact` hook from the bridge belongs in your
   `~/.claude/settings.json`. The template here
   (`config/settings-json.template.json`) already references
   `notify-once.ps1`.
3. Set up `~/.lark-cli/sync-secrets.local.json` per the bridge's README so
   the sync script can sanitize before commits.
4. Decide your routing convention:
   - Per-project bots → register each in `~/.lark-cli/config.json`, add an
     entry under `bots` in `bot-registry.json`, and add a `projects[]` entry
     if a specific working directory should auto-resolve to that bot.
   - One catch-all bot → just keep the default.

## Things this stack assumes you'll never do

- Have a hook in `~/.claude/settings.json` that calls out to Feishu without
  rate-limiting. The bridge's `sessionend-loop.md` documents how a naive
  `SessionEnd` hook caused a 286-message bombardment in 2026-05. Use
  `notify-once.ps1` for any external-side-effect hook.
- Have multiple Monitor tasks for the same bot in different sessions. The
  daemon tolerates it (NDJSON is append-only); but you'll get duplicate
  task-notifications. One session per bot.
- Disable the foreground-window guard in `send-keys.ps1`. The `-Force` switch
  exists for testing only.

## Mobile-side setup

On your phone:

1. Install **Feishu (Lark)** app, sign in, find your bot in Contacts.
2. Open a 1-1 chat with the bot (P2P). The `chat_id` for that conversation is
   what your bot-registry needs.
3. Test by sending "hi" — your desktop Claude Code session should see a
   `task-notification` within a couple of seconds.

If it doesn't, follow the bridge repo's `docs/lessons/monitor-pipe.md`
liveness-checking decision tree.

## You're done with the bridge when…

- A message from your phone arrives in Claude Code as a `task-notification`
- A `messages-send` from Claude returns `ok=true` and you see the message on
  your phone
- `/compact!` from phone screenshots → confirm → types → confirm → Enter, all
  via Feishu

Now you have a mobile inbox into the vault.
