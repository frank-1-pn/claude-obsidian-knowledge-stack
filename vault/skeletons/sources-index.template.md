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
> 笔记后缀 _(synthesis)_。
>
> 这份和 `wiki/index.md` 内容重复（一份在 vault 根，一份在 `sources/` 内）；
> 选 1 份单独维护即可。两份并存是 Obsidian 习惯：根 index 方便从 graph view 跳转，
> 子目录 _index 方便在子目录浏览时不必跳出。

---

## 📂 <Domain 1>/（N 篇）

> 1-2 句话讲这个 domain 是什么。

- [[<note 1>]]
- [[<note 2>]]
- [[<note 3>]] _(synthesis)_

## 📂 <Domain 2>/（N 篇，分 K 子目录）

> 1-2 句话讲这个 domain 是什么。

### 📁 01-<subdomain>/（N 篇）

子目录定位 1 句话。

- [[<note>]]
- [[<note>]]

### 📁 02-<subdomain>/（N 篇）

- [[<note>]]

## 📂 <Domain 3>/（N 篇）

- [[<note>]]

---

## 维护

- 加新源 → 加一行到对应 domain
- domain 内 >15 篇 → 考虑切子目录；切完跑 `wiki-lint` 或手 grep `[[wikilink]]` 看链接是否都解析
- 同步：每次大重排后核对 `wiki/index.md` 和本文件保持一致
