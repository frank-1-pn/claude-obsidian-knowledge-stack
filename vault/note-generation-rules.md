# Ten note-generation rules

These rules belong in `<vault>/CLAUDE.md` so Claude reads them at every
session start in the vault folder. The template at
`config/vault-claude-md.template.md` includes all ten as enforceable rules.

Each rule has a **what**, a **why** (the failure mode it prevents), and a
**how**.

---

## 1. Source bodies are immutable

**What.** Once a source note's body is written, Claude does not change it.
Frontmatter (tags / related / raw_path) can be added or refined; the body
itself is fixed. The user explicitly opts in to a re-organize with the words
"整理这份" or equivalent.

**Why.** A vault is only useful for citation if you can trust that the note
you cited last week still says what you cited. Silent rewrites destroy that.

**How.** If you find a body that needs editing, propose the diff in chat
first; only Edit after the user agrees. Default-deny.

---

## 2. External knowledge off by default

**What.** When summarizing a source, only use facts that appear in the source.
Drug names, gene aliases, PMIDs, vendor names, trial numbers, dates — if
they're not in the source, don't add them.

**Why.** Vaults are reference. Mixing operator-curated source content with
LLM-recalled "common knowledge" silently makes the vault uncitable —
readers can no longer trust any given fact came from the source.

**How.** Default-deny external facts in source notes' bodies and in
`notes-graph.md`. Only when the operator says "补一下背景" or "add some
context" do you add external facts — and then under rule 3.

---

## 3. External knowledge must be labeled

**What.** When the operator does authorize external knowledge, every external
addition is wrapped in `> [!external]` or annotated with `（外部补充：xxx）`
inline.

**Why.** Future-you needs to know what came from the source vs what came from
Claude's training data. Labeling makes review trivial; unlabeled mixing makes
audit impossible.

**How.** Use the callout form for paragraph-length additions; inline
parenthetical for single facts. Never invisible additions.

---

## 4. Sources land in `wiki/sources/`

**What.** The default location for any operator-written source is
`wiki/sources/<domain>/<title>.md`. If the operator writes elsewhere and
says "this is a source", move it (no body changes) to the right place.

**Why.** Predictable retrieval depends on predictable location.

**How.** When the operator drops a `.md` in `~/` or vault root and says
"this is a source": `git mv` (if tracked) or `Move-Item` into
`wiki/sources/<domain>/`. Do not rename. Do not edit the body.

---

## 5. Don't split sources

**What.** A source is one atomic note. Don't create entity / concept /
question / TLDR sub-pages derived from it. Cross-source relationships go in
ONE place: `wiki/meta/notes-graph.md`.

**Why.** We tried split-mode (Karpathy LLM Wiki original). After three
months: derived pages went out of sync with the source, link rot accumulated,
and the derived pages were lower quality than re-reading the source. The
hand-curated `notes-graph.md` won.

**How.** When you feel the urge to create `wiki/concepts/X.md` or
`wiki/entities/Y.md` — don't. Add an entry to `notes-graph.md` instead.

---

## 6. Every synthesized note opens with an abstract

**What.** Every note Claude generates (organize / synthesize / archive a
conversation) opens with a `> [!abstract] 摘要` callout. Format:

```markdown
> [!abstract] 摘要
> 这是 X 的整理 / 来源 Y / 涉及主题 Z。（1 句）
> - 核心看点 1
> - 核心看点 2
> - 核心看点 3
> 适合 [谁] 在 [场景] 时回头查。（可选）
```

100-200 characters in the body.

**Why.** When you search the vault on your phone (or grep it from another
project), the abstract is what lets you decide "is this the note I want?"
without opening it.

**How.** Position: right after frontmatter, before the first content section.
Special cases:

- Synthesis note → state what's being merged and why
- WeChat repost → "原作者立场 + Claude 加了什么洞见"
- Series continuation → "和上一期相比新增了什么"

---

## 6.2. List / roundup notes must include project names in the filename

**What.** Notes whose source is a "list of N projects / tools / repos /
articles" — typically GitHub weekly roundups, "top N this week", "must-read
N", curated collections — **do not inherit the original article's clickbait
title**. The filename has a fixed shape:

```
<series-or-type> 本周 <count> 项目 YYYY-MM-DD <project-1> <project-2> <project-3>[ <project-4>].md
```

Examples (vault-existing good naming):

