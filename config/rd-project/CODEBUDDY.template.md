# 研发总监助手：WorkBuddy 项目入口

先完整读取工作区 `agent.md`（业务角色）、`AGENTS.md`（知识库写入）、`docs/rd-assistant-implementation-plan.md`（实施与验收）。这些文件和本项目 `.codebuddy/skills/` 一起工作；用户本次明确指令优先。

首次运行 `python scripts/check_rd_assistant.py --workspace .`。若显示 partial，逐项修复，不把安装文件存在当作真实 WorkBuddy 验收。依赖使用工作区 `.venv`；Windows 的 Python 为 `.venv/Scripts/python.exe`，其他平台为 `.venv/bin/python`。

复杂研究调用 `pharma-research-workflow`，先澄清和 brainstorming、计划、执行，再证据核验；科研按相应 scientific skill、PPT 调用 `pharma-presentation`。原文 vendor 保持固定 revision、许可和目录；适配技能不得冒充原作者的科研流程。

笔记入口为 `wiki`，写入前读 `wiki/hot.md`，一份来源一篇笔记、raw-first、摘要标签与可回查 provenance。有 Git 时使用已有跨会话锁 helper；没有 Git 时遵循 `AGENTS.md` 的单会话串行降级，不能并行写共享状态。默认不初始化 Git；用户显式选择 `--git` 才创建本地仓库，没有提交或推送权限。

通讯与内容读取复用 WorkBuddy 已有连接器。智慧芽和邮件仅为设计，不启用 MCP、不读取凭据、不新建 bridge、不声称正在监控。技能内提及的可选付费服务不代表已购买或获授权。

每日资讯入口是 `integrations/daily-briefing/README.md` 与 `task-prompt.md`。先了解每天关注的主题、关键词、来源、排除条件、时间时区、条数与渠道，按偏好生成单次预演；明确启用后才配置实际调度。每条提供 AI 总结、单独标记的分析和原文链接；历史样例不作为今日新闻。当前模板未启用订阅或推送，不自动创建定时任务或读取收件人。

邮件管理入口是 `integrations/email/README.md` 和 `setup-checklist.md`，三个邮件 skill 分别解释事实/待办/期限、已有每日邮件简报和已有紧急提醒。连接步骤以用户原方案为准：只读 IMAP 与后台先完成，再联调只读 MCP 与本人通知。后台单一调度，私人邮件不进入公开每日资讯，源邮箱不修改。

精选 scientific 原文中提及的 `scientific-schematics`、`parallel-web`、`paper-lookup`、`venue-templates` 等可选扩展不包含在本安装中。没有实际安装/授权时跳过对应分支，说明缺少什么，或使用已批准的普通绘图/检索工具；不能声称调用了不存在的 skill。当前固定依赖只覆盖离线合成分析与 PPT 演示，其他领域技能按各自依赖和数据条件另行验证。

以真实任务工具记录、实际产物和同一任务的历史读回核实完成。仓库脚本检查只能证明本地准备或分析，不证明 WorkBuddy 已跑通。
