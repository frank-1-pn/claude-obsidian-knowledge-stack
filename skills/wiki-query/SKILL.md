---
name: wiki-query
description: "Answer questions using the Obsidian wiki vault. Reads hot cache first, then indexes and relevant atomic source notes, and synthesizes answers with citations. Remains read-only unless the user explicitly asks to save. Supports quick, standard, and deep modes. Triggers on: what do you know about, query:, what is, explain, summarize, find in wiki, search the wiki, based on the wiki, wiki query quick, wiki query deep."
---

# wiki-query: Query the Wiki

The wiki has already done the synthesis work. Read strategically and answer precisely. Content lives in `wiki/sources/`; relationships live in `wiki/meta/notes-graph.md`. Querying is read-only unless the user explicitly asks to save the answer.

---

## Query Modes

Three depths. Choose based on the question complexity.

| Mode | Trigger | Reads | Token cost | Best for |
|------|---------|-------|------------|---------|
| **Quick** | `query quick: ...` or simple factual Q | hot.md + index.md only | ~1,500 | "What is X?", date lookups, quick facts |
| **Standard** | default (no flag) | hot.md + index + 3-5 pages | ~3,000 | Most questions |
| **Deep** | `query deep: ...` or "thorough", "comprehensive" | Full wiki + optional web | ~8,000+ | "Compare A vs B across everything", synthesis, gap analysis |

---

## Quick Mode

Use when the answer is likely in the hot cache or index summary.

1. Read `wiki/hot.md`. If it answers the question, respond immediately.
2. If not, read `wiki/index.md`. Scan descriptions for the answer.
3. If found in index summary, respond and do not open any pages.
4. If not found, say "Not in quick cache. Run as standard query?"

Do not open individual wiki pages in quick mode.

---

## Standard Query Workflow

1. **Read** `wiki/hot.md` first. It may already have the answer or directly relevant context.
2. **Read** `wiki/index.md` to find the most relevant pages (scan for titles and descriptions).
3. **Read** those atomic source notes. Follow links to other relevant source notes to depth 2. No deeper.
4. **Synthesize** the answer in chat. Cite sources with wikilinks: `(Source: [[Page Name]])`.
5. Do not write a note by default. If the user explicitly asks to preserve the answer, route it through `/save` as one session note under `wiki/sources/sessions/`.
6. If the question reveals a **gap**: say "I don't have enough on X. Want to find a source?"

---

## Deep Mode

Use for synthesis questions, comparisons, or "tell me everything about X."

1. Read `wiki/hot.md` and `wiki/index.md`.
2. Identify all relevant source folders, atomic notes, and graph relationships.
3. Read every relevant page. No skipping.
4. If wiki coverage is thin, offer to supplement with web search.
5. Synthesize a comprehensive answer with full citations.
6. Return the result in chat. Save it only when the user explicitly asks; then use the single-note `/save` workflow.

---

## Token Discipline

Read the minimum needed:

| Start with | Cost (approx) | When to stop |
|------------|---------------|--------------|
| hot.md | ~500 tokens | If it has the answer |
| index.md | ~1000 tokens | If you can identify 3-5 relevant pages |
| 3-5 wiki pages | ~300 tokens each | Usually sufficient |
| 10+ wiki pages | expensive | Only for synthesis across the entire wiki |

If hot.md has the answer, respond without reading further.

---

## Index Format Reference

Use `wiki/index.md` as a route into source folders; treat its current contents as authoritative instead of assuming fixed legacy sections. A compatible Note-as-atom index may look like:

```markdown
## Source Domains
- [[AI技术]]: source-folder index or overview

## Recent Sources
- [[Source Title]]: author, date, type

## Metadata
- [[notes-graph]]: cross-note relationships
```

Scan the section headers first to determine which sections to read.

---

## Source-Folder Index Format

When a source domain already has an `_index.md`, use it for focused lookups:

```markdown
---
type: meta
title: "AI Technology Sources"
updated: YYYY-MM-DD
---
# AI Technology Sources

## Recent Notes
- [[Source Note A]]: what this source covers
- [[Source Note B]]: what this source covers
```

Use sub-indexes when the question is scoped to one domain. Avoid reading the full master index for narrow queries.

---

## Filing Answers Back

Do not file an answer merely because it seems useful. When the user explicitly asks to preserve it, invoke the `/save` workflow. That workflow creates one atomic note in `wiki/sources/sessions/`, archives the conversation under `.raw/transcripts/`, updates `wiki/meta/notes-graph.md`, writes the log immediately, and refreshes `wiki/最新笔记.md`.

---

## Gap Handling

If the question cannot be answered from the wiki:

1. Say clearly: "I don't have enough in the wiki to answer this well."
2. Identify the specific gap: "I have nothing on [subtopic]."
3. Suggest: "Want to find a source on this? I can help you search or process one."
4. Do not fabricate. Do not answer from training data if the question is about the specific domain in this wiki.


## 宿主适配

先读根 AGENTS.md。使用宿主实际提供的文件、搜索、网页和连接器工具；本文的 Claude 工具名与斜杠命令表示能力或意图，不要求在 WorkBuddy 安装同名工具。缺少自动 skill 发现时，直接按相对路径读取本文件。
