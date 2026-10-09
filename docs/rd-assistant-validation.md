# 研发总监助手：验收记录

日期：2026-10-09。**核心合成链已在真实 WorkBuddy 中通过。** Git 同步以对应远端 revision 和发布回执为准；智慧芽和邮件按用户要求保持现场设计状态。

源码已定向提交、推送到 main 并 fetch/逐文件读回，见 [发布回执](rd-publish-validation.json)。封存输入、实际分析 JSON/PPT 与处理器的远端 bytes/hash 均匹配。

## 真实宿主与实测范围

本机 WorkBuddy 桌面 5.7.6，运行时任务标识 `deepseek-v4.1-flash`。工作在独立公开/合成测试项目，未导入私人知识库、邮箱、凭据或真实企业数据。源码实施采用多个 agent；真实宿主的管线与查询任务并行，另开独立 WorkBuddy 任务测试管线快照。

| 用例 | 实际操作与读回 | 验收结论 |
|---|---|---|
| WB-01 角色与技能 | 本体 Read 项目入口、角色、规则和本项目技能入口；正常打开受信任项目后实际调用 `pharma-research-workflow` | 角色、方法和 39 个安装入口一致；安装不等于 24 项专业软件逐项执行 |
| 初始化 | 本体实际 bootstrap 新空工作区，安装固定依赖、查到既有 Obsidian，checker prepared/0 errors；6 项 bootstrap 和 13 项科学测试有实际输出 | 39 skills、13 个依赖 pin；隔离环境和本地 Git 锁结构通过 |
| WB-02 调研 | 首轮提供两种策略并提问；明确回答后正式轮先写计划、Read 读回，再生成处理器和执行 CSV；修复阶段排序、同日冲突和退出码描述 | 三资产及来源行可回查；旧轮保留为预演；正式计划顺序、结果与限制核对通过 |
| WB-02 独立测试 | 新 WorkBuddy 任务复制同 hash 快照，真实执行 8 个 subprocess，用独立预期核对三截点、hash 与两个负向 CLI 场景 | 9/9 资产行吻合；普通运行 child 0，冲突和未知阶段 child 3；前后源代码 hash 相同 |
| WB-03 科学 | 实际阅读项目统计/PK/批判性思考技能、运行固定上游 NCA 与统计代码、13 项测试，读回 JSON/限制 | 每组 8 个虚拟动物；数值、假设、未校正 CI/校正 p、PK 积分与限制独立复核一致 |
| WB-04 PPT | 从本轮实际 JSON 调用固定 PPT-master，生成/验证 PPTX 并由 Microsoft PowerPoint 渲染 | 5 页、1 个原生图表、2 个原生表格、5 份来源 hash notes；全部渲染逐页检查 |
| WB-05 入库 | 无子 agent 时明确串行降级；真实锁、expect/checkpoint；raw-first、一篇原子笔记、graph/index/log/hot/latest、校验、manifest 最后登记与锁释放 | 原始物 bytes/hash 一致，摘要 144 个汉字、tags/raw_path/provenance 完整；0 YAML/死链/缺 graph，首次空库不伪造关系 |
| WB-06 查回 | 新任务按 hot/index 定位实际笔记，读取笔记/raw；validation 仅在定位后交叉核对；补读 raw JSON 的事件与首次顺序分别记录 | 统计、PK 和限制回答引用正确；查询和补正前后 12 个 wiki/raw 文件完全不变 |

本地资产 checker 的 `workbuddy_verified:false` 保留其“仅资产就绪”口径。本体完成由独立的 [结构化宿主回执](rd-workbuddy-validation.json) 证明。

## 可公开复查的产物

- [真实 WorkBuddy 生成的合成 JSON/PPT/五页渲染](../integrations/presentation/examples/workbuddy-run/README.md)。分析 SHA256：`c5fc6732386bd79be3febebecc2afa290bc3e69db62e64d092f728e25f857035`；PPT SHA256：`d03ca7ad21e8cfad3e278125ba91f3ba46d752c19457f913897d73cd2439a993`。
- [实际验收后收录的管线处理器](../examples/pipeline/process_pipeline.py)，SHA256：`cd6269b5e76a0c6ba775f3033016f8dc54c03728b52de50ab9be2e9151936106`。数据与 CLI 用法见同目录 README，明确仅是合成 fixture 示例。
- [科学源快照与完整许可](../integrations/scientific/upstream-lock.json)：24 skills，387 个文件 hash，111 个 Python AST 校验；其余 API/软件未逐项执行。
- [独立审核](../research/workbuddy-acceptance-review.md)、[浏览器回执](rd-html-validation.json)、[Git 字节保持回执](rd-git-byte-validation.json)。临时 Git 仓库使用 `core.autocrlf=true`，11 个源码/输入/JSON/PPT 样本 checkout 后逐字节相同，测试不涉及提交或远端发布。

## 发现问题后的处理

首次管线任务先计算后补计划，且较晚截点的旧低阶段会覆盖新高阶段。该轮只算预演，保持原样；正式轮重建计划并读回后执行，按明确阶段序处理，同日矛盾保持未决并退出 3。独立测试确认边界和真实 CLI 链路。

查询报告早先把实际读取顺序和 raw JSON 读取写错，补正时实际补读，并分别记录首次与补读事件。独立测试报告另有一句把 10/09 的未来记录写成 R006/R007；原始 JSON 实际只排除 R007，9/15 才排除两者。集成人按 JSON 核对，不将文字差错作为新重跑或数据错误。本公开记录使用已核实的正确口径。

## 复刻与适用边界

Windows/Python 3.12.12 已实测；新空路径复制、依赖导入与重复执行无冲突。Obsidian 本机已有安装，实际检查复用；缺失安装、异常和其它平台分支由隔离测试覆盖，朋友机器上的实际安装与渲染环境以其运行结果为准。

HTML 在 320/390/768/1440 离线浏览器通过：24 科学卡与目录一致、10 Obsidian skills、筛选/搜索/页签/键盘/复制回退/规则展开/打印状态恢复；0 网络请求、0 页面/控制台错误，截图与打印版已检查。

初始空库只有一篇来源，related 为空与单篇 source orphan 是正确边界；source/model 未能由宿主取得时按 provenance 词表写 `unrecorded`，不编造模型。真实企业研究、24 项专业软件全量依赖、付费服务与账号、智慧芽、真实邮箱均没有被这些合成样例证明上线。

内部任务 ID、账号界面、原始工具历史和测试 vault 内容保存在不入 Git 的本地证据中；分享包只含源码、模板、完整许可、合成输入与脱敏回执。

## 每日资讯与邮件介绍增补（2026-10-09）

本次追加展示用户 2026-10-07 每日资讯页的三条历史新闻，并补齐关注偏好、单次预演、自动汇总推送的启用与验收模板；邮件部分依据用户原方案，补齐连接流程、七个只读工具和三个邮件 skill。原方案文件与用户指定来源逐字节一致。

本次验证针对 HTML、历史节选一致性、模板、技能 YAML/引用及新工作区复制，详见 [增补验证记录](daily-briefing-validation.json)。未实际创建定时任务、连接邮箱或发消息，原 WB-01 至 WB-06 不覆盖新增资讯调度或真实邮件服务。旧字节保持与发布回执对应原 revision，新增文件版本以本次 Git 记录及 HTML 回执为准。
