# 格式与溯源

完整来源字段见 skills/wiki/references/frontmatter.md；核实词表见 vault/skeletons/provenance.template.md。

源笔记 H1 后的 `[!abstract]` 说明具体主题、别名、问题、机制和适用场景。正文事实限于来源；AI 解释用 `[!info]`、`[!example]` 或 `[!tip]` 标明“AI 补充／非原文”，来源外事实用 `[!external]` 并附依据。

YAML 字符串用合法引号或 block scalar；保存后解析验证。列表逐项换行，callout 段落和列表间留空的 `>` 行。链接用 `[[笔记名]]`，附件用 `![[note-slug/file.png]]`。

Raw 类型：wechat、pdf（含 Office 原件）、screenshots、github、webfetch、rss、transcripts、social。快照名用 YYYY-MM-DD_<slug>，slug 为最多 10 个小写英文连字符词。仅归档真实获得的格式，不伪造 HTML。
