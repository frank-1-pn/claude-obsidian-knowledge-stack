---
name: save
description: >
  Save the current conversation, answer, or insight into the Obsidian wiki vault as a
  single atomic session note with a raw transcript record, frontmatter, graph links,
  log entry, index updates, and hot-cache refresh.
  Triggers on: "save this", "save that answer", "/save", "file this",
  "save to wiki", "save this session", "file this conversation", "keep this",
  "save this analysis", "add this to the wiki".
---

# save: File Conversations Into the Wiki

> [!danger] 本 vault 覆盖上游模板：Note-as-atom 架构（必读，优先级最高）
> `/save` 一律归档为 `wiki/sources/sessions/` 下的**单文件**。不要按主题、人物、术语、问题或决策拆成额外内容页；跨笔记关系写进 `wiki/meta/notes-graph.md`。完整规则见仓库根 `AGENTS.md`。

Good answers and insights shouldn't disappear into chat history. This skill takes what was just discussed and files it as a permanent wiki page.

The wiki compounds. Save often.

---

## Note Focus Decision

Choose the emphasis inside the single session note; the destination does not change:

| Focus | Emphasize |
|------|-----------|
| analysis | Reasoning, comparison, and conclusions |
| explanation | A clear explanation of an idea or mechanism |
| source-review | What external material contributed |
| decision | Decision, rationale, constraints, and consequences |
| session | The full durable context of the conversation |

If the user specifies a focus, use it. Otherwise choose the closest fit; when in doubt, use `session`.

---

## Save Workflow

1. **Scan** the current conversation. Identify the most valuable content to preserve.
2. **Choose a title** that says what the note contains. Ask only if the missing title would materially change the result.
3. **Archive first**: write a concise conversation record to `.raw/transcripts/YYYY-MM-DD_<slug>.md`. Do not begin the organized note before this exists; do not modify it afterward.
4. **Determine** the note focus using the table above.
5. **Extract** all relevant content. Rewrite it in declarative present tense (not "the user asked" but the actual content itself). Do not add outside knowledge unless the user requested it and each addition is marked external.
6. **Create one note** at `wiki/sources/sessions/<Title>.md` with the required abstract, `raw_path`, and truthful `provenance` block.
7. **Collect links**: add existing relevant source notes to frontmatter `related`, then update `wiki/meta/notes-graph.md`. Do not create additional content pages.
8. **Update** `wiki/index.md` if it tracks session sources.
9. **Append** to the TOP of `wiki/log.md` immediately after the note is complete:
   ```
   ## [YYYY-MM-DD] save | Note Title
   - 触发：<user request>
   - 原文取全：conversation archive
   - 原始物：.raw/transcripts/YYYY-MM-DD_<slug>.md
   - Output：[[Note Title]]（wiki/sources/sessions/Note Title.md）
   - 内容：<2–3 sentences>
   - 跨笔记关联：[[Related Note]]
   - YAML 校验：通过
   ```
10. **Update** `wiki/hot.md` to reflect the new addition.
11. **Refresh latest** by running `python scripts/refresh-latest.py`.
12. **Confirm**: "Saved as [[Note Title]] in wiki/sources/sessions/."

---

## Frontmatter Template

```yaml
---
type: source
source_type: session
note_focus: <analysis|explanation|source-review|decision|session>
title: "Note Title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - <relevant-tag>
status: developing
related:
  - "[[Any Wiki Page Mentioned]]"
raw_path:
  - .raw/transcripts/YYYY-MM-DD_note-slug.md
provenance:
  schema: v1
  model: <model-id>
  derived: false
  recorded: YYYY-MM-DD
  verified:
    - transcript
    - raw-archived
---
```

After the first `#` heading, add a 100–200 Chinese-character `> [!abstract] 摘要` callout. Inside callouts, put a blank `>` line between the title, paragraphs, and lists for mobile readability.

---

## Writing Style

- Declarative, present tense. Write the knowledge, not the conversation.
- Not: "The user asked about X and Claude explained..."
- Yes: "X works by doing Y. The key insight is Z."
- Include all relevant context. Future sessions should be able to read this page cold.
- Link relevant existing source notes with wikilinks; put broader relationships in `wiki/meta/notes-graph.md`.
- Cite sources where applicable: `(Source: [[Page]])`.

---

## What to Save vs. Skip

Save:
- Non-obvious insights or synthesis
- Decisions with rationale
- Analyses that took significant effort
- Comparisons that are likely to be referenced again
- Research findings

Skip:
- Mechanical Q&A (lookup questions with obvious answers)
- Setup steps already documented elsewhere
- Temporary debugging sessions with no lasting insight
- Anything already in the wiki

If the same material already exists, report the duplicate and avoid creating another note. Do not change an existing source-note body unless the user explicitly asks to organize that note; only frontmatter `tags` / `related` and graph metadata may be updated without that instruction.


## 宿主适配

先读根 AGENTS.md。使用宿主实际提供的文件、搜索、网页和连接器工具；本文的 Claude 工具名与斜杠命令表示能力或意图，不要求在 WorkBuddy 安装同名工具。缺少自动 skill 发现时，直接按相对路径读取本文件。
