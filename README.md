# claude-obsidian-knowledge-stack

A reproducible personal knowledge system built on **Claude Code + Obsidian**, with a
companion bridge to Feishu (Lark) so you can drive it from your phone.

This repo is the blueprint. It is not the data. Drop another AI into this folder
and tell it "set this up for me from scratch on a fresh Windows machine" — by
following the setup guides in order, that AI can recreate the working system
without ever needing access to the original operator's notes or credentials.

Everything here is sanitized: no real bot IDs, no chat IDs, no API keys, no
private note contents. Templates use placeholders like `<APP_ID>`,
`<CHAT_ID>`, `<USER_OPEN_ID>` that you fill in once for your own setup.

## What this stack does

- **Persistent, growing knowledge base** in Obsidian — a Note-as-atom vault where
  every source is one atomic page, cross-referenced via a hand-curated
  `notes-graph.md`. No RAG, no vector store; plain markdown + grep is enough at
  this scale and gives Claude 100% recall.
- **Claude Code as the operator** — reads sources, files notes, maintains the
  index, generates the cross-references, retrieves on demand.
- **Mobile-first inbox via Feishu** — your phone is the capture interface.
  Send a WeChat article link, ask a question, request a note — it lands in the
  desktop Claude Code session within seconds.
- **WeChat article ingestion** via the `wechatDownload` MCP server (bypasses
  the referer wall, fetches full HTML + images).
- **Image generation for diagrams** via `gpt-image-2` through a proxy, with
  hard rules that all in-image text be Chinese for cross-device readability.
- **Long-lived memory** across Claude Code sessions via the `claude-mem`
  plugin (observations / summaries persisted to a local SQLite).

## What this stack does NOT do

- Replace your own thinking. The vault grows because you decide what to ingest.
- Auto-generate notes from arbitrary URLs. You ask explicitly.
- Sync notes through any cloud you don't control. The vault syncs only via
  Obsidian Sync (paid, end-to-end encrypted, your account).

## How the pieces talk to each other

See `ARCHITECTURE.md` for the full picture. The short version:

```
[your phone, Feishu app]
        │  text / image / WeChat link
        ▼
[Feishu bot]  ←──── feishu-claude-code-bridge (separate repo)
        │  WebSocket event subscribe
        ▼
[Claude Code on desktop]
        │       │       │
        │       │       └── claude-mem  ──► local SQLite (cross-session memory)
        │       │
        │       └── wechatDownload MCP  ──► public WeChat articles → .raw/wechat/
        │
        └── Obsidian vault (this repo's vault/ describes the layout)
                │
                └── Obsidian Sync (your paid account) ──► your phone's Obsidian app
```

## Repo layout

```
setup/                  step-by-step install + config (run in order)
  01-prereqs.md          Windows tools, Node, Python, Git
  02-claude-code.md      install Claude Code + first run + plugins
  03-feishu-bot.md       link out to feishu-claude-code-bridge
  04-obsidian.md         install Obsidian + create vault + sync + plugins
  05-wechat-mcp.md       wechatDownload desktop + MCP wire-up
  06-image-generation.md gpt-image-2 via API proxy + helper script
  07-memory-plugins.md   claude-mem install + key knobs

vault/
  structure.md           folder layout you should end up with
  conventions.md         frontmatter, wikilinks, callouts, file naming
  note-generation-rules.md  the ten rules that keep the vault coherent
  skeletons/             starter templates for each kind of page

config/
  global-claude-md.template.md       ~/.claude/CLAUDE.md skeleton (with placeholders)
  vault-claude-md.template.md        vault/CLAUDE.md skeleton (the rules)
  settings-json.template.json        ~/.claude/settings.json hooks fragment
  mcp-config.example.json            ~/.claude.json mcpServers block
  enabled-plugins.md                 which Claude Code plugins to enable + URLs

scripts/
  check-bootstrap.ps1    sanity-check whether each piece is in place

.gitignore               excludes ~/.claude/settings.local.json patterns,
                         vault contents, anything with real IDs
```

## Bootstrap order (90 minutes on a fresh Win 11 machine)

1. `setup/01-prereqs.md` — install Node 20+, Python 3.12+, Git, PowerShell 7
2. `setup/02-claude-code.md` — install Claude Code, sign in, install plugins
3. `setup/04-obsidian.md` — install Obsidian, create the vault, paste the
   vault `CLAUDE.md` from `config/vault-claude-md.template.md`, enable Sync,
   verify cross-device propagation
4. `setup/07-memory-plugins.md` — install `claude-mem` so your second session
   onwards has context from prior work
5. `setup/03-feishu-bot.md` — (optional, if you want mobile capture) follow
   the linked `feishu-claude-code-bridge` repo
6. `setup/05-wechat-mcp.md` — (optional, if you read WeChat) install
   wechatDownload + register the MCP in `~/.claude.json`
7. `setup/06-image-generation.md` — (optional, if you want diagrams) drop in
   the helper script with your own API key
8. Ingest your first source: open a Claude Code session in the vault folder
   and say "ingest this URL: <some article>". The note-generation rules will
   produce a properly-shaped page in `wiki/sources/`.

## Why "Note-as-atom"

The original LLM Wiki pattern (Karpathy) splits sources into entity, concept,
and question sub-pages. After ~3 months of running it that way, we switched to
**Note-as-atom**: one source = one atomic page, no derived sub-pages.
Cross-source relationships are hand-curated in a single `wiki/meta/notes-graph.md`.

The reasoning:

1. Splitting created link rot. Updating one fact meant chasing it across N
   derived pages, and it never stayed consistent.
2. The derived pages were lower-quality than just re-reading the source.
3. Search-by-grep on whole-source pages gives Claude 100% recall when the user
   asks a specific question. RAG / vector recall caps out around 90% and
   doesn't surface enough context anyway.

If you don't agree, you can adopt the original entity/concept split — but the
ten rules in `vault/note-generation-rules.md` assume Note-as-atom.

## Placeholder legend

Templates throughout this repo use several placeholder styles. Pick one per
field and substitute consistently before saving the file in your own setup:

| Placeholder | Means | Example after substitution |
| --- | --- | --- |
| `<USER_HOME>` | Windows-style user home | `C:\Users\you` |
| `<USER_HOME_POSIX>` | MSYS / Git Bash style of the same path | `/c/Users/you` |
| `<APP_ID_*>`, `<CHAT_ID_*>`, `<USER_OPEN_ID>` | Feishu bot identifiers (from your `~/.lark-cli/config.json`) | `cli_xxxxxxxx`, `oc_xxxxxxxx`, `ou_xxxxxxxx` |
| `<your-github-user>` | Your GitHub handle | (your handle) |
| `<your-provider>` | Your OpenAI-compatible API provider host | e.g. `api.openai.com` |
| `<bot1>`, `<bot2>`, ... | Short name you give a bot in `bot-registry.json` | up to you |
| `<vault-name>` | Folder name for your Obsidian vault | `knowledge-vault` |

## License

MIT. The mechanism is for anyone to copy. The notes are yours.
