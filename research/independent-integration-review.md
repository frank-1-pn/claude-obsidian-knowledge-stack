# 研发助手集成独立审核

审核日期：2026-10-09。本次只读审核主集成的角色、实施计划、bootstrap/check，以及科学 worker 的分析代码、schema、fixture、来源锁和许可范围。审核者此前负责工作流/PPT，故本报告不把对自己 PPT 实现的检查称为独立代码审核。未访问真实 WorkBuddy 会话、账号、邮箱或智慧芽；未安装依赖、修改实现、启动 Office 或运行会写文件的测试。

结论：当前源码保持了用户要求的研发总监助手范围，没有将产品角色缩成合成示例。审核发现的安装异常、附加许可校验、BLQ 标记与重复比较契约问题已在审核期间由各路径负责人修正；复读源码确认修正存在。最终真实 WorkBuddy 验收、负测试执行和发布仍由主集成人完成，本报告不证明这些运行结果。

## 产品角色与任务范围

`agent.md` 明确研究/竞争情报、临床前科学支持、规划、PPT、Obsidian 与只读邮件接口六类职责；`CODEBUDDY.template.md` 显式引导宿主读取角色、知识库规则和实施计划。正常研究先明确决策问题、范围和来源，再计划、执行和逐项核实；软件 TDD 没有被强加给科研事实。

`setup/10-rd-director-workbuddy.md` 保留正常使用和合成验收的区别。智慧芽与邮件均标为现场设计，通讯和普通内容读取复用 WorkBuddy 连接器，没有用安装技能来宣称连接已启用。安装 payload 的只读内存检查得到 39 个技能、39 个唯一名称，角色与入口存在，自动启用 MCP 清单为空。

实施计划 P0–P6 与 WB-01–WB-06 仍要求角色发现、真实工作流、科学分析、实际 PPT/渲染、逐篇入库闭环以及新任务检索。未把脚本 prepared、文件数量或 demo 输出单独定义成完整完成条件。这些保留条件应在最终同步前逐项核实。

## 审核发现及当前收敛

| 发现 | 原行为与影响 | 当前源码 | 最终验证建议 |
|---|---|---|---|
| 安装异常没有统一进入 partial | `ensure_obsidian()` 会因官方安装元数据、安装后程序发现等失败抛 `RuntimeError`；bootstrap 原异常捕获没有该类型，部分复刻失败只能得到 traceback | `scripts/bootstrap_rd_assistant.py` 已把 `RuntimeError` 加入 main 捕获，保留 partial 报告 | 模拟 helper 的 RuntimeError，核对 exit 2、实际原因及已复制文件保留 |
| 六份附加许可未纳入初始化 source hash 检查 | 原 bootstrap 只验证 scientific lock 的 `files`；附加许可虽复制，但 source 损坏时可被新 registry 接受为基线 | bootstrap 现验证 `files + additional_license_texts`，与 scientific verifier 范围一致 | 对任一附加许可作受控变体，确认 source preflight 拒绝；正式包保持原字节 |
| 数值浓度配合 `blq=1` 可以被上游丢弃 | wrapper 原只拒绝浓度字段中的 BLQ 字符；上游读取显式 `blq` 列，并在 missing 规则下跳过该观测，违反本演示的完整数值输入契约 | `integrations/scientific/analyze_preclinical.py` 已拒绝不为空/0/false/no 的 BLQ 标记，负测试已加入 | 跑新增数值浓度加 BLQ flag 的负测试；确认不生成“完整分析”结论 |
| 两条 comparisons 可以同名 | 原 schema 限定数量为 2、名字在 low/high enum 内，却可接受两条 low 并缺少 high | `output.schema.json` 已用 contains/minContains/maxContains 要求 low/high 各一条 | 受控重复 contrast 应不通过 schema；生成器的正常两条比较仍通过 |

这是当前源码收敛检查，不是上述新增测试已执行的声明。主集成人应读取每项实际测试结果。

## 科学数字的独立复算

本次用 fixture CSV 和独立标量公式只读复算，没有调用 `analyze_efficacy()` 或 `analyze_pk()` 取得这些数字。均值、样本方差、Welch 标准误/自由度与逐段 PK 积分从 CSV 重新计算；Student t 分布仅用于分布函数与分位数。结果与实现及演示 JSON 一致。

