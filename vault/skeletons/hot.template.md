---
type: meta
title: Hot cache
updated: 2026-MM-DD
tags:
  - meta
  - hot
---

> [!abstract] 这是什么
> "正在做什么 / 当前关注 / 这周 / 这个月"。
> 约 500 字。每周 / 每次大背景切换时重写。
> 新 session 启动时 Claude 第一份读的文件。

---

<!-- AUTO-DIGEST-START (weekly-digest.py 维护，勿手改本块) -->
### 🤖 本周快照（auto，2026-MM-DD）
- 本周入库 N 篇：<[[笔记 A]] / [[笔记 B]] ...>
- <一句话本周主题摘要>
- 最近 log：<log.md 顶部那条一句话>
<!-- AUTO-DIGEST-END -->

> 上面这一块由 `weekly-digest.py`（一个按周跑一次的小脚本，扫 `wiki/log.md` 最近
> 条目 + 本周新建笔记）自动重写，是唯一允许被脚本而不是 Claude 直接改的区域——手改
> 会在下次自动刷新时被覆盖。区域之外的内容仍由 Claude 按下面的维护规则手工维护。

## 当前焦点

> [!info] 这周
> 1-2 句话讲这周在做什么。具体到 issue / 项目 / 任务级别。

> [!info] 这个月
> 1 段话讲本月的主线（项目目标 / 团队 ask / 个人成长方向）。

## 进行中的笔记 / 实验

- [[<note>]] —— 还差什么、卡在哪
- [[<note>]] —— 等 X 数据 / 等 Y 反馈

## 最近 5 条 ingest

按时间倒序，最近读 + 写的：
- [[<note>]] —— 一句话讲读完的收获
- [[<note>]]
- [[<note>]]
- [[<note>]]
- [[<note>]]

## 待消化（队列）

- URL / PDF / 链接（按优先级）：
  - 高：[xxx](https://...)
  - 中：[xxx](https://...)
  - 低：[xxx](https://...)

## 待问 / 待澄清

- [ ] 问 X 关于 Y 的事
- [ ] 找 Z 数据源

## 关键决策（最近做的）

- 2026-MM-DD：决定 X 走 A 方案，不走 B（理由：…）
- 2026-MM-DD：放弃 Y 实验（理由：…）

---

**维护规则**：

- 字数 ~ 500（看一眼能扫完，不含 AUTO-DIGEST 块）
- 这里只放**当前 / 即将相关**的；老的归 `wiki/log.md`
- 每周 / 每次切大背景时**全文重写**，不要 append
- `<!-- AUTO-DIGEST-START -->` … `<!-- AUTO-DIGEST-END -->` 之间的内容由
  `weekly-digest.py` 脚本维护，Claude 和用户都不手改这一块——需要改摘要逻辑改脚本，
  不要直接编辑生成结果
