---
type: meta
title: Sources index
updated:
tags:
  - meta
  - index
status: evergreen
related:
  - "[[index]]"
  - "[[notes-graph]]"
---

# Sources Index

> Note-as-atom 架构。所有源笔记按 domain 分子文件夹。每篇一行；synthesis / 综述
> 笔记后缀 _(synthesis)_。每个 domain / 子目录下面带一行 **📌 投放规则**——判断
> "新笔记该放哪"用这个，两可时优先看"动作/主体是什么"而非"用什么工具"。
>
> 这份和 `wiki/index.md` 内容重复（一份在 vault 根，一份在 `sources/` 内）；
> 选 1 份单独维护即可。两份并存是 Obsidian 习惯：根 index 方便从 graph view 跳转，
> 子目录 _index 方便在子目录浏览时不必跳出。`wiki/<glossary>/`（若启用）是独立子系统，
> **不在此索引内**——见 `vault/structure.md` 的"Optional: 一个独立的术语表子系统"。

---

## 📂 <Domain 1>/（N 篇）

> 1-2 句话讲这个 domain 是什么。

> 📌 **投放规则**：一句话讲清楚"看到什么样的新料就往这儿放"——例如"任何讲『某个可
> 下载/可用产品本身』的笔记，无论工具",或"任何讲『通用方法论、不绑定单一产品』的
> 笔记"。两可时按这条规则判断，不按笔记用了什么工具写成判断。

- [[<note 1>]]
- [[<note 2>]]
- [[<note 3>]] _(synthesis)_

## 📂 <Domain 2>/（N 篇，分 K 子目录）

> 1-2 句话讲这个 domain 是什么。

### 📁 01-<subdomain>/（N 篇）

子目录定位 1 句话。

> 📌 **投放规则**：这个子目录专收什么——1 句话判据。

- [[<note>]]
- [[<note>]]

### 📁 02-<subdomain>/（N 篇）

> 📌 **投放规则**：这个子目录专收什么——1 句话判据。

- [[<note>]]

## 📂 <Domain 3>/（N 篇）

> 📌 **投放规则**：这个 domain 专收什么——1 句话判据。

- [[<note>]]

---

## 维护

- 加新源 → 对照目标 domain / 子目录的 **📌 投放规则** 判断归属，加一行
- domain 内 >15 篇 → 考虑切子目录；切完给新子目录也写一条 📌 投放规则，并跑
  `wiki-lint` 或手 grep `[[wikilink]]` 看链接是否都解析
- 新增/合并 domain → 投放规则要跟着更新，不要留旧描述让新笔记无处安放
- 同步：每次大重排后核对 `wiki/index.md` 和本文件保持一致
