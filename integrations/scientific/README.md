# 临床前研发科学技能包

这里精选 24 个真实上游技能，保留每个技能的 `SKILL.md`、参考材料、脚本与模板。来源是 [K-Dense Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills)，固定 revision `92ace75ac21efe19a620434e0ca4e356081fe807`，采集日期 2026-10-09。逐项用途、依赖和固定来源链接见 [catalog.json](catalog.json)；逐文件 SHA-256 和 Git blob 见 [upstream-lock.json](upstream-lock.json)。本包没有复制整个上游仓库、模型权重、数据库资料或患者数据。

## 研发总监能怎么使用

先定义研发问题、实验单位、主要终点、证据范围和交付物，再选对应技能。涉及管线战略时，由 Superpowers 工作流先澄清与计划；科学技能负责专业方法和实际计算；验证阶段审查输入、计算、证据和结论。工具预测、统计关联和综述假设需要各自的实验证据，不能相互冒充。

| 任务 | 精选技能 | 本包实际提供的范围 |
| --- | --- | --- |
| 公开靶点和管线证据 | `database-lookup`、`depmap` | PubChem、ChEMBL、UniProt 等数据库方法；癌症依赖、CRISPR gene effect、PRISM 药敏。商业管线数据另由智慧芽 MCP 对接。 |
| 化合物性质、药化与 ADMET | `rdkit`、`medchem`、`pytdc` | 分子结构、描述符、规则警示、TDC 数据集与基准评估。ADMET 模型预测不等于实测安全性。 |
| PK/PD 与临床前安全证据 | `pkpd-modeling`、`relsa-severity-assessment`、`analytical-method-validation` | NCA/PKPD研究方法、动物福利严重度、分析方法验证材料。GLP毒理评估、病理结论和NOAEL认定属于专业审查与任务组合；本包没有一个自动完成它们的专用技能。 |
| 实验设计与统计 | `experimental-design`、`statistical-power`、`statistical-analysis`、`statsmodels`、`uncertainty-and-units` | 对照、随机化、区组、样本量、检验、回归、混合模型、单位与测量不确定度。 |
| 生信与机制 | `biopython`、`bulk-rnaseq`、`pydeseq2`、`scanpy`、`pathway-enrichment` | 序列、bulk计数准备、差异表达、单细胞探索及通路富集。注意生物学重复、背景基因集和多重比较。 |
| 精选通用科研能力 | `literature-review`、`citation-management`、`scientific-critical-thinking`、`scientific-writing`、`exploratory-data-analysis`、`scientific-visualization` | 可复现检索、引文核对、证据审阅、报告写作、数据检查和科学图表。PPT交付由本系统的 PPT Master 集成承担。 |

## 安装与发现

系统 bootstrap 应把 `vendor/scientific-agent-skills/skills/<name>/` 的完整目录安装到 WorkBuddy 项目的 `.codebuddy/skills/<name>/`。单个技能内部的相对 `references/`、`scripts/` 和 `assets/` 路径须原样保留。完整许可证和来源锁也要随项目保留。不要仅复制 `SKILL.md`。

这 24 项是可发现的流程文档和工具入口，不表示 24 个专业软件都安装、运行或通过验收。各技能的依赖彼此可能冲突，必须按具体任务建立独立环境；不要把 RDKit、PyTDC、Scanpy 和全部统计栈装入同一个环境。许多数据库要求网络、注册或授权；可选的 Parallel/OpenRouter 步骤和商业服务不会自动启用，也不是下面演示的依赖。

## 可复刻的离线临床前演示

演示接受两份公开合成 CSV：24 个独立虚拟动物的单个肿瘤体积终点与体重变化；另一个独立队列的 3 条浓度时间序列。无患者信息、真实实验记录、付费 API 或外部数据下载。依赖安装时需要访问公开 Python 包源，分析运行全程离线。

推荐 Python 3.12 及以上，用项目根目录运行：

```powershell
python -m venv .local/scientific-demo-venv
& .local/scientific-demo-venv/Scripts/python.exe -m pip install -r integrations/scientific/requirements-demo.txt
& .local/scientific-demo-venv/Scripts/python.exe integrations/scientific/analyze_preclinical.py --output .local/rd-demo/preclinical-analysis.json
& .local/scientific-demo-venv/Scripts/python.exe -B -m unittest discover -s integrations/scientific -p test_preclinical.py -v
python integrations/scientific/verify_snapshot.py
```

