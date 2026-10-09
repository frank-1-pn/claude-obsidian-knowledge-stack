# WorkBuddy 实际产物只读验收审核

审核日期：2026-10-09。审查对象为独立研发助手测试工作区的 `validation/` 产物及对应公开合成输入。报告只用相对路径和产物 hash，不复制工作区绝对路径、账号信息或私有任务标识。

本审核没有运行管线/科学业务脚本、重做 PPT、开启 Office、修改受测工作区或操作 Git，也没有读取私有宿主会话目录。宿主任务与工具事件的真实来源由主集成人核对，本报告负责审核已经落盘的代码、数据与产物。

最终修订结论：科学分析与 PPT 的数字/谱系、单篇知识库入库文件，以及补正后的 `pipeline-approved` 与 `vault-query.md` 均已只读核对。正式脚本修正最高阶段错序与同日矛盾状态处理；重跑 10/09 默认结果与 10/11 边界结果对应实际 CSV，冲突保持待核查而不输出确定状态。查询引用真正入库的 note/raw，补正明确区分首次检索与后续 raw JSON 补读，限制表述准确。旧轮次仍只计预演，不能据旧报告提升为四阶段通过。主集成人已反馈核对了正式计划 Write→Read→Execute 的真实顺序、首次查询先读笔记后交叉核对以及 12 项 wiki/raw 前后 hash；补正任务的工具事件/退出结果仍以主集成人的最终读回为准，本报告不独自宣布整个目标完成。

## 管线：真实处理输入，首次轮次只计预演

`validation/pipeline/process_pipeline.py` 用 `csv.DictReader` 实际读取 `examples/pipeline/assets.csv` 与 `asset_updates.csv`，记录文件/行号，执行精确靶点过滤、截止日过滤、按 `asset_id` 分组、最新记录状态选择与审计项生成。`pipeline-result.json` 的 assets 来自 `process(records, cutoff, target)`，没有把 expected 字典直接写成资产输出。因此代码机制支持“实际读取与处理”，不是一段预置答案的简单复写。

默认 `2026-10-09 / DemoTarget-A` 的资产表与来源矩阵可回到七条输入行：DEMO-001 合并 R001/R002，DEMO-002 当前停研并单列历史一期，DEMO-003 保留 R004 的 discovery，未来 R007 不回填，非目标靶点 R005 排除。该默认口径的三项资产与公开合成输入一致。

计划文件包含明确方法、范围、来源 hash 与验收标准，但主集成人已经确认首次脚本执行发生在计划落盘之前。文件存在或日级执行账本不能倒置真实执行顺序；`evidence-review.md` 自述 complete 不能补齐该缺口。应保留为预演，在计划实际获准后用新的输出目录执行，并由主集成人核对批准、执行与验证的真实顺序。

### 预演轮发现的问题与范围

1. **最高阶段会被旧阶段覆盖。** `process()` 先令 `highest_phase=current['highest_phase']`，又遍历所有历史行，用任何不同于 current 的值覆盖它，既没有阶段排序，也没有来源冲突决策。现有输入包含直接的反例：当截止日允许 R007（2026-10-11）进入时，DEMO-003 当前记录是 preclinical，旧 R004 的 discovery 却会覆盖其最高阶段。此为代码与现有输入的静态推演，本审核未执行该业务反例。新的宿主任务应按明确阶段顺序计算窗口内最高阶段，或按获准规则使用最新来源的最高阶段字段并保留差异；须验证升期后不会退回 discovery。
2. **同日真实冲突未覆盖。** 代码写 `same_day_conflict=true` 并保留各状态的冲突列表，但按行号挑一个 `current_status`。计划原文要求“并列呈现并标记，不静默取其一”；已有审计与 flag 意味着并非完全隐藏冲突，但“当前状态”字段在正式有冲突时仍应说明候选/临时选择/待核查的语义。当前 fixture 只有同日同状态别名，未覆盖真实冲突，不能把这组默认结果泛化为该场景已经验收。
3. **参数对照不等于 RED→GREEN 回归证明。** 代码的 PASS/FAIL 始终对照固定 `2026-10-09 / DemoTarget-A` 真值。改为早截止日时，DEMO-002 在当时仍处于 phase_1，是正确的历史查询结果，不能称“误判”；改为 DemoTarget-B 时只剩 DEMO-004 也是正确筛选。它们不匹配默认真值导致 FAIL，可以说明结果随参数变化，不能证明错误行为被修复，更不能证明科学事实。实际验收应对每套参数使用各自预期结果，区分查询正确性与默认 fixture 断言。

