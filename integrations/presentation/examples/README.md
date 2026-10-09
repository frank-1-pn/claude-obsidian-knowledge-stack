# 临床前合成演示

`analysis.json` 来自本仓库科学演示的真实计算输出。数字描述虚拟数据，不能用于真实药效、毒理、临床或企业管线判断。

`preclinical-demo.pptx` 使用固定版本的实际 PPT-master 生成器导出。五页包括合成数据范围、三组终点均值图、两个预设比较统计表、三个虚拟 PK profile 参数表和解释限制。PPTX 内有一张原生图表、两张原生表格及五份来源/方法讲者备注。

`powerpoint-render/` 为 Microsoft PowerPoint 实际渲染的五页 PNG，已逐页检查。`local-validation.json` 记录源/产物哈希与本地验证范围。此示例的本地收据不代表 WorkBuddy 本体验收；主流程需要在 WorkBuddy 内重新生成新产物并记录真正工具调用。

从同一输入重建（目标目录必须不存在）：

```powershell
python integrations/presentation/build_preclinical_demo.py --analysis integrations/presentation/examples/analysis.json --output <全新演示目录>
python integrations/presentation/verify_preclinical_deck.py --analysis integrations/presentation/examples/analysis.json --project <演示目录>
```

演示数据关系和布局固定在科学演示的 schema 范围；实际研发材料应走适配 skill 的常规路由，保留完整真实来源、单位和限制。不要把这个示例的数据套到真实管线。
