# 用 WorkBuddy 复刻药企研发总监助手

将分享仓库地址交给 WorkBuddy 后，发送下面的开场指令。先安装可复用系统，再以合成资料验收；智慧芽和邮件现场连接不在这一步启用。

> 帮我在本机搭建这个仓库中的药企研发总监助手。先读取 `agent.md`、`AGENTS.md`、`docs/rd-assistant-implementation-plan.md` 与 `setup/10-rd-director-workbuddy.md`。将仓库作为源码，创建仓库外独立工作区；使用 `scripts/bootstrap_rd_assistant.py` 安装 10 个 Obsidian 技能、精选科学技能、研发工作流与 PPT 适配入口。检查 Obsidian，未安装则用仓库官方安装 helper 安装。使用隔离 Python 环境与固定版本依赖，不修改我的全局模型、MCP、连接器或权限。不读取原有私有会话。依赖或安装失败就报告实际错误和 partial；完成后在这个新工作区创建真正的 WorkBuddy 任务，按计划执行合成临床前数据分析、PPT 生成/渲染、笔记入库/查询，并逐项展示真实任务记录与产物，不把脚本 smoke 当作 WorkBuddy 验收。

## 1. 取得源码与选用 Python

克隆或下载分享仓库，放在源码目录。新助手工作区必须在源码目录外，例如 `D:/Work/pharma-director-assistant`。已有文件全部保留；发现同路径不同 hash 会停止并列出冲突，不覆盖。

当前离线科学演示固定 NumPy/SciPy 版本，推荐 Python 3.12 或 3.13。如果默认 Python 较新且依赖没有 wheel，选择已安装的兼容解释器；不要自行修改依赖 pin 来冒充通过。在 Windows 可先运行 `py -0p` 查看安装路径，将实际解释器路径传给 `--python`。 如果本机没有兼容解释器，先从 [Python 官方 Windows 下载页](https://www.python.org/downloads/windows/) 选择 Python 3.13 的正式版、对应本机架构的安装程序，安装到当前用户；完成后核对解释器实际路径和 `--version`。不要默认下载页面最醒目的较新大版本，也不要以 Microsoft Store 的占位命令当作已安装解释器。macOS/Linux 同样选择官方或系统包管理器提供的 3.12/3.13；本次仅实际验证 Windows 路径。

```powershell
python scripts/bootstrap_rd_assistant.py --workspace D:/Work/pharma-director-assistant --install-deps --python C:/Path/To/Python313/python.exe
```

默认会检查/安装 Obsidian，依赖装在新工作区 `.venv` 中。不会初始化 Git、commit、push、启用智慧芽/邮件 MCP 或写全局配置。无 Git 时笔记仅允许单会话串行，不具备跨会话并发锁。

如果明确希望启用本地 Git 与跨会话笔记锁，显式增加 `--git`。这个参数只建立本地仓库，不授权提交或推送。

```powershell
python scripts/bootstrap_rd_assistant.py --workspace D:/Work/pharma-director-assistant --install-deps --python C:/Path/To/Python313/python.exe --git
```

无桌面脚本检查可显式使用 `--skip-obsidian`。此选项不会被解释为 Obsidian 桌面已验收。没有 `--install-deps` 时只准备文件，依赖不齐返回 exit 2 / partial，后续重新运行相同命令补齐。

## 2. 在 WorkBuddy 选用项目

通过 WorkBuddy 的项目入口选择新助手工作区。确认工作目录准确，根目录 `CODEBUDDY.md` 指向 `agent.md`、知识库 `AGENTS.md` 和当前实施计划。

首次打开带 `.codebuddy` 的文件夹，本机 WorkBuddy 5.7.6 会询问 **Choose how to open**。先确认这是自己刚生成、已核对来源的工作区，再选择 **Open normally**，看到该工作区 trusted 的提示后新建任务。Restricted mode 不自动加载项目配置，不能把磁盘上有 39 个技能当作正常发现。信任选择只针对这个工作区，不需要调整全局权限；在受限状态启动的旧任务应保留记录，改用正常打开后新建的任务验收。

项目 `.codebuddy/skills/` 包含原有 10 个 Obsidian 技能、24 个精选 scientific 技能、`pharma-research-workflow`、`pharma-presentation`，以及 `mail-triage`、`daily-email-brief`、`urgent-email-alert` 三个未接入邮件模板，共 39 个。邮件模板可按习惯修改，但安装不启用邮箱、监控、调度或发送。适配入口链接到工作区 `integrations/` 的完整方法；原文 vendor、scripts、templates、references 和许可一起复制，相对引用可回读。科学技能安装不等于 24 项逐项执行验收。

```powershell
python D:/Work/pharma-director-assistant/scripts/check_rd_assistant.py --workspace D:/Work/pharma-director-assistant
```

`prepared` 仅表示资产和指定离线依赖准备通过；报告始终保留 `workbuddy_verified: false`。WorkBuddy 登录和真实调用状态要在下一步证明。

## 3. 真正执行并核对结果

在新项目新建 WorkBuddy 任务，先确认问题与受众，写计划，再用合成资料执行。按当前实施计划逐项验收，不输入企业未批准的真实数据。

- 工作流：实际读取 Superpowers 原文与适配 skill，先完成范围/brainstorming、计划，执行后核对证据。
- 科学：用 `.venv` 的 Python 执行 `integrations/scientific/analyze_preclinical.py --output <本任务输出目录>/preclinical-analysis.json`，独立核查药效、实验单位、统计与 PK 数值；产物明确标“合成示例”。
- PPT：完整读 `integrations/presentation/SKILL.md`，按其真实命令生成 PPTX 并渲染。检查页数、文字、数字、图表与可编辑对象。
- 知识库：用本工作区的规则与 skills，材料先 `.raw/` 归档，写一篇摘要/标签/provenance 完整的笔记，完成关系、索引、日志、latest、验证与 manifest，再通过查询技能引用回读。测试不得写进原有个人知识库。
- 同一真实任务的 GUI/history 要能看到输入、工具调用、结果与产物；待审批、模型失败或中途退出保持 partial。不能只凭进程、probe、`isProcessing: false` 或脚本 exit 0 宣称跑通。

智慧芽与邮件在介绍/现场计划中保留设计状态。通讯连接器由已有 WorkBuddy 提供，这个包不会施工通用通讯 bridge。

## 4. 后续维护

再次 bootstrap 会预检静态程序/技能/vendor 的 hash，不同内容停止。`wiki/`、`.raw/` 和 `_templates/` 的已有用户内容原样保留，完成入库后也可重复补缺，不改笔记正文或回退 manifest。遇到静态冲突可保留原工作区并新建一个目录验证新版本，再明确选择迁移范围。直接依赖与本次解析的传递依赖都锁定版本，安装和检查不自行放宽 pin。

只在用户明确说“同步”时，唯一集成人对自己的验证通过路径提交并推送。项目初始化不授权分享私人笔记、邮箱内容或凭据。

官方机制见 [WorkBuddy 项目配置](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project) 与 [技能安装](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。这个流程使用项目级配置，不修改全局用户环境。
