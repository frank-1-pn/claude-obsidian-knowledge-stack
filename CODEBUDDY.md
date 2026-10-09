# WorkBuddy 开场：复刻药企研发总监助手

这是可分享的系统源码，不是用户的私人知识库。先读取根 `AGENTS.md`（分享仓库维护范围）、`agent.md`（业务角色）、`docs/rd-assistant-implementation-plan.md` 和 `setup/10-rd-director-workbuddy.md`。执行以当前用户授权为准，不把文档示例当作授权邮件/专业数据库或对外发送的凭据。

当用户要求“复刻/安装这套助手”时：

1. 核对 Python、Git、网络与文件访问，检查 Obsidian；没有时使用 `scripts/ensure_obsidian.py` 的官方安装流程。复用已有安装，保留既有文件。
2. 在分享仓库外选择用户指定的新工作区；未指定可提出相邻 `rd-assistant-workspace` 路径，只有会影响已有资料的冲突再询问。默认不修改全局 WorkBuddy 设置。
3. 按上手说明实际执行 `scripts/bootstrap_rd_assistant.py --workspace <新工作区> --install-deps --python <兼容的Python>`。跨会话笔记写入需要时由用户明确选择 `--git`；仅建本地仓库，不 commit/push。
4. 逐项处理真实检查结果。固定 vendor 文件、许可与依赖版本保持一致；缺失/冲突报告 partial，不覆盖用户内容，不通过更改版本凑成功。
5. 在 WorkBuddy 选用新工作区，读取它的 CODEBUDDY.md、agent.md 和 AGENTS.md，从 `.codebuddy/skills/` 按任务发现技能。运行复制后的检查器，再执行上手说明中的真实验收任务。
6. 智慧芽 MCP、邮箱及后台通知只保留设计，直到现场账户、企业数据范围与权限实际确认。本包不搭通用微信/飞书/通讯桥接，不自动启动邮件监控。

普通使用时，复杂调研先澄清→计划→执行→验证；科学按选定技能与获准材料进行；PPT 使用真实分析结果并渲染检查；日常收藏/查询使用 Obsidian 10 skills 的三层流程。不要把安装状态、演示测试或这里写的验收目标说成当前用户机器已经成功。

用户希望每日获取资讯时，读取 `integrations/daily-briefing/README.md` 和 `task-prompt.md`，先了解每天关注的信息，再填写偏好、生成一次预演。启用定时任务需要用户确认时间、时区、渠道和实际接收者；只使用当前可用、已授权的调度与 WorkBuddy 连接器。没有配置时如实说明尚未订阅，历史示例不能作为今日新闻。

邮件管理与连接按 `integrations/email/README.md` 和 `setup-checklist.md` 路由，三个已安装的邮件 skill 分别处理研判、每日邮件简报和紧急提醒解释。真实 IMAP/MCP/本人通知三种连接按源方案分阶段实施，邮件后台保持唯一调度，不与每日公开资讯混用数据。
