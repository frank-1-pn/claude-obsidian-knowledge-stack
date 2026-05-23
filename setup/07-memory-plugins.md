# 07 — Cross-session memory (claude-mem)

The vault holds explicit knowledge you decided to file. `claude-mem` holds
implicit knowledge — observations from every Claude session, summarized and
queryable, so the next session can grep "did we already solve this?" and
"what did we decide about X last week?".

This is optional but recommended once you start running Claude Code regularly.

## What you'll install

- `claude-mem` plugin (a Claude Code marketplace plugin)
- A local SQLite at `~/.claude-mem/claude-mem.db`
- A background worker daemon (Bun-based, runs on `127.0.0.1:<port>`)
- A summarization backend (OpenRouter-compatible; we use a cheap-fast OpenAI-compatible provider to keep
  costs low and data residency local-ish)

## Install

In Claude Code, open `/plugins` and install `claude-mem` by `thedotmack`.
Restart the session. The plugin will set up `~/.claude/plugins/cache/.../`
and bring its hooks into your `settings.json` automatically.

First boot:

```powershell
npx -y claude-mem start
# or, if you have a helper script:
powershell -ExecutionPolicy Bypass -File ~/.claude/scripts/claude-mem-start.ps1
```

This starts the worker. It self-registers a SessionStart hook so future
sessions pick it up.

## Configure for sane cost + speed

`~/.claude-mem/settings.json`:

```json
{
  "CLAUDE_MEM_MODE": "code--zh",
  "CLAUDE_MEM_PROVIDER": "openrouter",
  "CLAUDE_MEM_OPENROUTER_MODEL": "&lt;cheap-fast-non-reasoning-model&gt;",
  "CLAUDE_MEM_OPENROUTER_API_KEY": "<your-provider-or-openrouter-key>",
  "CLAUDE_MEM_OPENROUTER_BASE_URL": "https://api.<your-provider>",
  "CLAUDE_MEM_OPENROUTER_MAX_TOKENS": 8000,
  "CLAUDE_MEM_OPENROUTER_MAX_CONTEXT_MESSAGES": 6,
  "CLAUDE_MEM_SKIP_TOOLS": "ListMcpResourcesTool,SlashCommand,Skill,TodoWrite,AskUserQuestion,Read,Glob,Grep,WebFetch,WebSearch,NotebookEdit",
  "CLAUDE_MEM_MAX_CONCURRENT_AGENTS": 1,
  "CLAUDE_MEM_WORKER_PORT": 37783
}
```

Why each non-default knob:

| Knob | Why |
| --- | --- |
| `CLAUDE_MEM_MODE=code--zh` | Generates observations and summaries in Chinese — useful if you read the dashboard yourself; switches to English with `code` |
| `CLAUDE_MEM_OPENROUTER_MODEL=&lt;cheap-fast-non-reasoning-model&gt;` | Cheap, fast enough for summarization. Do **not** use `-pro` (reasoning model) — it burns tokens on reasoning and returns empty content |
| `CLAUDE_MEM_OPENROUTER_MAX_TOKENS=8000` (default 100K) | Cap context window per summarization; saves cost and matches a cheap-fast OpenAI-compatible provider's effective context |
| `CLAUDE_MEM_OPENROUTER_MAX_CONTEXT_MESSAGES=6` (default 20) | Same — fewer messages per summary; quality is fine |
| `CLAUDE_MEM_SKIP_TOOLS=...` | Don't summarize observations from `Read`, `Grep`, `Glob`, `TodoWrite`, etc. — noisy and uninformative |
| `CLAUDE_MEM_MAX_CONCURRENT_AGENTS=1` | Avoid concurrent SQLite writes; keep it simple |
| `CLAUDE_MEM_WORKER_PORT` | Pick a free port. Windows ghost-socket trouble (next section) sometimes forces you to bump this |

## a cheap-fast OpenAI-compatible provider vs OpenRouter

