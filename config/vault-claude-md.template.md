# <vault-name> — Claude + Obsidian Wiki Vault

This folder is both an Obsidian vault and a Claude Code project. Claude
reads this file at every session start in this folder.

**Plugin**: `claude-obsidian` (optional but recommended)  
**Skills**: `/wiki`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint`, `/save`, `/canvas`  
**Vault path**: this directory

## What This Vault Is For

Persistent, compounding knowledge base. Drop sources, ask questions, the
vault grows. See `vault/structure.md` in
[claude-obsidian-knowledge-stack](https://github.com/<github-user>/claude-obsidian-knowledge-stack)
for the architecture decisions.

## Vault Structure

```
.raw/           original artifacts — Claude reads, NEVER modifies, see rule 8
wiki/           Claude-generated knowledge base
  hot.md        current context (~500 words)
  index.md      one-line per note, by domain
  log.md        append-only timeline (newest top)
  overview.md   what this vault is
  sources/      atomic notes, one per source
  meta/         cross-source relationships (notes-graph.md)
  _attachments/ images / PDFs referenced by notes
```

## Architecture: Note-as-atom (since 2026-04-16)

This vault is **Note-as-atom**, not Karpathy's original split LLM Wiki.

- **1 source = 1 atomic note**. Claude does **not** generate entity / concept sub-pages.
- Cross-note relationships, keywords, and groupings are **centralized** in `wiki/meta/notes-graph.md`.
- Only two top-level folders under `wiki/`: `sources/` + `meta/` (**no `concepts/`, no `entities/`**).
- `/save`, `/autoresearch`, `/wiki-ingest` etc. that would create derived pages are **disabled** or modified:
  - `wiki-ingest`: only "read source → update notes-graph", no new content pages
  - `save`: archive conversation to `wiki/sources/sessions/`, single file, no splitting
  - `autoresearch`: only runs with explicit "build research subpages" opt-in

## User Ingest Rules (HARD rules, always obey)

These are the **ten rules** that keep the vault citable. Full version with
*why* and *how* lives in
[`vault/note-generation-rules.md` of claude-obsidian-knowledge-stack](https://github.com/<github-user>/claude-obsidian-knowledge-stack/blob/main/vault/note-generation-rules.md).

### 1. Source bodies are immutable

Once a source's body is written, Claude does not change it. Frontmatter
(tags / related) can grow. Body changes require explicit "整理这份" from user.

### 2. External knowledge OFF by default

In source notes and in `notes-graph`, only use facts that appear in the
source. No LLM-recalled drug names, gene aliases, PMIDs, vendor names,
trial numbers.

### 3. External knowledge MUST be labeled

When user authorizes external content, wrap each addition in
`> [!external]` callout or `（外部补充：xxx）` inline.

### 4. Sources land in `wiki/sources/<domain>/`

Default location. If user creates elsewhere and says "this is a source",
move it (no body changes) here.

### 5. Don't split sources

No entity / concept / question sub-pages. Cross-source relationships only
live in `wiki/meta/notes-graph.md`.

### 6. Every synthesized note opens with `> [!abstract] 摘要`

Position: right after frontmatter, before first section.

```markdown
> [!abstract] 摘要
> 这是 X 的整理，来源 Y，涉及主题 Z。
> - 核心看点 1
> - 核心看点 2
> - 核心看点 3
> 适合 [谁] 在 [场景] 时回头查。
```

100-200 chars. Synthesis notes name which sources merged + why. WeChat
reposts include original author's stance + Claude's added insights.

### 6.2 List / roundup 笔记文件名必须含项目名

合集型来源（GitHub 周报、N 个工具盘点、本周必读 N 篇 等）**不要照搬原文标题**。
文件名格式：

```
<系列名> 本周 <数量> 项目 YYYY-MM-DD <项目名 1> <项目名 2> <项目名 3>[ <项目名 4>].md
```

例：`GitHub 本周 9 项目 2026-05-24 scientific-agent-skills codegraph oh-my-pi 12-factor-agents.md`

挑 3-5 个最有代表性 / 最大 Star / 涨势最猛的项目名拼进去；其余在正文 §
里详解。**写完正文回头改文件名**（先写完才知道哪些项目最值得露出）。

**Why**：scan 文件名时不点开就能判断"我要的 repo 在不在"；扫历史避免"4
篇同名周报分不清"。

**例外**：单项目深度笔记（已经是项目名打头）无需此规则。

### 6.5. Every change → log entry IMMEDIATELY

Triggers: new note, architectural change, vault bugfix, new rule.

```markdown
## [YYYY-MM-DD] <operation> | <Title>
- 触发：<user ask>
- 原文取全：<how acquired>
- 原始物：.raw/<type>/<filename>
- Output：[[Note]] + diagrams/scripts
- 内容：<2-3 sentences>
- 外部洞见：N 处 `[!insight]`
- 跨笔记关联：[[A]] / [[B]]
- YAML 校验：通过
```

Append to `wiki/log.md` TOP (newest first). **Don't batch** — write one
note, log it, then move on.

### 7. WeChat article images must be localized

Copy images from `<download dir>/<account>/图片/` to
`wiki/_attachments/<note-slug>/`, replace `mmbiz.qpic.cn` URLs with
`![[<note-slug>/<name>.jpg]]`. Only images actually referenced in the note,
not all 30.

### 7.5. YAML frontmatter: NEVER same-kind nested quotes

Same-kind nesting silently breaks YAML → Obsidian shows red raw text.

```yaml
# WRONG: source: "..."生物原生数据基础设施"..."
# RIGHT: source: "...'生物原生数据基础设施'..."
# RIGHT: source: "...『生物原生数据基础设施』..."
# RIGHT: source: '..."生物原生数据基础设施"...'
# RIGHT: source: | (block scalar)
```

### 8. Archive raw to `.raw/<type>/` BEFORE writing the note

Hard sequence: `mkdir .raw/<type>/` → save raw → only then write the note.
Note's frontmatter gets `raw_path: [list]` pointing back.

Subdir + naming:

| Type | Subdir | Naming |
| --- | --- | --- |
| WeChat | `.raw/wechat/` | `YYYY-MM-DD_<slug>_<wxid>.{html,md}` |
| PDFs | `.raw/pdf/` | `YYYY-MM-DD_<slug>.pdf` |
| Screenshots | `.raw/screenshots/` | single: `YYYY-MM-DD_<slug>.<ext>`; multi: `YYYY-MM-DD_<slug>/01.jpg 02.jpg` |
| GitHub | `.raw/github/` | `YYYY-MM-DD_<owner>_<repo>_README.md` + `_meta.json` |
| WebFetch | `.raw/webfetch/` | `YYYY-MM-DD_<domain>_<path-slug>.md` |
| Transcripts | `.raw/transcripts/` | `YYYY-MM-DD_<topic>.md` |

WeChat 专用：HTML + extracted MD pair; per-image local copy only what note
references; preserve external links in HTML for full reading.

Exception: video skip (downloader pipeline pending); pre-2026-05-03 sources
need not be retroactively archived.

### 9. Generate diagrams on hard sections (Chinese text inside)

When a section's hard without a diagram, generate one via the configured
image-gen helper (see `setup/06-image-generation.md` of this stack).

**All in-image text must be Simplified Chinese** — titles, axis labels,
callouts, table headers. Proper nouns / model names / commands may stay
English.

0-2 diagrams per note. Save to `_attachments/<note-slug>/<name>.png`.
Embed via wikilink. Log path under `Output:`.

Don't diagram: lists / tables already clear, command refs / API docs,
short notes (<800 chars).

### 10. Hard concepts get an analogy or example

Inline `（打比方：xxx）` for brief; `> [!tip] 类比：xxx` callout for
substantial. 3-5 per note. Don't analogize when concept is obvious or when
analogy is forced.

Forms (most common first):
- Life analogy ("Egress 费就像健身房合约的退会费")
- Familiar-product parallel ("OrioleDB 之于 PG 像 InnoDB 之于 MySQL 早期")
- Quantified concrete ("PB 级 ≈ 5 万部 4K 电影")
- Scenario re-enactment
- Counter-example

## How to Use

Drop a source file into `.raw/` or vault root, then tell Claude:
"ingest [filename]" / "digest 一下".

Ask any question. Claude reads `hot.md` → `index.md` → drills into relevant
sources.

Run `lint the wiki` every 10-15 ingests to catch orphans and YAML gaps.

## Cross-Project Access

To reference this vault from another Claude Code project, add to that
project's `CLAUDE.md`:

```markdown
## Wiki Knowledge Base
Path: <USER_HOME>\Documents\<vault-name>\

When you need context not already in this project:
1. Read wiki/hot.md first (recent context, ~500 words)
2. If not enough, read wiki/index.md
3. If you need cross-source relationships, read wiki/meta/notes-graph.md
4. Only then read individual wiki pages

Do NOT read the wiki for general coding questions or things already in this project.
```

## Plugin Skills (if `claude-obsidian` installed)

| Skill | Trigger |
|-------|---------|
| `/wiki` | Setup, scaffold, route to sub-skills |
| `ingest [source]` | Single or batch source ingestion |
| `query: [question]` | Answer from wiki content |
| `lint the wiki` | Health check |
| `/save` | Archive current conversation as one source page |
| `/autoresearch [topic]` | Autonomous research loop (gated; needs explicit opt-in) |
| `/canvas` | Visual layer — add images / notes to Obsidian canvas |

## MCP (Optional)

For Claude Code to read / write vault notes via MCP rather than file tools,
see `skills/wiki/references/mcp-setup.md` if you installed `claude-obsidian`.
For most users the built-in `Read` / `Edit` / `Write` tools are sufficient.
