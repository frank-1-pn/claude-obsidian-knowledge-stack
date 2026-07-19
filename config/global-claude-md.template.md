# 用户全局偏好

每个新 Claude Code session 开始时会读本文件（`~/.claude/CLAUDE.md`）。如果用了 Feishu bridge，本文件还指挥启动自检。

> **这是一份模板。**用 `<>` 包起来的全是占位符，填进你自己的真实值（bot 别名、chat_id、open_id 等）。**不要把填好的版本提交到任何 git 仓库**。

> **组件关系（一句话）**：`daemon`（每 bot 一个·常驻·活过 /compact·写 ndjson）→ `Monitor`（每 session 一个·按 offset 读 ndjson）→ `binding-<pid>.json`（让 PostCompact 路由到对的 bot）。判活只认「入站 task-notification 的 task-id 匹配本 session Monitor」或「stream-ended」，**不认心跳 ok、不认 TaskList**（详见下方「判活规则」）。

---

## 已注册的飞书 bot（可选 — 用了 [feishu-claude-code-bridge](https://github.com/<github-user>/feishu-claude-code-bridge) 才有）

| 别名 | App ID | Brand | 默认 chat_id | 用户 open_id | config |
|------|--------|-------|--------------|--------------|--------|
| <Bot 主力的中文别名> | `cli_<your-app-id>` | feishu | `oc_<your-p2p-chat-id>` | `ou_<your-open-id>` | `<USER_HOME>\.lark-cli\config.json` |
| <Bot 编程项目用> | `cli_<...>` | feishu | `oc_<...>` | `ou_<...>` | profile `<profile-name>`（`--profile <name>`） |
| <Bot 财务/某项目用> | `cli_<...>` | feishu | `oc_<...>` (P2P) | `ou_<...>` | profile `<profile-name>`（`--profile <name>`）· 用于 `<project-dir>` 项目 |

新 bot 登记填这五列即可。其他路径：npm 全局 bin `<USER_HOME>\AppData\Roaming\npm`；文件下载目录 `<USER_HOME>\lark-downloads`。

## 启动自检（只在用 Feishu bridge 时有意义）

参考 [feishu-claude-code-bridge `claude-config/CLAUDE.md` §启动自检](https://github.com/<github-user>/feishu-claude-code-bridge/blob/main/claude-config/CLAUDE.md)。

简版顺序：

1. **`lark-cli` 可用**：`export PATH="$PATH:<USER_HOME_MSYS>/AppData/Roaming/npm" && lark-cli --version`
2. **列每个 bot 的 subscribe 占用情况**：`Get-CimInstance Win32_Process` 配 `*event*subscribe*` 过滤
3. **问用户要不要连**（仅当有空闲 bot 时）
4. **启 daemon + Monitor**：`ensure-bot.ps1 -Bot <bot1|...>` + `bash monitor-bot.sh <bot1|...>`
5. **心跳确认**：`lark-cli im +messages-send --chat-id <chat_id> --text "✅ ..." --as bot`
6. **写本 session 的 binding 文件**：`write-binding.ps1 -Bot <bot1|...> -MonitorTaskId <id>`（让 PostCompact 等 hook 路由对）。**注**：较新版本的 `ensure-bot.ps1`（第 4 步）已经会顺手自动写当前 PID 的 binding 文件，本步现为**冗余保险**——跑不跑都行，只在 `ensure-bot.ps1` 版本较旧、没有这个自动写入行为时才需要手动补跑。

## 判活规则（用户问"飞书还在吗"）

**永远不要靠"心跳 send ok=true"或"PostCompact hook 说 Monitor 在跑"判活**——它们只证明出站能发，不证明入站事件能到 Claude。

详细决策树：参考 [bridge repo docs/lessons/monitor-pipe.md](https://github.com/<github-user>/feishu-claude-code-bridge/blob/main/docs/lessons/monitor-pipe.md)。

简版：
1. 用户消息以 `task-notification` 推过来，task-id 等于本 session 启 Monitor 时返回的 ID → 链路 100% 活
2. 看到 `Monitor "..." stream ended` 通知 → 必死，重起
3. `Get-CimInstance` 看 subscribe 进程在 → 必要不充分（孤儿场景下进程在但流不到 Claude）

新 session 启动 / `/compact` 完成 / 自动压缩完成后，**默认假设是孤儿，无条件重连**（不论 PostCompact hook 说什么）。

**`TaskList` / `TaskGet` 不能用来判活**：这两个工具不追踪 Monitor watch，`TaskGet <monitor-task-id>` 即使在 Monitor 活着时也会返回 "Task not found"，`TaskList` 也不会列出它。同理，心跳 `messages-send` 返回 `ok=true` 只证明出站能发，不证明入站事件能到 Claude。判活只认上面 1、2 两条。

## 其他偏好

- 中文简短沟通，代码/路径保留原文。
- 工具调用前一句话说明；不堆长篇解释。
- 自检静默完成，出错再说；不要复述本文件内容。

## Vault 知识库（如果配了）

Path: `<USER_HOME>\Documents\<vault-name>\`

需要某个领域 context 时按此顺序：
1. 读 `wiki/hot.md`（最近 context，~500 字）
2. 不够 → 读 `wiki/index.md`
3. 还不够 → 读 `wiki/meta/notes-graph.md` 看跨笔记关系
4. 最后 → 读具体 `wiki/sources/<domain>/<note>.md`

不要为了"通用编程问题"或"本项目已有信息"去读 vault。

## Memory 系统（如果装了 claude-mem）

`~/.claude-mem/` 是跨 session 持久记忆。问"上次怎么解决 X" / "之前我们讨论过 Y 吗"时可以查 [[mem-search]] skill。

另外还有一份**文件型**的自动记忆索引（`memory/MEMORY.md`，每个新 session 开始时自动读取），与上面的 claude-mem SQLite 库是两套独立机制，互不替代。搭建/排查参考 `setup/07-memory-plugins.md`。

---

**编辑本文件时**：
- 不要复制粘贴本模板的 placeholder 注释；改成你自己的真实值
- 关于 bot 的部分，如果没用 Feishu 直接整段删
- 改完保存即生效（下次 session 启动读取）
