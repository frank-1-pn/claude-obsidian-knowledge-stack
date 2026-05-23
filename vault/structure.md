# Vault structure

Exact folder layout the rest of the stack assumes. Diverge at your peril; the
note-generation rules in `note-generation-rules.md` reference these paths.

```
<your-vault-name>/
├── CLAUDE.md                      # vault-scoped Claude Code rules (paste from config/vault-claude-md.template.md)
│
├── wiki/                          # all knowledge lives here
│   ├── hot.md                     # ~500-word "what we're currently working on" cache
│   ├── overview.md                # what this vault is, who maintains it
│   ├── index.md                   # one-line entry per note, grouped by domain
│   ├── log.md                     # append-only timeline (newest at top)
│   │
│   ├── sources/                   # one .md per atomic source
│   │   ├── _index.md              # human-curated overview of sources, by subfolder
│   │   ├── <domain-1>/            # e.g. "AI技术", "药物与生物", "工作流与工具"
│   │   │   ├── <Subdomain 01>/    # optional inner split when a domain has >15 notes
│   │   │   │   └── <Note Title>.md
│   │   │   └── <Note Title>.md
│   │   └── <domain-2>/
│   │
│   ├── meta/                      # cross-source curation
│   │   ├── notes-graph.md         # the only place cross-source relationships live
│   │   ├── dashboard.md           # optional Obsidian Dataview dashboard
│   │   └── *.png / *.gif          # cover images, demo gifs
│   │
│   └── _attachments/              # images + PDFs referenced from notes
│       ├── <note-slug-1>/         # one folder per source note that needs assets
│       │   ├── diagram-1.png
│       │   └── photo.jpg
│       └── <note-slug-2>/
│
└── .raw/                          # original artifacts — hidden from Obsidian, never modified
    ├── wechat/                    # WeChat article .html + extracted .md pairs
    ├── pdf/                       # PDFs, docx, pptx
    ├── github/                    # README + repo metadata json
    ├── webfetch/                  # WebFetch snapshots of arbitrary pages
    ├── transcripts/               # user dictation, video transcripts
    └── screenshots/               # user-sent screenshots
```

## What goes where (recap)

| If the file is… | It belongs in… |
| --- | --- |
| Operator-curated knowledge | `wiki/sources/<domain>/<title>.md` |
| Cross-source relationships | `wiki/meta/notes-graph.md` (NEVER scattered) |
| Image referenced by a note | `wiki/_attachments/<note-slug>/<descriptive-name>.<ext>` |
| Original artifact (raw input) | `.raw/<type>/<YYYY-MM-DD>_<slug>.<ext>` |
| What we're working on now | `wiki/hot.md` (~500 words, rewritten as context shifts) |
| Timeline of every change | `wiki/log.md` (append-only, newest at top) |
| "Quick glance at what's in here" | `wiki/index.md` (one line per note) |
| Vault-scoped Claude rules | `<vault>/CLAUDE.md` |
| Global Claude rules | `~/.claude/CLAUDE.md` (NOT here) |

## What does NOT go in the vault

- Bot secrets, API keys, OAuth tokens — those live in `~/.lark-cli/`,
  `~/.claude/.credentials.json`, OS keychain
- Per-session runtime state (PIDs, lockfiles, NDJSON event streams) —
  those live in `%TEMP%`
- Plugin scratch space — that's `~/.claude/plugins/cache/`
- Anything you can't legally redistribute — keep it out, or at least keep it
  out of any synced location

## Naming conventions

- **File names**: descriptive, human-readable, in whatever script you write
  in (Chinese is fine — Obsidian and Claude handle it). Avoid `?`, `:`,
  `\`, `/`, `<`, `>`, `*`, `|`, `"`, `#` in filenames (Obsidian /
  Windows filesystem hates these).
- **Slug for `_attachments/` and `.raw/`**: lowercase, hyphenated, ASCII.
  Strip punctuation, ~10 words max. For WeChat articles, append the last 5-8
  chars of the WeChat URL `/s/<id>` for traceability.
- **Domains under `sources/`**: 1-3 top-level domains is sweet. If you want
  finer division, split inside a domain (e.g. `AI技术/01-Coding Agent CLI/`,
  `AI技术/02-Agent 控制循环/`). Don't go three levels deep.

## How the index files relate

- `wiki/overview.md` — "what is this vault" — written ONCE, lightly maintained.
- `wiki/index.md` — every note, one line, grouped by domain. Updated when a
  note is added or moved. Doubles as the at-a-glance entry point for new
  sessions.
- `wiki/sources/_index.md` — same as `index.md` but lives next to sources for
  convenience when navigating subfolders.
- `wiki/meta/notes-graph.md` — cross-source relationships. NOT a list of all
  notes (that's `index.md`); this is "which notes talk about CRISPR? which
  notes form the Karpathy-LLM-Wiki critique cluster?". Hand-curated, no
  auto-generation.
- `wiki/hot.md` — what you're working on **right now**. Rewritten every time
  the context shifts (this week's project, this month's questions).
  Limited to ~500 words so it fits in initial reads.

## How a new session navigates the vault

In a typical query, Claude reads in this order:

1. `wiki/hot.md` — current context (always)
2. `wiki/index.md` — what notes exist
3. If the question is about cross-source relationships:
   `wiki/meta/notes-graph.md`
4. If the question is about a specific note: grep
   `wiki/sources/<domain>/` for keywords, read top hits
5. If the question is "how did X evolve?": grep `wiki/log.md` for the term
   and follow timestamps

This works because the vault is small (hundreds of notes, not millions) and
plain grep gives 100% recall.