Both work because they're OpenAI-compatible. Direct a cheap-fast OpenAI-compatible provider (`api.<your-provider>`)
is what we use because the user's region can't reliably hit Anthropic
directly from the SDK. If you can hit Anthropic, you can use Claude Haiku
through Anthropic's official endpoint — probably better summaries.

## The plugin URL upgrade-eats-patches problem

If you go behind a non-OpenRouter aggregator that requires URL rewriting
(e.g., to send `openrouter.ai/api/v1/chat/completions` traffic to
`api.<your-provider>/v1/chat/completions`), you'll patch the plugin's
`worker-service.cjs`. **Plugin auto-updates from the Claude Code marketplace
will overwrite your patch.**

We solved this with an idempotent autopatch script at
`~/.claude/scripts/claude-mem-autopatch.ps1` that:

1. Scans every cached copy of `worker-service.cjs` (under
   `~/.claude/plugins/cache/...` AND `~/AppData/Local/npm-cache/_npx/...`)
2. Checks for a needle (e.g., the old URL or a specific code pattern)
3. Replaces only if found; logs to `~/.claude-mem/logs/autopatch.log`

Wire it into a `SessionStart` hook so it runs on every fresh session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -ExecutionPolicy Bypass -File '/c/Users/you/.claude/scripts/claude-mem-autopatch.ps1' >/dev/null 2>&1 || true",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

The template at `config/settings-json.template.json` includes this wiring.

## Windows ghost socket

When the worker dies, Windows' TCP table sometimes holds the listener port in
a "TIME_WAIT" / orphaned state — restart fails with port-in-use. Workarounds
(in order of cost):

1. Pick a different port in `~/.claude-mem/settings.json`. Increment by 1
   until you find a free one. Common port-walk path:
   37777 → 37778 → … → 37783.
2. Reboot — frees all ghost sockets.
3. Hunt the owning PID with `Get-NetTCPConnection -LocalPort <port>` and kill
   it if it's actually still alive somewhere.

This is a Windows quirk, not a `claude-mem` bug.

## Verify it works

After a few minutes of normal usage:

- `~/.claude-mem/logs/claude-mem-<YYYY-MM-DD>.log` should show
  `ENQUEUED messageId=...` lines for events you triggered.
- The worker dashboard at `http://localhost:<port>` should be reachable.
- The next Claude Code session, when you ask "did we work on X last time?",
  should be able to surface relevant observations.

If you see `OpenRouter auth error (status 401)` and no new observations for
hours: a plugin upgrade ate your URL patch. Run the autopatch script
manually, restart the worker.

## Pruning and backups

`~/.claude-mem/` includes a `backups/` folder. Move it elsewhere if disk is
tight. SQLite WAL files (`*-wal`, `*-shm`) live alongside the DB; don't
delete them while the worker is running.

## Privacy

Conversation observations are stored locally in SQLite. The summarization
hop calls out to whatever provider you configured. If that bothers you, set
`CLAUDE_MEM_PROVIDER=offline` (no summaries, observations still queryable
locally) or uninstall the plugin entirely.

## You're done with this stack when…

- A fresh Claude Code session in your vault folder reads `wiki/hot.md`,
  greets you in Chinese / English (whichever your CLAUDE.md is in),
  recognizes `claude-mem` is alive, and is ready to ingest.
- Sending a message from your phone via Feishu (after `03-feishu-bot.md` is
  done) shows up in the session within a few seconds.
- Saying "ingest this WeChat URL" produces a properly-formed source note,
  archives the raw, localizes the referenced images, and logs the operation.
- Asking Claude to "draw a diagram for that section" generates a Chinese-text
  image and embeds it.
- Switching to your phone shows the new note within a few seconds of writing
  (Obsidian Sync icon green).

That's the loop. Build a couple of notes in this rhythm, then start adding
your own conventions on top.
