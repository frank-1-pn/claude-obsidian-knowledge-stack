# Vault 结构

```text
<your-vault>/
  AGENTS.md                         唯一规则入口
  CLAUDE.md                         兼容引用
  skills/                           10 个能力入口
  scripts/                          可运行本地 helper
  .raw/.manifest.json               已逐篇验收的来源状态
  .raw/<type>/                      不可覆盖原料快照
  wiki/sources/<domain>/<title>.md   一份来源一篇笔记
  wiki/sources/sessions/             保存会话的单文件笔记
  wiki/meta/notes-graph.md           跨笔记关系
  wiki/meta/provenance.md            来源字段与词表
  wiki/index.md                     总入口
  wiki/最新笔记.md                   生成的时间倒序入口
  wiki/hot.md                       近期状态
  wiki/log.md                       最新在顶部的日志
  wiki/overview.md                  概览
  _attachments/<note-slug>/          实际引用附件
  _templates/                       源与综述模板
```

不预建 entities/concepts/questions 层，不复制个人领域分类或已有笔记。目录按朋友实际资料逐步建立。