```
GitHub 本周 9 项目 2026-05-24 scientific-agent-skills codegraph oh-my-pi 12-factor-agents.md
GitHub 本周 YYDS 8 项目 2026-05-17 financial-services Ruflo 51K agentmemory UI-TARS easy-vibe.md
GitHub 本周开源新秀 10 项目 2026-05-12 ds4 Mirage TokenSpeed.md
GitHub 本周最火 7 项目 2026-05-10 9router jcode agentmemory.md
```

Pick 3-5 of the most representative / highest-Star / fastest-rising projects
from the N for the filename; the rest live in the body sections.

**Why.** Three failure modes the original-title approach causes:

1. **Search non-discoverability**: scanning Obsidian or your phone, you
   can't tell whether the repo you want is in the article without opening
   the note.
2. **History review**: a year later, scanning filenames in
   `06-GitHub.../` should tell you what each week contained — clickbait
   titles all blur together.
3. **Series collision**: 4 GitHub weekly posts in May with identical
   "本周 X 火火" titles are indistinguishable.

**How to apply.** Write the body first, then rename: lift the 3-5 most
representative project names from the section headers into the filename.
The frontmatter `title` field may stay longer (and include a positioning
clause); the filename strictly follows the template.

**Exception.** Single-project deep-dive notes (e.g.
`Maigret 输入用户名查遍 3000 站点 OSINT 工具 24K Star.md`) already lead
with the project name and don't need the multi-project pattern.

## 6.5. Every change to the vault gets a log entry

**What.** Any of these triggers a log append:

- New source / synthesis written to `wiki/sources/`
- Architectural change to `wiki/meta/`
- Vault-level bugfix (YAML break, broken link)
- New script / rule / infrastructure for the vault

The log lives at `wiki/log.md`, newest at top. Entry shape:

```markdown
## [YYYY-MM-DD] <operation> | <Title>
- 触发：<original ask>
- 原文取全：<how the source was acquired>
- 原始物：.raw/<type>/<filename>   ← when applicable
- Output：[[Note Name]] + any diagrams / scripts changed
- 内容：<2-3 sentences of key facts>
- 外部洞见：N 处 `[!insight]`（要点列表）
- 跨笔记关联：[[A]] / [[B]] ...
- YAML 校验：通过
```

Operation vocabulary: `organize`, `organize+insight`, `synthesis`, `ingest`,
`bugfix`, `architecture-switch`, `cleanup`, `rule-migration`,
`infrastructure`, `init`.

**Why.** `log.md` is the vault's timeline. Without it, "what did we do on
that Tuesday" becomes unanswerable.

**How.** **Don't batch.** Each completed write triggers its own log append
**before** moving to the next task. If you write three notes and only log
the third, the first two are invisible to history.

---

## 7. WeChat article images must be localized

**What.** When ingesting via `wechatDownload`, copy referenced images from
`<download dir>/<account>/图片/` to `<vault>/wiki/_attachments/<note-slug>/`,
and rewrite the `mmbiz.qpic.cn` URLs in the body to Obsidian wikilinks
`![[<note-slug>/<name.jpg>]]`.

