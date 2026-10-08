---
name: autoresearch
description: >
  Autonomous iterative research loop. Takes a topic, runs web searches, fetches sources,
  archives source snapshots, synthesizes findings, and files one atomic source note by default.
  Based on Karpathy's autoresearch pattern: program.md configures objectives and constraints,
  the loop runs until depth is reached, output goes directly into the knowledge base.
  Triggers on: "/autoresearch", "autoresearch", "research [topic]", "deep dive into [topic]",
  "investigate [topic]", "find everything about [topic]", "research and file",
  "go research", "build a wiki on".
---

# autoresearch: Autonomous Research Loop

> [!danger] 本 vault 覆盖上游模板：Note-as-atom 架构（必读，优先级最高）
> autoresearch 默认只产出**一篇综述源笔记**放在 `wiki/sources/`，不按人物、产品、术语或待研究问题拆页。只有用户明确说「建研究子页」时，才可在 `wiki/sources/research/<topic>/` 增加研究子页。跨笔记关系统一写进 `wiki/meta/notes-graph.md`。完整规则见仓库根 `AGENTS.md`。

You are a research agent. You take a topic, run iterative web searches, archive every source used, synthesize the findings, and file the result into the wiki. The user gets a durable atomic note plus a concise completion report.

This is based on Karpathy's autoresearch pattern: a configurable program defines your objectives. You run the loop until depth is reached. Output goes into the knowledge base.

---

## Before Starting

Read `references/program.md` to load the research objectives and constraints. This file is user-configurable. It defines what sources to prefer, how to score confidence, and any domain-specific constraints.

---

## Research Loop

```
Input: topic (from user command)

Round 1. Broad search
1. Decompose topic into 3-5 distinct search angles
2. For each angle: run 2-3 WebSearch queries
3. For top 2-3 results per angle: WebFetch the page
4. Extract from each: key claims, named subjects, mechanisms, disagreements, and remaining gaps

Round 2. Gap fill
5. Identify what's missing or contradicted from Round 1
6. Run targeted searches for each gap (max 5 queries)
7. Fetch top results for each gap

Round 3. Synthesis check (optional, if gaps remain)
8. If major contradictions or missing pieces still exist: one more targeted pass
9. Otherwise: proceed to filing

Max rounds: 3 (as set in program.md). Stop when depth is reached or max rounds hit.
```

---

## Filing Results

Before drafting, save every webpage or document actually used under the matching `.raw/<type>/` directory defined by root `AGENTS.md`. Raw snapshots are immutable after archival.

Default output:

- Create one synthesis note under the appropriate `wiki/sources/<domain>/` folder.
- Keep all people, organizations, products, mechanisms, disagreements, and research gaps inside that note.
- Add links to existing source notes through frontmatter `related`; record cross-note relationships in `wiki/meta/notes-graph.md`.
- Do not create standalone topic, person, product, or gap pages.

Explicit research-subpage mode:

- Activate only when the user explicitly says 「建研究子页」 or an unambiguous equivalent.
- Put every extra page under `wiki/sources/research/<topic>/`.
- Each extra page must cover one coherent source or research angle, link its own archived material with `raw_path`, and remain an atomic source/research note.
- Write the required `wiki/log.md` entry immediately after completing each page; do not postpone logs until the whole research batch finishes.

---

## Synthesis Page Structure

```markdown
---
type: synthesis
title: "Research: [Topic]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - research
  - [topic-tag]
status: developing
related:
  - "[[Existing Related Source Note]]"
raw_path:
  - .raw/webfetch/YYYY-MM-DD_domain_source-one.md
  - .raw/webfetch/YYYY-MM-DD_domain_source-two.md
provenance:
  schema: v1
  model: <model-id>
  derived: false
  recorded: YYYY-MM-DD
  verified:
    - raw-archived
    - web-fetch
---

# Research: [Topic]

> [!abstract] 摘要
>
> [100–200 字：研究对象、来源范围、2–4 个核心看点。]

## Overview
[2-3 sentence summary of what was found]

## Key Findings
- Finding 1 (Source: original URL and archived raw path)
- Finding 2 (Source: original URL and archived raw path)
- ...

## Important Subjects and Mechanisms
- [Name or mechanism]: role/significance in this research

## Contradictions
- Source A says X. Source B says Y. Cite their original URLs and raw paths; use wikilinks only for notes that actually exist.

## Remaining Gaps
- [Question that research didn't fully answer]
- [Gap that needs more sources]

## Sources
- Source 1: author, date, original URL, archived raw path
- Source 2: author, date, original URL, archived raw path
```

---

## After Filing

For every note completed, finish these steps before moving to another note:

1. Update `wiki/meta/notes-graph.md` with relationships supported by the archived sources.
2. Update `wiki/index.md` if this vault's index tracks that source folder.
3. Append the required entry to the TOP of `wiki/log.md` immediately:
   ```
   ## [YYYY-MM-DD] autoresearch | [Topic]
   - Rounds: N
   - Sources found: N
   - 原始物：.raw/<type>/...
   - Output: [[Research Note]]
   - Key finding: [one sentence]
   ```
4. Update `wiki/hot.md` with the research summary.
5. Run `python scripts/refresh-latest.py` so `wiki/最新笔记.md` includes the new note.

---

## Report to User

After filing everything:

```
Research complete: [Topic]

Rounds: N | Searches: N | Notes created: N

Created:
  wiki/sources/<domain>/Research [Topic].md

Key findings:
- [Finding 1]
- [Finding 2]
- [Finding 3]

Remaining gaps recorded: N
```

---

## Constraints

Follow the limits in `references/program.md`:
- Max rounds (default: 3)
- Default one synthesis note; extra research pages only with explicit user authorization
- Confidence scoring rules
- Source preference rules

If a constraint conflicts with completeness, respect the constraint and record what was left out in the Remaining Gaps section.


## 宿主适配

先读根 AGENTS.md。使用宿主实际提供的文件、搜索、网页和连接器工具；本文的 Claude 工具名与斜杠命令表示能力或意图，不要求在 WorkBuddy 安装同名工具。缺少自动 skill 发现时，直接按相对路径读取本文件。
