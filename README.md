# claude-obsidian-knowledge-stack

## 药企研发总监助手

本仓库提供 WorkBuddy 可复刻的研发总监助手：角色职责见 [agent.md](agent.md)，开场入口见 [CODEBUDDY.md](CODEBUDDY.md)，实施与真实宿主验收见 [实施计划](docs/rd-assistant-implementation-plan.md)。

组合包含 Superpowers 的澄清/计划/执行/验证工作方法、精选 24 个生物医药与通用科学技能、PPT-master 的实际演示文稿生成，以及下方 Obsidian 10 skills。智慧芽管线 MCP 与私人邮件后台仅提供现场接入设计，通讯复用 WorkBuddy 自带连接器。

先看可离线打开的 [WorkBuddy 研究与知识助手 HTML 介绍](docs/rd-director-assistant.html)，复刻步骤见 [WorkBuddy 研发助手上手](setup/10-rd-director-workbuddy.md)，证据与实测范围见 [验收记录](docs/rd-assistant-validation.md)。2026-10-09 已在真实 WorkBuddy 完成角色/初始化、澄清与正式管线处理、科学分析、PPT 生成/渲染、笔记入库与新任务查回；管线与查询并行，并另开任务独立运行 8 项 CLI 验收。

已验收的合成 [管线处理器与数据](examples/pipeline/README.md) 和 [实际 PPT/渲染](integrations/presentation/examples/workbuddy-run/README.md) 一起分享。24 个科学技能文件已安装并固定来源；离线样例实测统计/PK，不把安装当作全部专业软件或商业 API 都已执行。智慧芽与邮箱只提供现场设计，尚未连接。

新增 [每日资讯](integrations/daily-briefing/README.md)：先定制用户每天关注的主题、关键词、来源、时间与渠道，再配置每日自动汇总推送。用户可直接看 AI 总结与分析，也可点击原文链接阅读源新闻。两份 HTML 都展示了用户现有 2026-10-07 资讯页的部分历史内容；偏好配置、任务提示与简报模板会一起复制到新研发工作区。目前没有开启朋友的定时任务或实际推送，原有 WorkBuddy 验收不覆盖这一新增调度。

[邮件管理与连接](integrations/email/README.md) 按用户提供的原方案补充：只读 IMAP、MailParser、持久后台、七个只读 MCP 查询工具及本人通知渠道的分工与[现场连接步骤](integrations/email/setup-checklist.md)。三个对应技能为 [邮件研判](integrations/email/skills/mail-triage/SKILL.md)、[每日邮件简报](integrations/email/skills/daily-email-brief/SKILL.md)、[紧急提醒解释](integrations/email/skills/urgent-email-alert/SKILL.md)。正文可追溯到原邮件证据，管理事项不等于修改源邮箱；公开资讯与私人邮件的来源、数据和调度各自配置。

---

把当前使用的 Obsidian 笔记流程分享给 WorkBuddy 用户：一份来源一篇笔记，先归档原料，再整理、关联、验收；后续按摘要、索引和原文检索。

本仓库提供 **10 个 skills、项目规则、空白 vault 模板和可运行脚本**。不含个人笔记、原始资料、附件、聊天记录、密钥或本机配置。

想先了解系统，可下载并用浏览器打开 [HTML 图文介绍](docs/obsidian-knowledge-system.html)：三层文件架构、10 个 skills、写入规则、检索与上手流程。单文件离线可读，支持手机、技能筛选、三层示例切换和打印。GitHub 的文件页显示源码，下载原始 HTML 后打开即可。

微信文章和飞书内容由朋友在 WorkBuddy 中已有的连接器读取。本分享版不提供这两类连接器的安装、抓取器、bot、bridge 或事件订阅。阅读整理规范仍保留。

## 给朋友的开始方式

1. 下载本仓库，或 `git clone https://github.com/frank-1-pn/claude-obsidian-knowledge-stack.git`。
2. 按 [WorkBuddy 上手](setup/00-workbuddy.md) 初始化自己的空白笔记库。
3. 在 Obsidian 打开生成的文件夹，在 WorkBuddy 打开或授权访问同一个文件夹。
4. 把下面这段话发给 WorkBuddy：

```text
请先完整读取当前笔记库的 AGENTS.md 和 skills/wiki/SKILL.md，再读取 wiki/hot.md。
先运行 python scripts/ensure_obsidian.py 检查 Obsidian；没有安装就自动下载安装，完成后核对程序路径。
以后根据我的任务按需读取对应 SKILL.md。微信文章与飞书内容用我已配置的连接器读取。
整理时先保存实际取得的原料，再按一份来源一篇笔记处理，完成索引、关系、日志与检查。
如果没有子 agent 能力，请说明改为串行执行。只有我明确说“同步”才提交和推送 Git。
```

不依赖 WorkBuddy 自动加载 AGENTS.md 或识别 `/wiki`。用自然语言即可：“整理这篇文章”“从库里查一下”“保存这次讨论”“检查笔记库”。

## 保留的系统

| 能力 | 文件入口 |
|---|---|
| 架构、初始化与任务路由 | skills/wiki/SKILL.md |
| 来源入库、阅读讲解、摘要与溯源 | skills/wiki-ingest/SKILL.md |
| 有引用的只读检索 | skills/wiki-query/SKILL.md |
| 结构与链接检查 | skills/wiki-lint/SKILL.md |
| 单文件会话保存 | skills/save/SKILL.md |
| 明确发起的研究与综述 | skills/autoresearch/SKILL.md |
| Canvas、Markdown、Bases、网页清理 | skills/canvas、obsidian-markdown、obsidian-bases、defuddle |

```text
skills/                当前 10 个技能与必要参考文件
scripts/               初始化、检查、latest、lint、provenance、集成锁
config/                新 vault 的 AGENTS.md 与 Claude 兼容入口
vault/skeletons/       空白入口、元数据、源笔记与综述模板
setup/                 WorkBuddy 优先的安装与可选能力说明
ARCHITECTURE.md         数据流与协作边界
CHANGELOG.md            分享仓库变更与实际验证
```

快速初始化（路径按自己电脑替换）：

```powershell
python -m pip install -r requirements.txt
python scripts/init_vault.py --vault "D:/my-knowledge-vault"
python scripts/check_bootstrap.py --vault "D:/my-knowledge-vault"
```

`init_vault.py` 会先检查 Obsidian，缺少时从官方源下载、校验并自动安装；已安装则复用。笔记库文件只补缺失，不覆盖已有文件。Git 和 Obsidian Sync 都由朋友自行选择配置，不自动创建仓库、安装插件或同步。纯脚本环境可加 `--skip-obsidian`。分享包验证可运行 `python scripts/verify_share.py`。

脚本在临时 vault 的归档、笔记、索引、日志、manifest 和最新笔记流程见 CHANGELOG.md，可运行 `python scripts/smoke_share.py` 重现；尚未在朋友的 WorkBuddy 环境实测。

## 许可与来源

本仓库自有源码与模板使用 MIT；保留 [LICENSE](LICENSE) 和 [ATTRIBUTION.md](ATTRIBUTION.md)。项目基于 AgriciDaniel/claude-obsidian，并按本地 Note-as-atom 流程适配。

固定上游源码保留各自许可和署名：Superpowers 与 PPT-master 的 MIT，科学技能目录声明的 MIT、BSD、Apache、CC-BY 和 Biopython 等许可分别适用，见 [科学来源锁](integrations/scientific/upstream-lock.json) 与各 vendor 的 snapshot/许可。原始文章、数据、图片与真实企业材料的使用权限另行判断，不因代码开源自动获得转载授权。