以上不改变默认三项资产已经可核对的事实，也不允许将预演提升为完整四阶段通过。

### 正式轮复核：最高阶段修复与参数口径已收敛

已读取 `validation/pipeline-approved/` 的计划、实际脚本、默认 JSON、10/11 边界 JSON、资产表、来源矩阵与审查报告，没有调用其中的业务函数。

- 脚本仍用实际 CSV 读取/筛选/分组产生 assets。`PHASE_ORDER` 明确定义本 fixture 的 `discovery < preclinical < phase_1`；表外值经 `phase_rank()` 拒绝，停研只属于状态。highest_phase 从窗口内 ranked 的最大阶段取得，并带支持记录/日期，不再被较低旧阶段覆盖。
- `pipeline-result.json` 的实际 `cutoff=2026-10-09`：DEMO-001 为 preclinical/preclinical，DEMO-002 为 discontinued/phase_1，DEMO-003 为 discovery/discovery；R005 被排除、R007 未回填、别名合并与来源行匹配。
- `boundary-2026-10-11.json` 的实际 `cutoff=2026-10-11`：DEMO-003 的 current/highest_phase 均为 preclinical，支持记录 R007。默认与边界 JSON 都写 `acceptance_result=PASS`；二者记录的三个 input hash 均与当前原始物一致。
- `ACCEPTANCE` 已按截点/靶点分别匹配对应 expected，未列入映射的参数只报告敏感性结果，不对照 10/09 默认答案误报失败。较早截止日的 phase_1 被正确说明为当时的历史结果。
- 计划在首次写入时先列 T2–T5 pending，并要求 Read 读回后再写脚本；最终计划追加了执行账本。本审核不从最终 mtime 或报告自述单独推断计划读回，实际事件顺序仍由主集成人核对。

正式轮核心结果和代码修复可核对，当前没有发现这两个已落盘参数案例的业务数值错误。进一步补正已将 RUN D 说明为源码中自有 expected 的断言，并把旧预演对照分开写为 child exit=1 / wrapper exit=0；原误差来自管道 grep 的 shell 返回值，不再把它冒充子脚本退出码。

### 最后补正：同日矛盾待核查与退出链路

最终脚本 SHA-256 为 `cd6269b5e76a0c6ba775f3033016f8dc54c03728b52de50ab9be2e9151936106`。最新日期同一资产有不同 `dev_status` 时，脚本列出冲突状态、记录 ID、来源与行号，令 current 字段为 null、`current_status_resolved=false`，保留最高阶段与历史信息，拒绝把任何一行说成确定当前状态。一致的同日别名仍合并，不误报为矛盾。

审核期间曾看到局部 `unresolved=[]` 与 audit 冲突列表分离的接线问题；最终源码已改为 `unresolved = audit['unresolved_conflicts']`，append、打印、JSON acceptance_result 与 main exit 判定共用同一列表。源码的冲突分支输出 `UNRESOLVED_CONFLICT`、`acceptance_result="unresolved"` 并返回 3，默认/边界无冲突分支仍按各自 expected 验收。

最新版 evidence-review 记录内存复制 fixture 的冲突断言与临时副本 CLI 端到端 child exit=3；默认、10/11 边界、较早日期与 Target-B 重跑 child exit=0，未知阶段分支继续拒绝。审核者读取了这些记录与代码，并确认重新落盘的默认/边界 JSON 都无 unresolved、各资产 `current_status_resolved=true`、结果 PASS、输入 hash 仍匹配。真实 CLI/内存测试事件由主集成人核对，审核者没有运行它们。

这一范围涵盖已列明的合成默认案例、升期边界、同日矛盾/一致重复及当前未知阶段拒绝逻辑；不扩大为真实商业数据库、所有阶段分类、所有来源优先级或真实管线科学结论。建议分享包携带最终被审核的处理脚本与使用说明，使朋友复刻已验收的行为，而不仅靠提示让另一个模型重新生成处理器。

## 科学分析：数值与限制一致

