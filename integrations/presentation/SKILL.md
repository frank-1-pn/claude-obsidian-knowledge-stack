---
name: pharma-presentation
description: 将已核实的研发材料或临床前分析呈现为可编辑PPT，使用固定版本PPT-master与逐页渲染验收。演示模式从科学分析JSON生成图表和表格，不编造管线或研究结论。
---

# 研发材料呈现

先确定本仓库根目录并使用绝对路径。上游实际入口在 `<仓库>/vendor/ppt-master/skills/ppt-master/SKILL.md`；它与 `workflows/`、`references/`、`scripts/`、`templates/` 原文完整保留对应的精选快照，revision 和省略清单见 `<仓库>/vendor/ppt-master/snapshot.json`。版权与 `attribution_guard.py` 检查原样保留，不得绕过。

## 日常报告

1. 先用 pharma-research-workflow 核实决策问题、输入来源、关键数字、时间与单位。
2. 阅读上游 SKILL 及其当前路由，选择普通材料生成或已有模板编辑。已授权的任务遵循用户范围，不额外扩大到模型推荐、连接器施工或付费 API。
3. 需要品牌/版式时使用用户提供模板；没有模板时采用清楚的科研报告布局。采购/自动更新或新增数据外传渠道仍需对应授权。
4. 来源字段与输入统计产物是事实依据，逐项区分真实资料、推断和合成示例。以讲者备注保存支持来源，重大限制放在可见页。
5. 保持关键数据表格/图表原生可编辑；运行上游 final SVG quality gate、导出与 PPT package delivery check。检查实际PPT渲染后才报告呈现完成。

WorkBuddy 连接器取得文章或飞书材料后，只需将获准材料提供为本地 Markdown/文件；本包不传微信抓取器或飞书 bridge，也不自动配置外部图片/模型 API。上游可选网页转换脚本已从快照排除。若其他可选路线需要快照省略的图标、音效、图片或网页工具，应明确说明并选择现有可用资料，禁止声称完整上游资源均已安装。

## 可复刻临床前演示

安装最小演示依赖（在 bootstrap 创建的项目隔离环境中）：

```powershell
python -m pip install -r integrations/presentation/requirements-demo.txt
```

先让科学分析步骤产生 `preclinical-analysis.json`。再在仓库根目录执行：

```powershell
python integrations/presentation/build_preclinical_demo.py --analysis <preclinical-analysis.json> --output <全新演示目录>
```

此命令接受 `integrations/scientific/output.schema.json` 定义的分析 JSON；只接受合成临床前示例。输出 5 页 PPTX、来源输入副本、SVG 源与预览、逐页来源备注、设计规范和运行收据。图表读取三组均值，统计表读取每个预设比较，PK 表读取所有最多 4 个演示 profile。profile 超出布局支持范围时停止并保留 partial，需要重新设计完整展示，不能静默丢行。

验证数字与原生结构：

```powershell
python integrations/presentation/verify_preclinical_deck.py --analysis <preclinical-analysis.json> --project <演示目录>
```

Windows 已安装 Microsoft PowerPoint 时可实际渲染：

```powershell
powershell -NoProfile -File integrations/presentation/render_powerpoint.ps1 -Pptx <演示目录>/preclinical-demo.pptx -OutputDirectory <全新渲染目录>
```

渲染脚本仅关闭自己打开的文稿；不关闭已有 PowerPoint 实例。没有 PowerPoint 或 COM 失败时如实标记“PPT已生成，真实PPT渲染待验收”，不得以SVG预览替代PPT渲染完成。可由获准安装的LibreOffice或用户PowerPoint补验收，这些软件本包不自动安装。

## 科学表达边界

- 合成数据显著性不代表真实化合物有效。
- 终点体积下降比例不等于纵向 TGI。
- 单点体重描述不构成毒理或 NOAEL 评估。
- 分离的 PK 与药效模拟队列不能建立个体暴露反应关系。
- 口服 CL/F 和 V/F 无法辨识生物利用度 F。
- 本地构建、PowerPoint 渲染、WorkBuddy 真正执行和业务验收分别提供证据。

最小演示不需要图片 API、邮箱、智慧芽、网络检索或音频服务。常规新材料可以扩展上游路线，但须检查对应依赖与资源。本包只锁定并验收列出的演示范围；可选 PDF 转换依赖 PyMuPDF 的 AGPL 或商业许可，未捆绑其二进制依赖。
