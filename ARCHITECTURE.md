# 系统结构

```text
用户明确发起任务
  → WorkBuddy 现有连接器 / 本地文件 / 可用搜索工具
  → 核对完整性，先保存 .raw/<type>/ 快照
  → 一个来源对应 wiki/sources/<domain>/<title>.md
  → 唯一集成人逐篇完成 graph/index → log → hot/latest → validate
  → 最后写 .raw/.manifest.json，关闭该项
```

内容层只有 sources；人物、概念、问题留在同一原子笔记。关系集中在 wiki/meta/notes-graph.md。检索顺序为 hot → index/领域索引 → graph → 相关原子笔记，不保证全文搜索自动达到完全召回。

能委派时默认两个独立 note workers，唯一集成人写共享元数据；worker 只拥有该来源的 raw、note、附件路径。不能委派时如实改为串行执行。详情和 handoff 在生成 vault 的 AGENTS.md。

集成锁保存在 Git common directory，多个 worktree 共用。非 Git vault 无跨 session 锁保障，只能单会话串行。初始化脚本不会自行 git init。锁被占用时报告持有人和 checkpoint，不自动破锁；逐篇 manifest 最后写入。

连接器返回什么格式就归档什么格式。只返回 Markdown 时，不声称取得完整 HTML 或所有图片；保留真实源 URL、取得时间、连接器名称和缺失项。截断或抓取失败保持 partial，不能登记为完整入库。原料不覆盖，重试追加新版本，复用已核实原料避免重复笔记。

私人数据归朋友自己的 vault；分享仓库只保存系统。同步、发消息、云端发布都是单独的操作范围。