读取 `validation/science/preclinical-analysis.json` 及 `preclinical-review.md`，并比对实际 fixture 内容与 SHA-256。JSON 声明 synthetic-preclinical-demo，运行版本为 Python 3.12.12、NumPy 2.3.3、SciPy 1.16.2；两个输入 hash 与当前 CSV 一致。

| 核对项 | 实际产物 | 审核结论 |
|---|---|---|
| 三组样本/均值 | 每组 8；507.5 / 460 / 313.75 mm³ | 与 CSV 和此前独立标量复算一致 |
| low 差值/CI/Holm P | −47.5；[−80.88515, −14.11485]；0.00864726543 | 双侧 Welch；未校正逐比较 CI 与 Holm P 分开 |
| high 差值/CI/Holm P | −193.75；[−225.69478, −161.80522]；9.68918631×10⁻⁹ | 与当前 JSON 和独立复算一致 |
| PK01 AUC_last / AUC_inf_obs | 0.79118856634 / 0.80561551675 mg·h/L | 线性上升/对数下降积分，观测末点外推 |
| 三个 PK profile 半衰期 | 均为 4 h | 人工指数末段解析真值，不是实测模型验证 |
| PK01 CL/F 与 V/F | 约 0.15516 L/h 与 0.89540 L | 口服表观参数，F 不可辨识 |
| PK findings | exit_code=0，findings=[] | 只表示工具覆盖范围内未提出发现 |

报告保留了独立性仅为合成设计假设、Shapiro 不证明正态/独立、终点下降不是 TGI、单点体重不构成毒理/NOAEL、分离队列不能建立个体暴露反应、显著性不支持真实化合物等限制。未发现把虚拟数据写成真实研发证据的数字或结论。

报告称 13 项测试与 snapshot 校验通过。该执行声明需要主集成人在真实宿主工具记录中核对；本审核未重跑这些测试。关于 20% AUC 外推的说法，固定上游工具确有 `--max-extrap` 默认 20.0 的警示参数；宜解释为本工具的可配置筛查设置，不直接提升为真实项目的方法有效性证明。

## PPT：来自本次 JSON，原生证据与渲染可核对

已读取实际 PPTX ZIP/OOXML、构建收据、输入副本、渲染收据，并查看已有五张 PowerPoint 渲染 PNG；没有启动 Office 或重新生成文件。

- 分析 JSON SHA-256：`c5fc6732386bd79be3febebecc2afa290bc3e69db62e64d092f728e25f857035`。
- `presentation/sources/analysis.json` 与科学分析 JSON 逐字节相同；build receipt 的 analysis hash 一致。
- PPTX SHA-256：`d03ca7ad21e8cfad3e278125ba91f3ba46d752c19457f913897d73cd2439a993`，与构建/渲染收据一致。
- 包中实际有 5 页、1 张原生 Chart、2 张原生 Table；Chart 数值缓存为 `[507.5, 460.0, 313.75]`；5 页讲者备注均含当前分析 hash。
- 渲染收据标明 Microsoft PowerPoint COM、5 页与当前 deck hash；五页 PNG 已逐页检查，图表、统计值、PK 数字与单位可读，未见裁切或重叠。
- build receipt 的 `workbuddy_runtime_verified=false` 只表示本地构建器不自行确认宿主，不能据此抹掉或替代主集成人另行核对的真实 WorkBuddy 工具链证据。

一处文档路径需校正：`validation/presentation-build-log.md` 将 postflight 报告写作 `validation/presentation.report.json`，实际文件为 `validation/presentation/validation/preclinical-demo.report.json`。这不影响已有 deck，但复刻者照日志定位会落到不存在的路径。

## 知识库：单篇闭环文件与新查询均已可读

本节只读核对 `.raw/.manifest.json`、`wiki/sources/science/` 的唯一源笔记、graph/index/sources-index/overview/log/hot/latest 与 `validation/vault-ingest.md`、lint 报告，没有写共享状态或操作锁。

