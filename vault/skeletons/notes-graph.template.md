---
type: meta
title: Notes graph
updated: 2026-MM-DD
tags:
  - meta
  - graph
---

> [!abstract] 这是什么
> 全 vault 唯一的"跨笔记关系"页。entity / concept / question 都**不**单独成页——
> 任何跨笔记的关键词、对照、群组都写在这里。
>
> 维护方式：每次新增 / 大改源笔记 → 顺手更新本页相关章节。

---

## 1. 关键词索引（按字母 / 拼音）

### A

- **Agent 控制循环** → [[Anthropic Prompt Caching ...]] / [[Cline SDK 700 万 agent harness ...]] / [[Harness 工程实践复盘 OpenClacky ...]]
- **AI 制药** → [[合成致死 RAS MAT2A SHP2 机制总结]] / [[AACR 2026 Zoldonrasib ...]] / [[AI 药物设计讨论笔记 2026-04-19]]
- **autonomous driving** → ……

### B

…（按需）

### C

…

---

## 2. 主题群组

### 群组 A：Coding Agent 产品对照

涵盖各家 coding agent CLI 的功能/价格/工程取舍：
- [[Claude Code 长程任务记忆管理 4 方案对比]]
- [[cc-switch 多 Agent 模型切换桌面工具 51K Star]]
- [[Warp Agent 十个使用技巧 vs Claude Code]]
- [[DeepSeek-TUI 终端 Coding Agent ...]]
- [[Cline SDK 700 万 agent harness ...]]（synthesis）

**关键对比维度**：模型选择灵活性 / 长程记忆 / 多 agent 协作 / 价格 / 开源度

### 群组 B：靶向药物机制

涵盖 KRAS / RAS / 合成致死 等靶点的机制与药物：
- [[合成致死 RAS MAT2A SHP2 机制总结]]
- [[KRAS 靶向新局 合成致死与 RAS(ON) 分子胶整合]]（synthesis）
- [[pan-RAS(ON) 分子胶赛道 ERAS-0015 中国分子海外授权]]

**关键对比维度**：靶点验证程度 / 临床阶段 / 中国 vs 国外分子 / 授权交易

### 群组 C：……

---

## 3. 跨笔记观察（合并视角）

> [!insight] 观察 1：所有 coding agent 都在解决 context budget 问题
> [[Anthropic Prompt Caching ...]] 给出 caching 是关键技术；
> [[Claude Code 长程任务记忆管理 4 方案对比]] 列举了 compact / hand-off / sub-agent / RAG 4 种 budget 拓展方法；
> [[Harness 工程实践复盘 OpenClacky ...]] 给出"不做 RAG，做适合 AI 阅读的文档站"作为另一种思路。

> [!insight] 观察 2：……

---

## 4. 待补 / 待整理

- [ ] X 方向缺一篇 source 笔记（从 .raw/wechat/YYYY-MM-DD_xxxx 整理）
- [ ] Y 群组 synthesis 缺最新一篇（YYYY-MM）

---

**维护规则**（[[note-generation-rules.md|note-generation rules]] 第 5 条）：

- entity / concept / question **不**单独成页 → 在此聚合
- 关键词索引只列出现 ≥ 2 篇的关键词
- 主题群组每组 3+ 篇，少于 3 篇直接列在某篇 `related:` 即可
