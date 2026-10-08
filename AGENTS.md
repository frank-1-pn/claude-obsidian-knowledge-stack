# 分享仓库维护规则

这是笔记系统的可复用源码与模板，不是私人笔记库。维护时只改规则、skills、脚本、setup、config、vault 模板和 CHANGELOG.md。

- 新 vault 使用 config/vault-agents.template.md 作为唯一规则入口；当前本文件只约束分享仓库维护。
- 不导入现有 wiki 正文、raw、附件、聊天、凭据、本机配置或 Obsidian workspace。
- 不重新加入微信抓取器和飞书 bridge；WorkBuddy 的现有连接器承担内容读取。
- 改代码前检查 Git 状态并使用独立分支或 worktree。提交仅包含自己的明确路径。
- 用户明确要求“同步”才允许定向 commit/push；不自动提交或推送。
- 系统/规则变更记入 CHANGELOG.md，不为模板维护伪造 ingest manifest。
- 验证使用临时 vault，不把测试笔记写入分享仓库。
