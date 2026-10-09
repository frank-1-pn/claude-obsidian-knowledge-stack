# 变更记录

## 2026-10-09 — 核心 WorkBuddy 合成链验收与复刻收敛

- 触发：用户要求真实 WorkBuddy 跑通后同步，并追加允许多任务并行、包括宿主测试。
- 实际宿主：WorkBuddy 5.7.6；角色/39skills/13项固定依赖初始化，管线与查询并行，另开独立管线测试任务。用户的私人 vault、邮箱和凭据未进入分享包。
- 科学与呈现：实际统计与上游 NCA、13项测试；本轮 JSON→真实5页PPT、1原生Chart/2原生Table/5份notes与PowerPoint渲染，通过数字与逐页核对。实际样例和哈希复制到 integrations/presentation/examples/workbuddy-run/。
- 知识库：本体持锁串行 raw-first，单来源笔记、graph/index/log/hot/latest、真实校验、manifest-last及锁释放；新任务从hot/index/笔记/raw查回并引用，12个库内文件前后hash未变。未知source模型按现行词表诚实写unrecorded，首次空库不编造related。
- 管线：保留首次先算后补计划的预演；正式轮计划Write→Read→代码→实际执行。修复历史最高阶段被旧低阶段覆盖、同日矛盾当前状态择一、固定断言与参数敏感性混淆、子进程/wrapper退出码混用。独立WorkBuddy快照实际8次CLI运行，三截点9/9资产行吻合，冲突/未知阶段child3；代码版本未漂移。
- 复刻：已审核处理器收入examples/pipeline，实际读CSV而非复写答案；新增三截点独立预期。对vendor、脚本、封存输入和PPT/JSON证据保留字节；Windows core.autocrlf=true临时Git checkout-index测试11文件0字节差异，保护hash与来源链。
- 文档：角色、实施、现场智慧芽/邮件设计、WorkBuddy正常打开/信任步骤、上手与HTML最终状态收敛。各项来源、许可、真实事件和限制见docs/rd-assistant-validation.md及结构化回执。
- 发布：本条记录核心验收完成；目标仓库同步和远端读回单独记录，不将资产prepared当本体验收。
- 原始物/ingest manifest：分享源码维护不适用；实际测试入库只发生在独立合成vault。

## 2026-10-09 — 研发总监助手集成与阶段验收（尚未全部跑通）

- 触发：用户要求 WorkBuddy 作为运行中台，集成角色、Superpowers、精选科学技能、PPT-master 与现有 Obsidian，并在本体跑通后同步；智慧芽与邮件连接本轮仅设计。
- 输出：agent.md、CODEBUDDY.md、实施计划/当前验收记录、研发助手离线 HTML、隔离 bootstrap/checker、24 个科学技能、2 个研发适配、3 个未连接邮件模板、合成样例和固定上游快照。
- 本地验证：24 skills 的 387 个来源/许可 hash、111 个 Python AST；合成统计与实际上游 NCA，在 Python 3.12.12 固定依赖环境通过 13 项测试；PPT 实际生成 5 页并由 PowerPoint 渲染，含 1 个原生图表/2 个原生表格。本体科学/PPT 任务尚未完成。
- HTML：320/390/768/1440 自适应、目录一致、筛选/搜索/页签/键盘/复制回退/规则展开与打印状态恢复通过，离线 0 网络请求、0 浏览器错误；手机截图和打印版已检查。
- 真实 WorkBuddy：桌面 5.7.6 的角色读取与首次 bootstrap 已执行、任务完成且实际产物已读回；新工作区发现 39 skills、13 项依赖 pin 和既有 Obsidian。首次初始化早于最后审核修复，最终版本新项目与完整业务链仍待验证。
- 审核修复：BLQ 数值标记不再静默丢弃、schema 拒绝重复比较、bootstrap 检查补充许可 hash、Obsidian helper 的 RuntimeError 进入 partial。bootstrap 6 项测试通过；没有把异常、mock 或本地 smoke 充作真实宿主闭环。
- 当前阻塞：系统暂时不能提供 WorkBuddy 前台输入窗口，已请求恢复；未启用旁路调试/权限入口。剩余真实调研、科学/PPT、入库与新任务查询见当前验收记录，未提前推送。
- 来源与连接：保留用户邮件方案原件与完整许可，不分享私人 vault、凭据、账号或原始会话；不建设微信/飞书 bridge，智慧芽与邮箱保持未连接设计状态。
- 原始物与 ingest manifest：不适用，本轮是源码/系统集成；测试笔记只在独立验证 vault 生成。

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
