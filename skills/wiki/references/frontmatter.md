# Frontmatter

Use source or synthesis for content, meta for structural pages. Keep names/products/concepts within the atomic note. YAML supports the nested provenance block.

```yaml
---
type: source
title: "项目名 + 它是什么"
created: YYYY-MM-DD
updated: YYYY-MM-DD
authors: []
url: ""
tags: []
status: developing
related: []
raw_path:
  - .raw/webfetch/YYYY-MM-DD_example.md
provenance:
  schema: v1
  model: unrecorded
  derived: false
  recorded: YYYY-MM-DD
  verified: []
---
```

模板中的 model、日期、路径、核实手段必须换为实际值；无法取得模型 id 时如实用 unrecorded。只有实际归档后才填 raw-archived。历史回溯用 derived: true；当次核实用 false。来源补充的事实附可核验依据，AI 解释明确标注。详见根 AGENTS.md 和 wiki/meta/provenance.md。
