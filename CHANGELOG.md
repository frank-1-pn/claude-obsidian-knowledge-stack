# 变更记录

## 2026-10-08 — 单文件 HTML 知识库介绍

- 触发：用户要求 HTML 版介绍，包含 10 个 skills、原料/检索笔记/分类关联三层架构与写入规则，并补充有用内容。
- 输出：docs/obsidian-knowledge-system.html；README 增加下载入口。
- 依据：当前项目规则、分享规则模板、10 个 SKILL.md、结构与笔记模板。第三层通过文件夹、索引、双链和关系元数据组织第二层的同一份笔记；不扩大原子笔记架构。
- 内容：三层职责、可点击合成示例、10 个技能的场景与输出、八步入库闭环、十项写入规则、笔记模板、检索路径、WorkBuddy/Obsidian 分工与上手提示。示例和图明确为演示，未包含私人来源、凭据或真实文章。
- 实际验证：浏览器离线检查通过，320/390/768/1440 宽度均无页面横向溢出；三层切换及键盘导航、技能分类/搜索/清空、提示词复制、规则展开和打印检查通过。10 个技能齐全，示例摘要 168 字，段落与图示已目视检查；0 远程资源请求、0 浏览器错误。打印包含全部三层与 10 个技能。
- 归档与 manifest：不适用，本次输出为分享仓库介绍页，没有新建 wiki 来源笔记。

## 2026-10-08 — 初始化前自动检查与安装 Obsidian

- 触发：用户追加要求让 AI 检查 Obsidian，未安装时自动下载安装。
- 输出：scripts/ensure_obsidian.py、scripts/test_ensure_obsidian.py、初始化器、wiki skill、规则模板及上手说明。
- 行为：已有安装复用；未安装从官方最新稳定发布下载并核对 SHA-256，再执行当前用户安装。Windows 静默安装、macOS 用户 Applications、Linux 官方 AppImage；安装后核对程序路径，失败返回非零并停止初始化。纯脚本环境可显式跳过桌面安装。
- 依据：Obsidian 官方下载/安装说明及 Microsoft WinGet 的 Obsidian 安装清单；未固定第三方镜像或版本。
- 验证：安装器的 12 项隔离/模拟测试通过，覆盖已有安装不下载、默认初始化检查、失败阻止初始化、SHA-256 不符拒绝、非官方地址拒绝、安装后复查及三种平台的安装分支；临时 vault 闭环、54 份文本文件分享扫描、wiki skill 和 Git diff 校验通过。本机只读检查找到现有 Obsidian，未安装或重装软件；朋友机器上的完整安装与桌面启动仍需实机验收。
- 原始物、ingest manifest 与笔记关系：不适用，本项为系统流程变更。

## 2026-10-08 — 同步当前笔记系统，适配 WorkBuddy

- 触发：用户要求同步到 claude-obsidian-knowledge-stack，给已有微信/飞书连接器的 WorkBuddy 朋友分享。
- 来源：当前本地规则、10 个 skills 和本地 helper 的定向源码读取；未读取或复制私人笔记正文与原始资料。
- 输出：skills/、config/vault-agents.template.md、vault/skeletons/、scripts/、README.md、ARCHITECTURE.md、setup/。
- 内容：Note-as-atom、raw-first、理解优先、检索摘要、真实 provenance、默认委派与唯一串行集成；移除旧微信抓取和飞书 bridge，使用现有连接器。
- 可移植性：latest/lint 改为相对 vault 路径；新增只补缺失的初始化和离线检查；不安装 hooks、定时任务、代理或全局设置。
- 外部补充：0；本次是系统分享，不是来源 ingest，原始物、来源关联与 ingest manifest 不适用。
- 实际验证：`python scripts/verify_share.py` 通过（52 份文本文件，0 错误）；`python scripts/smoke_share.py` 通过。临时中文路径 vault 完成初始化、重复执行不覆盖、raw/note/index/graph/log/hot/latest/manifest 闭环和 provenance 查询；注入缺 manifest、raw 篡改、死链均失败，恢复后通过；第二持有人与未完成项释放均被锁拒绝。
- Skill 校验：以 UTF-8 运行 skill-creator 的 quick_validate，10/10 通过；Git diff 空白校验通过。
- 来源范围：同步的是 2026-10-08 本地当前规则与技能文件，包含尚未提交的规则更新；个人 vault 的原有改动保持独立，未提交或推送该仓库。
- 限制：未在朋友的 WorkBuddy 运行；连接器完整性、本地文件权限和真实配图显示需在其环境验收。
