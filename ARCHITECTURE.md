# Architecture

How the five components fit. Read after `README.md`, before any `setup/` page.

## The five components

| Component | Role | Where it lives | Persistent? |
| --- | --- | --- | --- |
| Claude Code | Operator that reads, writes, retrieves | `~/.claude/` | Yes (settings + plugins) |
| Obsidian vault | The knowledge base itself | `~/Documents/<vault-name>/wiki/` | Yes (files on disk) |
| Obsidian Sync | Cross-device file replication | Obsidian's paid service | Yes (encrypted cloud + local cache) |
| Feishu (Lark) bot | Mobile capture surface | A long-running `lark-cli` daemon on desktop | Yes (daemon + WebSocket) |
| MCP servers | Domain plugins (WeChat, image gen, etc.) | Process or HTTP endpoints | Spawned on demand by Claude Code |

## Where each component reads / writes

```
                              Claude Code
                                  │
                ┌────────────┬────┴───────┬────────────┐
                │            │            │            │
            reads/writes  reads/writes  reads/writes  spawns/talks-to
                │            │            │            │
                ▼            ▼            ▼            ▼
        ~/.claude/      Obsidian       Feishu       MCP servers
        - settings.json  vault         events        (wechatDownload,
        - CLAUDE.md     - wiki/                       playwright,
        - plugins/      - .raw/                       context7, etc.)
        - hooks                        ▲
        - skills                       │
                                       │ WebSocket
                                       │
                              Feishu bridge daemon
                              (lark-cli event +subscribe,
                              detached process under %TEMP%)
                                       ▲
                                       │
                                phone Feishu app
```

## Data flow patterns

### Pattern 1 — manual ingest

```
operator opens Claude Code in vault folder
    └→ "ingest <url-or-file>"
         └→ Claude (per note-generation-rules.md):
            1. mkdir -p .raw/<type>/
            2. fetch raw (curl / WebFetch / wechatDownload MCP)
            3. write .raw/<type>/<YYYY-MM-DD_slug>.<ext>
            4. read raw, extract structure
            5. write wiki/sources/<domain>/<title>.md
               - frontmatter: type, title, source, raw_path, tags, related
               - § Abstract callout
               - sections + 1-2 generated diagrams (optional)
               - 3-5 analogies on hard concepts
            6. append entry to wiki/log.md (date, op, output, related)
            7. update wiki/meta/notes-graph.md cross-refs
```

### Pattern 2 — Feishu-driven ingest

```
phone sends WeChat link via Feishu chat to bot
    └→ feishu-bridge daemon writes JSON event line to %TEMP%\lark-<bot>-events.ndjson
         └→ per-session monitor tail reads, awk filters chat_id messages
              └→ Claude Code sees `task-notification`
                   └→ runs Pattern 1 with link as input
                        └→ replies in Feishu with note title + WikiLink
```

### Pattern 3 — query

```
operator asks "what do I know about X?" (desktop or via Feishu)
    └→ Claude reads vault hot.md and meta/notes-graph.md
         └→ greps wiki/sources/ for X (no vectors, just ripgrep)
              └→ reads top hits, synthesizes
                   └→ optionally proposes filing a new synthesis note
```

### Pattern 4 — image generation for a note

```
Claude finishes writing a complex section
    └→ self-asks "is anything here hard without a diagram?"
         └→ if yes: calls genimg.py with Chinese-text prompt
              └→ gpt-image-2 via proxy → returns PNG
                   └→ saves to _attachments/<note-slug>/<name>.png
                        └→ embeds as Obsidian wikilink ![[<note-slug>/<name>.png]]
                             └→ appends path to log entry's Output field
```

## Lifetimes

| Thing | Lifetime | Outlives `/compact`? | Outlives session restart? |
| --- | --- | --- | --- |
| Vault files | Forever (Obsidian Sync versioned) | Yes | Yes |
| `.raw/` archives | Forever | Yes | Yes |
| Claude Code conversation | Single session | No (gets compacted) | No |
| `claude-mem` SQLite | Forever | Yes | Yes |
| `~/.claude/CLAUDE.md` rules | Forever (you edit) | Yes | Yes |
| Feishu bridge daemon | Until you kill it | Yes | Yes |
| Per-session bot binding file | Single claude.exe PID | Yes (PID stable) | No |

The vault and `claude-mem` are the two long-memory layers. The vault holds
explicit, hand-curated knowledge; `claude-mem` holds implicit, per-tool-use
observations that future sessions can grep when you ask "did we already solve
this?".

## Trust boundaries (be paranoid here)

- **`.raw/` is source-truth.** Anything Claude writes to `wiki/sources/` is
  derived. If you doubt a note, open the matching raw file under `.raw/`.
- **Bot secrets** live only in `~/.lark-cli/` and the OS keychain. The Feishu
  bridge repo's sync script reads a local-only file
  `~/.lark-cli/sync-secrets.local.json` to redact secrets before committing.
- **Image-gen API key** lives in a single local file, never in the helper
  script. The script reads `~/Desktop/openai_api.txt` line 1.
- **`claude-mem` observations** are local SQLite. The summarization step calls
  out to a third-party LLM (DeepSeek or similar). Be aware that summaries of
  your conversations leave your machine to that provider. If that's
  unacceptable, run `claude-mem` with `CLAUDE_MEM_PROVIDER=offline` or
  uninstall.

## Failure modes you will hit (and where they're documented)

| Symptom | Where to read |
| --- | --- |
| Note written but doesn't show on phone | `setup/04-obsidian.md` — "Obsidian Desktop must be running for Sync" |
| Claude pops a console window per subagent | `setup/02-claude-code.md` — `claude-agent-sdk` Windows fix |
| Feishu bot online but messages don't reach Claude | linked: `feishu-claude-code-bridge` repo `docs/lessons/monitor-pipe.md` |
| WeChat article comes back blank or images missing | `setup/05-wechat-mcp.md` — referer wall, output-dir verification |
| Generated images contain English when prompt asked for Chinese | `setup/06-image-generation.md` — prompt template + retry rule |
| Cross-session memory empty after upgrade | `setup/07-memory-plugins.md` — `claude-mem` autopatch |

## Why this stack instead of (alternatives)

- **vs. Notion** — Notion is great as a UI but won't let an LLM read your
  whole base efficiently and doesn't run plugins inside your own machine.
- **vs. Logseq + plain Claude** — fine alternative; rules in `vault/` mostly
  port over. The Feishu bridge is independent of vault choice.
- **vs. RAG over markdown** — at ~150 source notes, grep is faster and recalls
  100%. RAG starts paying off above ~10K documents or when sources are noisy.
  Revisit when you cross that line.
- **vs. ChatGPT memory** — that memory is opaque, capped, and theirs. This
  vault is yours, inspectable, branchable, gittable.
