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
│   ├── 最新笔记.md                 # (optional) mobile-first "what's new" page — time-descending,
│   │                               # grouped by day, rebuilt (not appended) by refresh-latest.py
│   │                               # after every ingest; linked from index.md as "🆕 最新笔记"
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
│   │   ├── dashboard.base         # optional Obsidian Bases equivalent of dashboard.md
│   │   ├── contradiction-check.md # optional — output of a "do any two notes disagree" pass
│   │   ├── health-report.md       # optional — output of a wiki-lint health check
│   │   ├── lint-report.md         # optional — output of a wiki-lint pass
│   │   └── *.png / *.gif          # cover images, demo gifs
│   │
│   ├── <glossary>/                # OPTIONAL — separate glossary/term-explainer subsystem
│   │   ├── _index.md              # its own term table + its own mini operation log
│   │   └── <Term>.md              # one page per jargon term (see "Glossary subsystem" below)
│   │
│   └── _attachments/              # images + PDFs referenced from notes
│       ├── <note-slug-1>/         # one folder per source note that needs assets
│       │   ├── diagram-1.png
│       │   └── photo.jpg
│       └── <note-slug-2>/
│
└── .raw/                          # original artifacts — hidden from Obsidian, never modified.
    │                                 (ONE canonical location: vault root, sibling of wiki/ — see note below)
    ├── wechat/                    # WeChat article .html + extracted .md pairs
    ├── pdf/                       # PDFs, docx, pptx
    ├── github/                    # README + repo metadata json
    ├── webfetch/                  # WebFetch snapshots of arbitrary pages (legacy web/ merged in here)
    ├── transcripts/               # video/audio transcripts + user dictation (no separate video/)
    ├── rss/                       # RSS/Atom entries — auto-fetched daily by a scheduled task, no LLM
    ├── social/                    # community posts — V2EX / 小红书 / Reddit, post + selected comments
    ├── screenshots/               # user-sent screenshots
    └── articles/                  # legacy path, kept for backward compatibility only
```

> **One canonical `.raw/` location.** `.raw/` lives exactly once, at the
> vault root. Don't let a second copy accumulate at `wiki/.raw/` — it's an
> easy accident if a fetch/download tool is invoked with its working
> directory inside `wiki/` instead of the vault root, and once both exist
> nothing guarantees which one a given script or Claude session reads from
> next. If you ever find both, the root-level `.raw/` is canonical: migrate
> anything under `wiki/.raw/` up a level and delete the nested folder.

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
| "What's newest, phone-first" | `wiki/最新笔记.md` (optional, time-descending, rebuilt not appended) |
| A jargon/term explainer page | `wiki/<glossary>/<Term>.md` (optional subsystem, see below — NOT `sources/`) |
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
- **Domains under `sources/`**: this is a **soft guideline, not a cap**.
  Starting with 2-3 top-level domains is sweet — but don't fight it once
  your reading spreads into new topics. Real long-running vaults commonly
  grow to somewhere around 6-9 top-level domains over months of use; there
  is no penalty for adding one when a new topic area stops fitting anywhere
  existing. Illustrative examples of what mature vaults' domain lists tend
  to look like (name yours after what you actually read about, not these):
  *AI/tech*, *drugs & biology*, *workflow & tooling*, *startups & business*,
  *investing & quant*, *agriculture & livestock*, *semiconductors & hardware
  supply chain*, *design & product*. If you want finer division inside one
  domain, split with a numbered subfolder (e.g. `AI技术/01-Coding Agent
  CLI/`, `AI技术/02-Agent 控制循环/`). Don't go three levels deep.

## Optional: a separate glossary subsystem

Some vaults add a small **glossary / term-explainer** folder — short,
example-heavy pages answering "what is X" for recurring jargon (e.g. a page
explaining a file format, a protocol, a language). This is the **one
deliberate exception** to Note-as-atom / "don't split sources" (rule 5):
each term gets its own small entity page, written to be genuinely easy to
understand — lean on examples and analogies rather than density.

Key properties, all by design:

- Lives at `wiki/<glossary>/` — a **peer** of `sources/` and `meta/`, not
  nested inside either.
- Has its **own `_index.md`** (a term table: term → one-line definition →
  last-updated date), separate from `wiki/index.md`.
- **Deliberately excluded** from `wiki/index.md`, `wiki/meta/notes-graph.md`,
  and `wiki/log.md`. It's a self-contained subsystem with its own rules and
  its own mini operation log kept inside its `_index.md` — mixing it into
  the main index/graph/log would blur "atomic source note" with "concept
  explainer," which is exactly the split-mode failure rule 5 exists to avoid.
- Optional. Most vaults don't need one until jargon explainer requests start
  recurring — add it then, not preemptively.

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
- `wiki/最新笔记.md` (optional) — mobile-first "what's new" page: every note
  as a one-line card, grouped by date, newest date group first. This is a
  **regenerate-the-whole-page** artifact (like `index.md`), not an
  append-only log (like `log.md`) — a script rebuilds it from `sources/**`
  frontmatter after every ingest pass (note-generation-rules.md rule 12).
  Linked from the top of `index.md` as "🆕 最新笔记" so a phone session has
  one tap to "show me what's newest" instead of browsing domain folders.

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
