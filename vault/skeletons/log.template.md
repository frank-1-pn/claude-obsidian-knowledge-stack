---
type: meta
title: Vault log
updated: 2026-MM-DD
tags:
  - meta
  - log
---

> [!abstract] 这是什么
> Vault 时间线。每次 ingest / synthesis / 架构变更 / bugfix 都在顶部追加一条。
> 新的在最上面（reverse chronological）。
>
> 参考规则 [[note-generation-rules.md|note-generation rules §6.5]]。

---

## [2026-MM-DD] organize+insight | <Title>

- 触发：用户原话"<复制粘贴>"
- 原文取全：wechatDownload MCP → `single_article_download(url)` → 30s 后落 `<download dir>/<account>/<title>.{html,md}`
- 原始物：
  - `.raw/wechat/2026-MM-DD_<slug>_<wxid>.html`
  - `.raw/wechat/2026-MM-DD_<slug>_<wxid>.md`
- Output：[[<note title>]]（`wiki/sources/<domain>/<title>.md`）+ 1 张配图 `_attachments/<slug>/<name>.png`
- 内容：2-3 句关键事实总结。
- 外部洞见：3 处 `[!insight]`
  - 观察 1：……
  - 观察 2：……
  - 观察 3：……
- 跨笔记关联：[[相关笔记 A]] / [[相关笔记 B]]
- YAML 校验：通过

## [2026-MM-DD] synthesis | <Title>

- 触发：……
- 合并来源：[[A]] + [[B]] + [[C]]
- 合并视角：……
- Output：[[<synthesis title>]]（`wiki/sources/synthesis/<title>.md`）
- 外部洞见：N 处
- 跨笔记关联：……
- YAML 校验：通过

## [2026-MM-DD] bugfix | <description>

- 触发：用户报告 [[<note>]] frontmatter 红色
- 原因：source 字段同种 quote 嵌套
- Fix：内层 `"` 改 `'`
- 校验：通过

## [2026-MM-DD] architecture-switch | <description>

- 触发：……
- 改前 → 改后：……
- 影响的笔记：N 个，列表 …… 或 wiki-lint 跑出来的
- 通过校验：是 / 否

## [2026-MM-DD] init | Vault scaffolded

- 触发：bootstrap claude-obsidian-knowledge-stack 第 4 步
- 操作：建立 `wiki/`, `meta/`, `_attachments/`, `.raw/`；从 stack 模板复制 7 个文件
- 校验：Obsidian 打开 vault 正常，sync 配置 done

---

**Operation 词典**：

`organize` / `organize+insight` / `synthesis` / `ingest` / `bugfix` /
`architecture-switch` / `cleanup` / `rule-migration` / `infrastructure` /
`init`
