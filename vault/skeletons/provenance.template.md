---
type: meta
title: "来源溯源"
tags: [meta, provenance]
status: evergreen
---

# 来源溯源

schema 为 v1；model 写实际模型 id，未知时 unrecorded；derived 表示该块是否事后回溯，普通整理/综述不自动等于 derived: true；recorded 为实际记录日期。

verified 只记录实际做过的核实，没记录某项不等于没做过。已有含义不能悄悄修改。

| 标记 | 实际动作 |
|---|---|
| raw-archived | 已归档原料 |
| connector-read | 已使用宿主连接器读取，记录连接器和覆盖范围 |
| wechat-fetch | 实际取得微信公众号正文，不限定抓取工具 |
| web-fetch | 获取网页快照 |
| gh-api | 调用 GitHub API 核实元数据 |
| readme-full | 通读 README |
| license-full | 通读许可 |
| source-code | 阅读代码确认行为 |
| live-run | 实际运行核实 |
| live-api | 实际调用线上 API 并核对结构 |
| transcript | 实际取得字幕或转录 |
| images | 实际配图并检查 |

原作者观点、独立事实核验和 AI 理解分开标注。模板字段不能冒充已经完成的验证。
