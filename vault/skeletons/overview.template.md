---
type: meta
title: Vault overview
updated: 2026-MM-DD
tags:
  - meta
  - overview
status: evergreen
related:
  - "[[index]]"
  - "[[notes-graph]]"
  - "[[hot]]"
---

# <vault name>

> [!abstract] 这是什么
> 这是我的 Claude + Obsidian 个人知识库。
> 主要存：
> - 我读过、整理过的东西（公众号文章 / 论文 / GitHub repo / 视频转录 / 对话归档）
> - 我自己产出的合并视角（synthesis）
> - 跨笔记的关键词 / 主题群组（在 `meta/notes-graph.md`）
>
> 维护人：<你的名字 / 团队> · 起始时间：YYYY-MM
>
> 公开度：私有（除非另注明）

---

## 内容范围

按 `wiki/sources/` 顶层目录划分：

- **<Domain 1>**：1 句话讲这个领域涉及什么、为什么我关注它
- **<Domain 2>**：...
- **<Domain 3>**：...

## 不放什么

- **新闻**（除非有长期价值）
- **代码片段**（除非配套笔记说清楚背景）
- **未整理的原料**（那个在 `.raw/`，不在 `wiki/`）
- **个人日程 / 私人通讯 / 财务记录**（用别的工具）

## 入站源（怎么进的）

| 来源 | 工具 / 路径 | 入口规则 |
|------|------------|----------|
| 微信公众号 | `wechatDownload` MCP → `.raw/wechat/` | 触发：飞书 bot 发 URL，或本地说"ingest 这篇" |
| arxiv / 博客 | `WebFetch` / `curl` → `.raw/webfetch/` | 触发：说"ingest 这个链接" |
| GitHub repos | `gh api` → `.raw/github/` | 触发：说"看下这个 repo" |
| 视频 / 长会 | 手转 → `.raw/transcripts/` | 触发：说"我整理一下这个会，要点 X Y Z" |
| 对话 | `/save` skill | 触发：说"save 一下这次对话" |
| 手写源 | 直接在 Obsidian 写 | 触发：在 `wiki/sources/<domain>/` 新建 .md |

## 同步与备份

- **跨设备**：Obsidian Sync（付费），E2E 加密
- **版本控制**：(可选) git，仓库私有；提交频率：每天 1-2 次
- **本地备份**：(可选) 定期 `robocopy` 到外部磁盘

## 联系 / 翻新规则

- 重大架构变更 → 在 `log.md` 写一条 `architecture-switch` 条目
- 规则修订 → 同步更新 `<vault>/CLAUDE.md` + 这份 overview 的相关章节
- 每月扫一次 `wiki-lint` 跑健康检查
