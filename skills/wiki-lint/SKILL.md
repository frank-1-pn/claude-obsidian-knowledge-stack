---
name: wiki-lint
description: >
  Health check the Obsidian wiki vault. Finds orphan pages, dead wikilinks, stale claims,
  missing cross-references, frontmatter gaps, and empty sections. Creates or updates
  Dataview dashboards. Generates canvas maps. Triggers on: "lint", "health check",
  "clean up wiki", "check the wiki", "wiki maintenance", "find orphans", "wiki audit".
---

# wiki-lint: Wiki Health Check

Run lint after every 10-15 ingests, or weekly. Ask before auto-fixing anything. Output a lint report to `wiki/meta/lint-report-YYYY-MM-DD.md`.

This vault uses Note-as-atom. Scan content notes under `wiki/sources/` and structural metadata under `wiki/meta/`. Repair relationships in `wiki/meta/notes-graph.md`; never propose new standalone pages for names, products, topics, or gaps. Root `AGENTS.md` is authoritative.

---

## Lint Checks

Work through these in order:

1. **Orphan pages**. Wiki pages with no inbound wikilinks. They exist but nothing points to them.
2. **Dead links**. Wikilinks that reference a page that does not exist.
3. **Stale claims**. Assertions on older pages that newer sources have contradicted or updated.
4. **Missing graph relationships**. Repeated subjects or claims across source notes that are not represented in `wiki/meta/notes-graph.md`.
5. **Missing cross-references**. Existing related source notes missing from frontmatter `related` or the centralized graph.
6. **Frontmatter gaps**. Source notes missing required fields such as `type`, `created`, `tags`, `raw_path`, or `provenance`.
7. **Empty sections**. Headings with no content underneath.
8. **Stale index entries**. Items in `wiki/index.md`, `wiki/最新笔记.md`, or source-folder indexes pointing to renamed or deleted notes.

---

## Lint Report Format

Create at `wiki/meta/lint-report-YYYY-MM-DD.md`:

```markdown
---
type: meta
title: "Lint Report YYYY-MM-DD"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [meta, lint]
status: developing
---

# Lint Report: YYYY-MM-DD

## Summary
- Pages scanned: N
- Issues found: N
- Auto-fixed: N
- Needs review: N

## Orphan Pages
- [[Page Name]]: no inbound links. Suggest: link from [[Related Page]] or delete.

## Dead Links
- [[Missing Note]]: referenced in [[Source Note]] but does not exist. Suggest: correct the target or remove the stale metadata link after review.

## Missing Graph Relationships
- "shared subject": supported by [[Source A]], [[Source B]], and [[Source C]] but absent from `wiki/meta/notes-graph.md`. Suggest: add one relationship entry to the graph.

## Frontmatter Gaps
- [[Page Name]]: missing fields: status, tags

## Stale Claims
- [[Page Name]]: claim "X" may conflict with newer source [[Newer Source]].

## Cross-Reference Gaps
- [[Related Source]] is relevant to [[Source A]] but absent from its `related` metadata and the centralized graph.
```

---

## Naming Conventions

Enforce these during lint:

| Element | Convention | Example |
|---------|-----------|---------|
| Filenames | Descriptive: what the note is about | `AirLLM 分层流式加载 让 70B 跑在单张 4GB 显卡.md` |
| Folders | Source domain below `wiki/sources/` | `wiki/sources/AI技术/` |
| Tags | lowercase, hyphenated | `agent-memory` |
| Wikilinks | match filename exactly | `[[AirLLM 分层流式加载 让 70B 跑在单张 4GB 显卡]]` |

Filenames must be unique across the vault. Wikilinks work without paths only if filenames are unique.

---

## Writing Style Check

During lint, flag pages that violate the style guide:

- Not declarative present tense ("X basically does Y" instead of "X does Y")
- Missing source citations where claims are made
- Uncertainty not flagged with `> [!gap]`
- Contradictions not flagged with `> [!contradiction]`

---

## Dataview Dashboard

Create or update `wiki/meta/dashboard.md` with these queries:

````markdown
---
type: meta
title: "Dashboard"
updated: YYYY-MM-DD
---
# Wiki Dashboard

## Recent Activity
```dataview
TABLE source_type, created, file.folder FROM "wiki/sources" SORT created DESC LIMIT 15
```

## Source Notes Missing Raw Paths
```dataview
LIST FROM "wiki/sources" WHERE !raw_path SORT file.mtime DESC
```

## Source Notes Missing Provenance
```dataview
LIST FROM "wiki/sources" WHERE !provenance SORT file.mtime DESC
```
````

---

## Canvas Map

Create or update `wiki/meta/overview.canvas` for a visual domain map:

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "file",
      "file": "wiki/meta/notes-graph.md",
      "x": 0, "y": 0,
      "width": 300, "height": 140,
      "color": "1"
    }
  ],
  "edges": []
}
```

Add only existing files from `wiki/sources/` or `wiki/meta/`. Connect source notes using relationships already recorded in `wiki/meta/notes-graph.md`. Colors map to the CSS scheme: 1=blue, 2=purple, 3=yellow, 4=orange, 5=green, 6=red.

---

## Before Auto-Fixing

Always show the lint report first. Ask: "Should I fix these automatically, or do you want to review each one?"

Safe to auto-fix:
- Regenerating `wiki/最新笔记.md` with the existing refresh script
- Correcting deterministic stale paths in indexes and `wiki/meta/notes-graph.md`
- Adding frontmatter `tags` or `related` only when the value is unambiguous and source-supported

Needs review before fixing:
- Deleting orphan pages (they might be intentionally isolated)
- Resolving contradictions (requires human judgment)
- Merging duplicate pages
- Filling provenance fields when the actual verification method cannot be reconstructed
- Any source-note body edit; source bodies require an explicit user instruction to organize that note


## 宿主适配

先读根 AGENTS.md。使用宿主实际提供的文件、搜索、网页和连接器工具；本文的 Claude 工具名与斜杠命令表示能力或意图，不要求在 WorkBuddy 安装同名工具。缺少自动 skill 发现时，直接按相对路径读取本文件。
