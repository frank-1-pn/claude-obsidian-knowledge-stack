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
---

# Vault index

> Note-as-atom 架构。所有源笔记按 domain 分子文件夹；每篇一行一句话讲讲。

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

## 维护

- 每次新加 source / synthesis → 加到对应 domain 一行
- 每次 domain 内笔记 > 15 篇 → 考虑切子目录
- 每次切子目录 → 跑 `wiki-lint` 或手 grep 所有 `[[wikilink]]` 验证仍可解析（Obsidian filename-based 链接通常能自动跟）
- _(synthesis)_ / _(industry)_ / _(产业实战)_ 等小标签放笔记后面，方便扫
