# 变更记录

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