- 两份 raw 归档与 `validation/science/` 的复核正文/分析 JSON **逐字节相同**。raw 正文 SHA-256 为 `0b59077d437bd196cfdbe202de37c1160e9712028f46e4d09aac3b757c89c7bc`，JSON 为上述 `c5fc6732…`；manifest 的两条 hash 均与实际 raw 相符。
- `wiki/sources/science/` 只有一篇《合成临床前终点与 PK 分析复核（终点 Welch-Holm + 上游 NCA）》。两个原始物归为同一分析报告来源集，没有拆成概念子页。笔记包含检索摘要、主题 tags、数值表与科学边界、两个 raw_path，以及 v1 provenance。
- `model: unrecorded` 如实披露未获得宿主模型 ID；当前 `wiki/meta/provenance.md` 明确允许未知时采用该值。`derived: false` 按同文件定义表示普通整理、不是事后回溯，不能误解为“没有 AI 整理”。来源没有伪造模型名。
- graph、总索引、来源索引、overview、log、hot 和 latest 均有本次笔记入口。graph 如实记录 raw Markdown 与 JSON 是同一来源集，并说明空库尚无其他来源笔记，未制造跨笔记关系。
- log 记录触发、实际原料、输出、内容、关联与验证；hot/latest 均显示 1 篇来源笔记。`related=[]` 与 lint 的 source-source orphan=1 对这个首次单篇空库不构成应伪造关系的理由；已有索引/graph 入口仍实际可见。
- lint 报告的 YAML、摘要、死链、graph、日志与 raw_path 缺口均为 0。宿主报告声称实际执行 YAML 解析、refresh-latest 和 lint；本审核读取已有报告，没有重跑生成器或 lint。
- 文件修改时间支持 raw 先于 note，再到 graph/log/latest/lint，manifest 最后落盘。**mtime 只是顺序旁证**，不能替代同一 item 的真实 started/done checkpoint、manifest: done 和锁释放事件。主集成人应以已授权宿主事件/锁收据核对；不依赖本审核读取私有会话。

这一状态支持“本次指定来源已形成一篇可回查的笔记与入口”。最新的 `validation/vault-query.md` 已补正为真实顺序：首次先读 hot/index，再读具体 science 笔记，来源索引在笔记之后读取；首次回查 raw 正文与 validation 分析 JSON 作交叉核对，**未**读 raw 分析 JSON。后续审核补正才完整补读 raw 分析 JSON，并将该动作另列，未把它倒填成首次检索。

查询中的双侧 Welch、两预设比较、Holm、未校正 CI、8–24 h 手动终末窗、linear-up/log-down、虚拟 4 h 半衰期、单点终点/体重和分离队列限制，与实际 note/raw 一致。引用的文件确实存在，不是指向预置 examples。报告把 validation 分析 JSON 说明为额外交叉核对，而主要答案来源在知识库；不应仅根据报告自述认定真实检索事件，主集成人还需核对宿主读取记录。

原 Q1 的无关“20.”排版残留已移除；Q3 已明确“合成 PK 终末浓度点来自指数真值”，不再和药效肿瘤终点混淆。最终查询报告 SHA-256 为 `41b4044ee901fe525e5236e0eb9e04a720e855efe175eefaacc3d30c8ef3fecb`。报告引用值与实际 note/raw 一致，raw 与 manifest hash 复查仍匹配。首次查询只读性由主集成人反馈的 12 项 wiki/raw 前后 hash 验证；补正报告另记录其 wiki hash 未变，最终整个只读范围仍由主集成人核对，审核者不读私有会话也不修改受测文件。

## 最终验收尚需证据

1. 已看到正式管线最高阶段和同日矛盾修复、重新落盘的默认/边界结果、更正后的 child/wrapper 记录与新查询补正；主集成人核对最后补正的真实计划读回、冲突 CLI 测试与实际退出结果，保留预演与正式轮次区别。
2. 主集成人读取实际宿主任务与工具事件，确认角色发现、科学分析、PPT 生成/渲染、正式管线与新知识库查询的执行来源；本审核的文件检查不能替代这一步。
3. 已看到单篇 source/raw、provenance、graph/index/log/hot/latest 和最后写入的 manifest 文件；仍需主集成人核对真实 checkpoint/锁释放、校验退出结果和新查询前后 12 项 wiki/raw hash。
4. 固定源文件和受测项目不由审核者修改；智慧芽与邮件继续保持设计状态，不把离线合成成果说成连接已启用。

本报告属于当前产物审核快照；最终通过结论由唯一集成人基于修正后的真实执行记录与完整要求作出。
