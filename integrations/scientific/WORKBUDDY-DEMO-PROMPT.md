# 交给 WorkBuddy 的实际分析验收任务

请在这个仓库的工作副本里完成一次实际执行，不要只解释方法或编造结果。

1. 先读本项目 `AGENTS.md` 和研发助手入口、`integrations/scientific/README.md`、`fixtures/README.md`，再按需读取已安装的 `statistical-analysis`、`pkpd-modeling`、`scientific-critical-thinking` 技能。声明该任务只使用本仓库合成数据。
2. 先核对环境与 `integrations/scientific/verify_snapshot.py`。用独立 Python 环境按 `requirements-demo.txt` 安装依赖；不要全量安装24技能的依赖。已存在可用环境时复用。
3. 实际运行 `analyze_preclinical.py --output .local/rd-demo/preclinical-analysis.json`；运行 `test_preclinical.py` 测试。保存真实命令、退出码与产物文件。JSON中必须包含真实runtime版本、输入SHA-256和固定上游revision。
4. 读取生成的 JSON 和 schema，检查两组样本数、均值差、区间、Holm p 值、PK积分约定、终末窗、半衰期及完整findings。若 `pk.exit_code=1` 或 findings 非空，报告问题，不能称PK验证通过。
5. 用简短中文写 `preclinical-review.md` 到 `.local/rd-demo/`，包含输入、分析计划、真实结果、局限和下一步。说明“终点相对下降不是TGI”“模拟数据没有真实药效证据”“体重不证明毒理安全”“两队列不能声称暴露反应”。需要 PPT 时交给本系统 PPT 生成器，传入真实 JSON，不手填数字。
6. 保留可复查产物与测试结果，向用户报告实际执行范围。此步骤不调用智慧芽、邮箱、通讯连接器、付费模型或真实企业资料，也不自行提交或上传Git。