| 项目 | 只读复算结果 | 解释范围 |
|---|---|---|
| 对照/低剂量/高剂量终点均值 | 507.5 / 460 / 313.75 mm³ | 每组 8 个虚拟动物，单个终点 |
| low–vehicle 差值与未校正 95% CI | −47.5 mm³；[−80.88515, −14.11485] | 双侧独立 Welch 比较 |
| low 原始 P | 0.00864726543 | 对两个预设比较做 Holm 后仍为此值 |
| high–vehicle 差值与未校正 95% CI | −193.75 mm³；[−225.69478, −161.80522] | 逐比较区间，未做同时区间校正 |
| high 原始 P / Holm P | 4.84459315×10⁻⁹ / 9.68918631×10⁻⁹ | Holm 最小 P 乘以 2，另一 P 保持单调 |
| PK01 AUC_last | 0.79118856634 mg·h/L | 上升段线性积分，正值下降段指数解析积分 |
| PK01 AUC_inf_obs | 0.80561551675 mg·h/L | 观测末点浓度外推；不是预测末点版本 |
| PK01 半衰期 | 4 h | 8/12/24 h 人工指数末段给定的解析真值 |
| PK01 CL/F | 0.15516086446 L/h | 0.125 mg ÷ AUC_inf_obs；口服表观参数 |

代码和说明区分了未校正逐比较 CI 与 Holm P。Shapiro 只是描述性诊断，没有用其不拒绝结果证明正态/独立，也没有临时切换检验。终点相对下降不是纵向 TGI，单点体重不能构成 NOAEL 或毒理评价。PK 和终点来自分离的合成队列，不支持个体暴露反应。口服 CL/F、V/F 不辨识 F。没有发现这些固定 fixture 数字的计算错误。

## 复刻路径、发现与许可

- bootstrap 从脚本本身定位源码，工具从安装后原始目录定位仓库；适配 thin SKILL 相对链接返回工作区 `integrations/`，保留 vendor 布局，搬迁没有写死作者机器路径。
- 10 个 Obsidian 技能、24 个 scientific 技能、2 个研发适配及 3 个邮件设计模板共 39 个。科学原目录保留 references/scripts/templates；安装数量不等于全部科学 API 或软件逐项执行。
- mutable 的 `wiki/`、`.raw/`、`_templates/` 保留已有内容；静态源码 hash 冲突先预检并停止。重新安装不是覆盖私人笔记或回退 manifest 的授权。
- `CODEBUDDY.md` 显式加载 `agent.md` 与 `AGENTS.md`，不依赖宿主自动发现后两者。真实宿主是否读取正确入口仍须 WB-01 的实际记录证明。
- 无 Git 时使用单会话串行降级；有显式 `--git` 时才初始化本地仓库。该模式不是跨会话互斥证据，也不授予提交/推送权限。
- 上游集合 MIT 与逐技能的 BSD-3-Clause、Apache-2.0、CC-BY-4.0、Biopython 等声明分别保留；科学完整许可文本有独立来源/hash。本包不能据根目录 MIT 推断所有依赖、数据和内容均为 MIT。
- `highest_phase` 与 `dev_status` 在管线设计和 fixture 中分开，停研资产保留历史最高阶段；未来日期更新不能回填过去截点。DEMO-001 别名去重、DEMO-002 停研、DEMO-003 截止日过滤、DEMO-004 靶点排除均有明确来源行和验收真值。

## 仍需最终验收或可改善处

1. 真实 WorkBuddy 分阶段任务、PPT 实际渲染与新任务的笔记查询应以当前版本的 fresh workspace 证明；源码审阅、payload 或本地数学复算不能替代这些证据。
2. 默认管线任务可以使用获准公开来源；合成表只用于方法验收。智慧芽未接入时不得把 public/demo 结果描述为其返回。真正来源还需保留适应症、地区、资产更新时间和字段口径，不能把全球最高阶段投射为某个地区的当前阶段。
3. 复刻说明目前要求可用 Python 3.12/3.13。建议补充“没有兼容解释器时”的发现/取得步骤，避免朋友只能收到一个不存在的 `--python` 示例路径。此项不影响已具备兼容 Python 的本次运行。
4. 科学 schema 的 PK rows 仍是宽泛 object，analysis_plan 多数字段只要求存在；schema 通过不能证明统计方法、关键 PK 字段或数学关系。当前生成代码和独立数值复核覆盖固定 fixture。以后接收其他工具产生的 JSON 时应定义对应的字段/方法契约，并按原数据核实。
5. Windows 依赖锁、安装与运行的实证不要扩写为 macOS/Linux/现场企业环境均已通过。各技能还需要网络、特定数据库授权或隔离软件环境时，保留准确的未实测范围。

审核者只写本报告，未修改其他路径。最终工作流与发布的收敛由唯一集成人决定。
