---
type: meta
title: Vault index
updated: 2026-MM-DD
tags:
  - meta
  - index
status: evergreen
related:
  - "[[overview]]"
  - "[[notes-graph]]"
  - "[[hot]]"
  - "[[log]]"
  - "[[sources/_index]]"
---

# Vault index

Navigation: [[hot]] | [[notes-graph]] | [[log]] | [[sources/_index]] | 🆕 [[最新笔记]]

> Note-as-atom 架构。所有源笔记按 domain 分子文件夹；每篇一行一句话讲讲。
>
> 想知道"最新加了什么"直接点上面的 🆕 [[最新笔记]]，不用逐个 domain 翻。

---

## 结构地图

一眼扫清 vault 顶层都装了什么、有多少篇——新增/合并 domain 时这张表和下面的分组
小节要一起更新：

| # | 文件夹 | 篇 | 装什么 |
| --- | --- | --- | --- |
| 1 | `<Domain 1>/` | N | <一句话：这个 domain 装什么> |
| 2 | `<Domain 2>/` | N | <一句话：这个 domain 装什么，K 个子目录> |
| 3 | `<Domain 3>/` | N | <一句话：这个 domain 装什么> |
| — | `<glossary>/`（可选） | N | 术语/黑话解释页——**独立子系统**，详见本页末尾说明 |

---

## 📂 <Domain 1>/（N 篇）

> 这个 domain 的一句话定位。

- [[<note title 1>]]
- [[<note title 2>]]
- [[<note title 3>]] _(synthesis)_

## 📂 <Domain 2>/（N 篇，分 K 子目录）

> 这个 domain 的一句话定位。

### 📁 01-<subdomain title>/（N 篇）

子目录定位（1 句话）。

- [[<note title>]]
- [[<note title>]]

### 📁 02-<subdomain title>/（N 篇）

- [[<note title>]]

## 📂 <Domain 3>/（N 篇）

> 这个 domain 的一句话定位。

- [[<note title>]]

---

## 术语表 / 独立子系统（可选）

若这个 vault 启用了 `wiki/<glossary>/`（术语/黑话解释页），它**不在本索引内**——
它有自己的 `_index.md`（术语表 + 自己的操作日志），也不进 [[notes-graph]] /
[[log]]。这是 Note-as-atom（不拆源，见 note-generation-rules.md 第 5 条）**唯一
有意的例外**：每个术语单独成一个概念实体页，专为"讲人话、多举例、打比方"设计，跟
`sources/` 的"1 源 = 1 原子笔记"规则不是一套体系。要查术语时直接开
`wiki/<glossary>/_index.md`，不是在这份索引里翻。

## 维护

- 每次新加 source / synthesis → 加到对应 domain 一行 + 更新上面「结构地图」的篇数
- 每次 domain 内笔记 > 15 篇 → 考虑切子目录
- 每次切子目录 → 跑 `wiki-lint` 或手 grep 所有 `[[wikilink]]` 验证仍可解析（Obsidian filename-based 链接通常能自动跟）
- _(synthesis)_ / _(industry)_ / _(产业实战)_ 等小标签放笔记后面，方便扫
- 整理完一批笔记后 → 别忘了同一时间刷新 [[最新笔记]]（note-generation-rules.md §12）