macOS/Linux 可将环境内解释器路径换为 `.local/scientific-demo-venv/bin/python`。不要手工编造示例 JSON。AI 运行脚本后读取真实产物，按 [output.schema.json](output.schema.json) 检验，再根据值写报告或交给 PPT 生成器。WorkBuddy 可直接使用 [WORKBUDDY-DEMO-PROMPT.md](WORKBUDDY-DEMO-PROMPT.md)。

分析内容：

- 两个预设独立均值比较：low–vehicle、high–vehicle；双侧 Welch t 检验，Holm 控制这两个比较的家族错误率。
- 每组样本量、均值、标准差、差值和 95% 点对点置信区间。置信区间未做同步多重比较调整，必须与 Holm p 值分开解释。
- Shapiro 仅作描述性诊断。检验不拒绝正态不能证明正态或独立；不按诊断 p 值临时更换检验。
- 单点体重变化是描述性的耐受性上下文。体重未达到示例 10% 下降标记不能证明安全；这不是人道终点阈值。
- 真实调用固定上游 `pkpd-modeling/scripts/nca.py`，选择线性上升／对数下降积分、8–24h 手动终末相、观测末点 AUC 外推；保存完整诊断、notes 和 findings。
- 所有缺失、非有限数值、重复动物、重复采血时间或 BLQ 字符拒绝处理，不静默删除或插补。真实 BLQ、重复测量、笼位或批次依赖需单独制定分析计划。

该固定 fixture 的数值检查点：vehicle 均值 507.5 mm³，low 460 mm³，high 313.75 mm³；high–vehicle 差值 −193.75 mm³，点对点 95% 区间约 [−225.69, −161.81]；high 的终点相对下降约 38.18%，Holm p≈9.69×10⁻⁹。这个“下降”不是纵向肿瘤生长抑制率 TGI。三条人为设计的 PK 终末相半衰期恰为 4h；PK01 的 AUC(0–last)≈0.79119 mg·h/L，观测末点 AUC(0–∞)≈0.80562 mg·h/L。两队列不能用于动物个体暴露–反应建模。

生成 JSON 的 `pk.exit_code=1` 表示上游存在 findings，AI 必须展示这些发现并停止把 PK 结果称为“验证通过”；`exit_code=0` 也仅表示脚本未提出其覆盖范围内的发现。分析脚本返回 0 说明 JSON 成功生成并通过 schema，不能代替科学审查。

## 本次验证与边界

已在隔离环境 Python 3.14.2、NumPy 2.3.3、SciPy 1.16.2、jsonschema 4.25.1 运行完整合成演示；本次复审也在 Python 3.12.12 的复刻依赖环境通过 13 项测试。测试覆盖解析真值半衰期、独立标量 Welch 公式、AUC 逐段解析积分、Holm 已知输入、多种错误输入、schema 和快照完整性。381 份上游文件及 6 份补充完整许可文本均有哈希校验，111 个上游 Python 文件做 AST 语法检查（数量以 verifier 实际输出为准）。

这些检查证明离线示例的数值路径和固定字节；未执行全部 24 个领域工作流、远程 API、GPU训练、真实研究或注册申报。不将上游“validated”等自述作为本系统的验收结果。WorkBuddy 的项目发现和完整任务运行以系统实施记录为准。

## 许可与归属

原上游集合 [LICENSE.md](../../vendor/scientific-agent-skills/LICENSE.md) 是 MIT，版权所有者 K-Dense Inc.。上游明确声明各技能许可证不同；本包逐项保留其 `license` 字段。RDKit/Scanpy/Statsmodels 为 BSD-3-Clause，medchem 为 Apache-2.0，DepMap 为 CC-BY-4.0，Biopython 为 Biopython License Agreement，其他所选项声明 MIT。相关完整文本归档在 [licenses](../../vendor/scientific-agent-skills/licenses/)，来源固定提交和哈希见 lock。附加软件和数据集仍以其各自许可为准，本包不捆绑它们。

本包科学技能来自 K-Dense，原技能文件未改写。采用其研究方法与NCA实现；本仓库另写集成演示、fixture、catalog 和验证代码，分别放在 `integrations/scientific/`，未将它们伪装成上游原文件。上游引用元数据原样保存为 [CITATION.cff](../../vendor/scientific-agent-skills/CITATION.cff)：Scientific Agent Skills, [DOI 10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。
