# Vault conventions

How every page is shaped. These are mechanical / surface-level rules
(frontmatter, callouts, wikilinks); the semantic / generation rules are in
`note-generation-rules.md`.

## Frontmatter

Every source note starts with YAML frontmatter:

```yaml
---
type: source           # source | synthesis | meta | log
title: "<full descriptive title>"
source: "<URL / book / conversation date / GitHub repo + version>"
created: 2026-MM-DD
tags:
  - <topic-tag>
  - <secondary-tag>
related:
  - "[[Another Note Title]]"
  - "[[Yet Another]]"
raw_path:
  - .raw/<type>/<YYYY-MM-DD>_<slug>.<ext>
---
```

### Field meanings

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `source` = one atomic input; `synthesis` = derived overview combining N sources; `meta` = index / dashboard / notes-graph / log / 最新笔记 / glossary-index |
| `title` | yes | Full title; can repeat the filename or be longer. Quote with `"` and use `'` inside (NOT same-kind nested) |
| `source` | yes | Where the content came from. Long titles with punctuation must follow the YAML quote-nesting rules (next section) |
| `created` | yes | ISO date when the note was first written |
| `tags` | yes | 3-8 tags; first one is usually domain/topic, the rest narrow it |
| `related` | optional | Wikilinks to neighbor notes; populated by hand or `wiki-lint` |
| `raw_path` | required when sourced from archived raw | Relative path(s) to the `.raw/` archive of the original input |

### YAML quote-nesting trap

Same-kind nested quotes in YAML strings break parsing **silently** — Obsidian
shows the frontmatter as red raw text and `tags` / `related` stop working.

```yaml
# WRONG — inner " closes outer "
source: "公众号文章《大模型不卷参数，而是"生物原生数据基础设施"》"

# RIGHT — outer ", inner '
source: "公众号文章《大模型不卷参数，而是'生物原生数据基础设施'》"

# RIGHT — outer ", inner Chinese 「 」
source: "公众号文章《大模型不卷参数，而是『生物原生数据基础设施』》"

# RIGHT — outer ', inner "
source: '公众号文章《大模型不卷参数，而是"生物原生数据基础设施"》'

# RIGHT — block scalar (no quoting needed)
source: |
  公众号文章《大模型不卷参数，而是"生物原生数据基础设施"》
```

**Sanity check before writing**: scan the long string fields for opposite-pair
quotes; if any are same-kind, change inner to opposite kind or use a block
scalar.

## Wikilinks

Always use `[[Wikilink Form]]` with the displayed page title (NOT the file
path). Obsidian resolves by filename across the whole vault — moves don't
break links.

```markdown
See [[Anthropic Prompt Caching 是构建 Claude Code 的一切 7 条工程经验]] for
context.

If the wikilink target doesn't exist yet (you're forward-referencing), the
link still works — Obsidian shows it as a hollow / red link, prompting you
to create the note when ready.
```

Aliasing:

```markdown
See [[Anthropic Prompt Caching 是构建 Claude Code 的一切 7 条工程经验|prompt caching guide]]
```

Embedding (transcludes the target):

```markdown
![[Some Other Note]]
```

For images and attachments:

```markdown
![[<note-slug>/<diagram-name>.png]]
```

## Callouts

Use Obsidian's native callouts. The vault uses a small set with specific
meanings:

```markdown
> [!abstract] 摘要
> 这是 X 的整理，来源 Y，涉及主题 Z。
>
> - 核心看点 1
> - 核心看点 2
>
> 适合 [谁] 在 [场景] 时回头查。
```

→ Every source / synthesis note starts with `> [!abstract] 摘要` per
`note-generation-rules.md` rule 6. Note the blank `>` lines around the list
— per rule 11, any callout with more than one paragraph/block needs a blank
`>` separator between them, or Obsidian's mobile renderer merges everything
into one unreadable blob.

```markdown
> [!insight] Claude 的洞见
> 这条不是原文，是 Claude 看完后补的判断/推断/类比/反例。
```

→ Any external knowledge added on top of the source must be marked. See rule
3.

```markdown
> [!external] 外部补充
> 文章里没有这一段，是 Claude 从 [memory / 上一份对话 / 通用知识] 补的：xxx
```

→ When `[!insight]` doesn't fit (e.g., a single fact you needed to look up),
use `[!external]`.

```markdown
> [!warning]
> 这里有一个常见踩坑：xxx
```

→ Hard-won lesson worth flagging in dotted yellow.

```markdown
> [!tip]
> 类比：xxx 就像 yyy。
```

→ Per rule 10, when a concept is hard, the analogy goes in a tip callout if
it's substantial, or inline `（打比方：…）` if it's brief.

## Headings

H1 (`#`) is the note title — exactly one per file. Obsidian shows the
filename as the page title; H1 is for in-content display. Common to skip H1
entirely and let the filename + abstract callout serve as the title.

H2 (`##`) is the main section. Number them in Chinese / Roman / Arabic — pick
one style per note and be consistent.

```markdown
## 一、第一节
## 二、第二节
## 三、第三节
```

H3 + H4 for subsections; rarely deeper.

## Lists

- Use `-` not `*` for bullets (consistency)
- Indent with 2 spaces for nesting
- Numbered lists for ordered steps

## Tables

Standard markdown tables. For wide tables, prefer multiple narrow tables over
one impossible-to-read wide one.

| Column 1 | Column 2 |
| --- | --- |
| Value | Value |

## Images

Per rules 7 and 9, images that the note references are localized. The
default embed form is the wikilink — it survives folder moves and matches
how Obsidian shows other internal references:

```markdown
![[<note-slug>/<descriptive-name>.png]]
```

The relative-path form works too and is occasionally useful when the note
will be exported as plain Markdown to a non-Obsidian viewer:

```markdown
![描述说明](../../_attachments/<note-slug>/<descriptive-name>.png)
```

Pick wikilink unless you have a specific export reason. Mixing both
in the same vault is fine, but be consistent within a single note.

## File names

- Spaces are fine
- Chinese is fine
- Avoid `?`, `:`, `/`, `\`, `<`, `>`, `*`, `|`, `"`, `#`
- 100 characters max (Windows path length safety)
- Be descriptive — Obsidian's filename-based wikilink resolution means file
  names ARE the public identity of the note

## Tags

- All-lowercase, hyphenated for multi-word: `prompt-caching`,
  `multi-agent`, `claude-code`, `chinese-text`
- Domain tags first: `ai`, `bio`, `tooling`, `workflow`
- 3-8 tags per note is typical

Avoid tag explosion: every tag you invent should be intentional and reusable.
Single-use tags pollute the tag pane.

## What you don't need to do

- Don't write a table of contents — Obsidian generates one in the outline
  pane
- Don't add HTML — pure markdown, Obsidian renders it
- Don't add timestamps in body text — `created` in frontmatter is enough
- Don't add "back to top" links — Obsidian's outline does it

## Next

Read `note-generation-rules.md` for the twelve generation-time rules Claude
follows when creating or updating notes.
