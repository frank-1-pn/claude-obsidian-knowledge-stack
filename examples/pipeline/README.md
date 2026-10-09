# 合成管线调研验收材料

这是专门为角色与工作流验收创建的虚构资料，不是真实药物、公司、病种或智慧芽数据。只用于测试 brainstorming、计划、执行和来源核验，不支持真实研发/投资决策。

问题故意包含三种容易误读的情况：同一资产的别名/重复记录、历史最高阶段与当前停研状态、目标之外的记录。CSV 中每条记录保留来源 ID、来源日期、资产 ID 和实体字段。来源说明文件记录完整合成数据生成规则。

`asset_updates.csv` 是追加更新，不能静默覆盖旧记录。按截止日期选择最新记录；同一日冲突需报告待核查。原始记录仍保持不变。验收比较 `highest_phase` 与 `dev_status` 的语义，不把有过 Phase 1 的停研资产说成当前正在一期。

WorkBuddy 先澄清用途/范围和采用哪种状态口径，再写计划、生成资产表与来源矩阵，最后检查每条结果都能定位到这两份输入。

`acceptance-cases.json` 给出这两份固定输入在 2026-09-15、2026-10-09、2026-10-11 的预期值和输入 hash，只用于独立核对。处理脚本仍需真实读取 CSV，不得把此文件直接当作查询结果。

日期改变会产生合理的历史结果：9/15 的 DEMO-002 当前为 phase_1；10/09 为 discontinued，但历史最高仍为 phase_1；10/11 纳入 R007 后，DEMO-003 当前与历史最高均为 preclinical。不要让旧的 discovery 覆盖较新的高阶段，也不要把不符合另一个截点固定答案的结果称为“误判”。这三个案例验证合成材料的口径，不证明真实企业管线事实。

`process_pipeline.py` 是真实 WorkBuddy 正式任务生成、修复后经独立审查的示例处理器，不是智慧芽生产检索器。它实际读取两份 CSV，按资产/截点合并、取当前状态、按明确阶段序取历史最高，并保留来源记录。最新同日状态矛盾会输出待核查（当前状态为空、退出 3），未知阶段明确拒绝，不凭遍历顺序选定答案。

先让 WorkBuddy 形成 brief、将计划写入实际文件并读回，再执行这个已审核实现；不用让朋友从零再生成同样的处理器。从工作区根目录运行，输出目录必须先建立且选择本任务的新路径：

```powershell
.venv/Scripts/python.exe examples/pipeline/process_pipeline.py --repo-root . --verify-hashes --cutoff 2026-10-09 --target DemoTarget-A --json-out validation/my-pipeline/result.json
```

固定 fixture 断言通过返回 0、不匹配返回 1，输入 hash 不符返回 2，阶段错误或同日未决冲突返回 3。未配置固定断言的参数只打印实际处理结果，返回 0 不代表已有对应真值验证；用 `acceptance-cases.json` 与真实输出独立核对。阶段序仅覆盖本样例的 discovery、preclinical、phase_1；真实业务需另定义来源、字段和范围。

分享仓库对已封存输入、脚本和演示证据关闭 Git 文本换行转换，避免 Windows `core.autocrlf` 改变输入 hash 或破坏 PPT/JSON 的来源链。
