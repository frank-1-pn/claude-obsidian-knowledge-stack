# 07 — Cross-session memory (claude-mem + file-based auto-memory)

The vault holds explicit knowledge you decided to file. This stack layers two
more memory systems on top of that, and they're complementary rather than
redundant:

- **`claude-mem`** — implicit knowledge: observations from every Claude
  session, summarized and stored in a local SQLite, queried on demand so the
  next session can grep "did we already solve this?" and "what did we decide
  about X last week?".
- **File-based auto-memory (`MEMORY.md` index)** — a lighter-weight,
  plaintext-markdown system with no plugin, no daemon, and no database. A
  slim index file is loaded verbatim into every session's context
  automatically; it links out to small per-fact files you (or Claude) write
  by hand or on request. See "File-based auto-memory" below.

Both are optional but recommended once you start running Claude Code
regularly. You can run either alone or both together — they don't conflict.

## Part 1 — claude-mem

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
```

This starts the worker. It self-registers a SessionStart hook so future
sessions pick it up.

For idempotent / scheduled-task autostart, this repo ships
`config/claude-mem-start.ps1` (and a sibling `config/claude-mem-autopatch.ps1`
for patch re-application). Drop both into `~/.claude/scripts/` if you want
the worker up at logon without manual intervention.

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

This repo ships `config/claude-mem-autopatch.ps1` — an idempotent script that:

1. Scans every cached copy of `worker-service.cjs` (under
   `~/.claude/plugins/cache/...` AND `~/AppData/Local/npm-cache/_npx/...`)
2. Checks for a needle (the old URL or a specific code pattern)
3. Replaces only if found, backs up the pre-patch file, logs to
   `~/.claude-mem/logs/autopatch.log`

Drop it at `~/.claude/scripts/claude-mem-autopatch.ps1`. **It is not wired
into the `SessionStart` hook chain** in `config/settings-json.template.json`
— that chain only runs `claude-agent-sdk-autopatch.ps1` (the Windows
console-flash fix from `setup/02-claude-code.md`). Run
`claude-mem-autopatch.ps1` manually after a `claude-mem` plugin update, or
schedule it (e.g. a Windows Scheduled Task alongside `claude-mem-start.ps1`,
or your own SessionStart entry if you'd rather have it re-checked every
session).

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

## Part 2 — File-based auto-memory (MEMORY.md index)

No plugin, no daemon, no SQLite — just plain markdown files that Claude Code
reads and writes directly. This is the mechanism behind `~/.claude/CLAUDE.md`
itself: a small, always-loaded index, plus a folder of one-fact-per-file notes
it points to.

### Where it lives

```
~/.claude/projects/<project-slug>/memory/
  MEMORY.md              the slim index — auto-injected verbatim into every
                          session's context for that project
  project_<name>.md       one atomic fact about a specific project
  feedback_<name>.md      one atomic fact from user feedback / a correction
  reference_<name>.md     one atomic fact that's a durable reference/lookup
```

`<project-slug>` is derived from the project's working-directory path (the
same slugging Claude Code uses elsewhere under `~/.claude/projects/`). The
folder is a git repo (`git init` it yourself) so the fact history survives a
machine loss and you can diff/revert bad entries.

### How it differs from claude-mem

| | `claude-mem` | File-based auto-memory |
| --- | --- | --- |
| Storage | SQLite (`~/.claude-mem/claude-mem.db`) | Plain `.md` files |
| Granularity | Per-tool-use observations, summarized | One atomic fact per file |
| Retrieval | Queried on demand (search / MCP tools) | `MEMORY.md` index loaded verbatim into every session — no query step |
| Moving parts | Plugin + worker daemon + summarization LLM call | None — just files Claude reads/writes |
| Best for | "Did we already solve this?" across large histories | A handful of durable, high-signal facts you want Claude to *always* know, no lookup required |

They're complementary: `MEMORY.md` keeps a short list of things worth
surfacing unconditionally every session (with a link to the fact file for
detail); `claude-mem` is the wider, searchable net for everything else.

### Setting it up

1. Create the folder: `~/.claude/projects/<project-slug>/memory/`.
2. Create `MEMORY.md` with a `# Memory Index` heading and one bullet per fact
   file, each linking to it by relative path, e.g.
   `- [short label](reference_some_fact.md) — one-line summary`.
3. Write one fact per file, named `project_*` / `feedback_*` / `reference_*`
   depending on what kind of fact it is. Keep each file small — this is meant
   to be atomic, like the vault's own Note-as-atom convention.
4. Keep `MEMORY.md` itself short. It is injected into every session's
   context in full, so bloat here has a real, permanent token cost — push
   detail into the linked fact files instead.
5. `git init` the `memory/` folder and commit as you add facts, same as any
   other durable store in this stack.

There's no autopatch or worker to babysit here — the only failure mode is
letting `MEMORY.md` grow past "slim index" into a second vault. If that
happens, prune aggressively; the fact files are still there to link back to
if you regret trimming a line.

## You're done with this stack when…

- A fresh Claude Code session in your vault folder reads `wiki/hot.md`,
  greets you in Chinese / English (whichever your CLAUDE.md is in),
  recognizes `claude-mem` is alive (and, if you set it up, greets you with
  whatever's in `MEMORY.md`), and is ready to ingest.
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

Optional remaining setup steps (each independent): `03-feishu-bot.md` (mobile
capture), `05-wechat-mcp.md` (WeChat article ingestion), `06-image-generation.md`
(diagrams).