**Why.** WeChat has a referer wall — `mmbiz.qpic.cn` links don't render in
Obsidian (it doesn't send the right Referer header).

**How.** Per-image, only ones actually used in the synthesized note. A
WeChat article with 30 images doesn't need all 30 localized; just the ones
you embedded.

---

## 7.5. YAML frontmatter: never same-kind quote nesting

**What.** In any frontmatter string field that contains punctuation
(`source:`, `title:`, `description:`), outer and inner quotes must be
different kinds.

**Why.** YAML doesn't escape inner same-kind quotes — they terminate the
string. Obsidian then shows the whole frontmatter as red raw text and tags /
properties stop working. Silent breakage.

**How.** See `conventions.md` "YAML quote-nesting trap" for the four valid
shapes. Default to `outer "" + inner ''` (or block scalar `|`) when in
doubt.

---

## 8. Archive raw before integrating

**What.** Every external artifact (URL, PDF, screenshot, GitHub repo, video
transcript) is first saved to `.raw/<type>/<YYYY-MM-DD>_<slug>.<ext>`
**before** any source note is written. The source note's frontmatter
`raw_path:` field then points back.

| Type | Subdirectory | Naming |
| --- | --- | --- |
| WeChat HTML + extracted MD | `.raw/wechat/` | `YYYY-MM-DD_<slug>_<wxid>.{html,md}` |
| PDFs and Office docs | `.raw/pdf/` | `YYYY-MM-DD_<slug>.pdf` |
| Screenshots / images | `.raw/screenshots/` | single `YYYY-MM-DD_<slug>.<ext>`, multiple in `YYYY-MM-DD_<slug>/01.jpg 02.jpg ...` |
| GitHub READMEs + metadata | `.raw/github/` | `YYYY-MM-DD_<owner>_<repo>_README.md` + `_meta.json` |
| WebFetch snapshots | `.raw/webfetch/` | `YYYY-MM-DD_<domain>_<path-slug>.md` |
| Transcripts / dictation | `.raw/transcripts/` | `YYYY-MM-DD_<topic>.md` |

**Why.** Three reasons:

1. **Citation.** A year later you want to verify a claim — the raw lets you.
2. **Re-do.** If the synthesis was wrong, the raw lets you redo it without
   re-fetching.
3. **Loss.** The original page may 404 or get edited. Your archive is the
   only stable copy.

**How.** Hard sequence: `mkdir -p .raw/<type>/` → save raw → only then start
writing the synthesis note. **Failure to archive = failure to ingest.**

Exceptions (operator-approved 2026-05-03):
- Video: skip (downloader pipeline pending)
- Pre-2026-05-03 sources: no need to retroactively archive

---

## 9. Generate diagrams on hard sections (Chinese text)

**What.** When a section is hard to read without a diagram — abstract
mechanism, multi-element comparison, architecture / pipeline,
biology mechanism, algorithm flow — generate one. All text inside the image
must be Simplified Chinese (titles, labels, callouts, headers). Model
defaults to `gpt-image-2` via the configured proxy (see
`setup/06-image-generation.md`).

**Why.** Phone-first reading. OCR is friction. Diagrams with Chinese labels
share cleanly with non-English colleagues and don't need re-rendering.

**How.** Per-note: 0-2 diagrams. More is overkill. Save to
`wiki/_attachments/<note-slug>/<name>.png`. Embed via wikilink. Log path
under `Output:` in the matching `log.md` entry. On retry failure (>3),
leave `（图待补：<description>）` in place and move on — don't block the
note.

---

## 10. Hard concepts get an analogy or example

**What.** When a section uses a concept that's abstract / cross-disciplinary
/ jargon-heavy, drop an analogy or concrete example inline. Forms (most
common first):

| Form | Use when… | Example |
| --- | --- | --- |
| Life analogy | Abstract mechanism | "Egress 费就像健身房合约的退会费，进门便宜出门贵" |
| Familiar-product parallel | Showing generational evolution | "OrioleDB 之于 PostgreSQL 像 InnoDB 之于 MySQL 早期 MyISAM" |
| Quantified concrete | Conveying scale | "PB 级日志 ≈ 5 万部 4K 电影的体积" |
| Scenario re-enactment | Workflow or failure | "Anthropic 3 人管 PB 级 ClickHouse = 像 3 人开滴滴公司，车队是百万辆" |
| Counter-example | Limit conditions | "TiDB 不擅长场景 = 给你一辆超跑跑山路 — 不是车不好，是路不匹配" |

**Why.** Analogies are memory hooks for working memory. Cheaper than
diagrams (rule 9), faster to read, easier to forward.

**How.** Position: directly under the first mention of the concept, in
`（打比方：xxx）` inline form or `> [!tip] 类比：xxx` callout when
substantial. 3-5 analogies per note is plenty. **Don't analogize when:**

- The concept is already obvious
- The analogy is forced and could mislead — better to leave it unanalogized
- The analogy touches sensitive / cultural / violence themes (image
  moderation pain, and just generally not necessary)

---

## How the rules compose

For a typical "ingest this article" flow:

1. **8** — Archive raw to `.raw/<type>/`
2. **2** — Read raw, summarize without external facts
3. **6** — Write the note with an abstract callout up top
4. **7.5** — Frontmatter — double-check YAML quote nesting
5. **7** — If WeChat: localize referenced images to `_attachments/`
6. **9** — On hard sections, optionally generate 1-2 Chinese-text diagrams
7. **10** — Add inline analogies where useful
8. **5** — Update `wiki/meta/notes-graph.md` with cross-source connections
9. **6.5** — Append entry to `wiki/log.md`

For a "synthesize multiple sources" flow:

- Same plus: the abstract must say "哪几篇合并，为什么合"
- Body cites each merged source as a wikilink
- Anything NOT in any of the sources requires a `[!external]` label (rules
  2 + 3)
- `tags:` should include `synthesis`
