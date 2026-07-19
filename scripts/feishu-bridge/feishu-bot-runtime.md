# 飞书 bot 运行时规则

配套脚本见 [`../feishu-bridge/`](.)（`ensure-bot.ps1` / `monitor-bot.sh` /
`notify-once.ps1` / `write-binding.ps1` / `feishu-watchdog.ps1` 等），启动流程见
[`../../setup/03-feishu-bot.md`](../../setup/03-feishu-bot.md)，全局自检顺序见
[`../../config/global-claude-md.template.md`](../../config/global-claude-md.template.md)。

**适用范围**：本 session 已经绑定一个 bot（全局 CLAUDE.md「启动自检」跑完、Monitor
已启、binding 文件已写）之后才用得上这份规则。没绑定的 session 不需要读这份文件。

如果你把这份文件当 Claude Code skill 用，建议这样描述触发条件：发飞书消息 / 回复飞书
/ 长消息截断（末尾 `...(truncated)`）/ 出现 `stream ended`、`another event
+subscribe`、`permission_violations`、`file must be a relative path` 等报错 / 本
session 已绑飞书时准备执行高风险操作。

---

## 核心约束（背景）

1. **按 bot 粒度判冲突**：看 `event +subscribe` 进程命令行里的 `--profile <name>`，
   没有 `--profile` = 默认 bot（本文档记作 `<DEFAULT_BOT>`）。同一个 bot 已被别的
   session 占用 → 不抢；不同 bot 互不影响，可以分别绑定。
2. **一 session 一 bot，不串线**：只响应绑定 bot 推来的事件、只往绑定的
   `<CHAT_ID>` 发消息。事件里的 `chat_id` 跟绑定值对不上 = 异常，停止回复并报告
   用户，不要猜测发到别的 chat。
3. **无空闲 bot 可绑时主动问**：所有已注册 bot 都被占用 → 问用户要不要切换
   config / profile，或者暂不连；只要有一个空闲 → 问用户连不连、连哪个。不要替
   用户做主直接抢占别的 session 正在用的 bot。

---

## 收发消息规范

- 只在 `chat_id` 等于**本 session 绑定 chat_id** 的 `im.message.receive_v1` 事件时
  回复；其余事件一律忽略或原样报告给用户，不要跨 bot 回话。
- 回复必须发到绑定的 `<CHAT_ID>`（如果是群聊，事件里的 chat_id 本身就必须归属于
  绑定 bot，不能借用另一个 bot 的群）。
- **长消息被截断（末尾出现 `...(truncated)`）→ 必须自己取全文，不要让用户重新粘贴一
  次**：
  - `lark-cli im +messages-mget --message-ids <om_xxx> --as bot [--profile <name>]`
  - 或按时间线翻页找：`lark-cli im +chat-messages-list --chat-id <CHAT_ID> --as bot
    --page-size 5 [--profile <name>]`
- **文件 / 图片下载**：从消息 `content` 里的 `<file key="..." name="..."/>`（或
  `<image key="..."/>`）取出 `file_key`，`cd` 到你的下载目录（例如
  `<USER_HOME>/lark-downloads`），再执行：
  ```
  lark-cli im +messages-resources-download --message-id <om_xxx> --file-key <key> \
    --type file|image --as bot --output "./<name>" [--profile <name>]
  ```
  下载目标路径必须是相对路径（见下方故障符号表），所以要先 `cd` 再传 `./文件名`。
- 长回复用 `--markdown`；终端里禁止打印 appSecret / accessToken 等凭证。

---

## 判活规则（判断链路是否真的活着）

**核心原则：永远不要靠"心跳 `messages-send` 返回 `ok=true`"，也不要靠"某个 hook
说 Monitor 在跑"来判活**——这两者只证明**出站能发**，完全不能证明**入站事件能到
Claude**。历史上不止一次因为这个误判坑过人，不能再犯。

### 判活信号（按可信度从高到低排列）

1. **入站事件刚到（最强正向信号）**：用户消息以 `task-notification` 的形式推进
   来，且 task-id 等于本 session 启动 Monitor 时返回的那个 ID → 链路 100% 活着，
   有这条信号就不需要再验证别的。用户问"还在吗"这句话本身往往就是经由 Monitor
   推上来的——只要这条消息的 task-id 对得上本 session 绑定 bot 的 Monitor task
   id，直接回答"活着"即可。
2. **`Monitor "..." stream ended` 通知（最强反向信号）**：本 session 的 Monitor
   task 挂了之后，飞书侧会推一条 `status=completed, summary=Monitor "..." stream
   ended` 的通知。看到这个 = 必死，必须立即重启 Monitor（见下方重连流程）。
3. **`Get-CimInstance` 查 `event +subscribe` 进程（必要不充分）**：抓
   `node.exe ... event +subscribe`，按 `--profile` 区分是哪个 bot。**进程还在不
   等于链路还活着**——孤儿场景下进程活着，但事件流已经到不了 Claude 了。

### 明确不算数的信号

- **`TaskList` / `TaskGet` 不能用来判 Monitor 活不活**：这两个工具只列
  `TaskCreate` 系任务（有 `subject` / `status` / `blockedBy` 字段），根本不追踪
  Monitor watch。`TaskGet <monitor-task-id>` 会直接返回 `"Task not found"`——
  哪怕 Monitor 这时候活得好好的。所以"`TaskList` 里没有飞书相关 task = Monitor
  死了"是一个**错误的判断依据**：Monitor 活着的时候 `TaskList` 本来就是空的。
- **心跳 `messages-send` 返回 `ok=true`**：只证明这次出站发送成功，跟入站事件
  能不能到 Claude 没有任何关系。

### 决策树

| 触发场景 | 处置 |
|---|---|
| 新 session 启动 / `/compact` 完成 / 自动压缩完成 | 上一个 session 的 Monitor task 必死，但 subscribe 子进程不会跟着死 → **默认假设是孤儿**，无条件走下方重连流程（不管有没有 hook 说 Monitor 还在跑） |
| 用户问"飞书还在吗 / 连接正常吗" 且本 session 启过 Monitor | 先看本 session 对话里有没有该 Monitor task 的 "stream ended" 通知；没有 → 顺手 `Get-CimInstance` 确认 subscribe 进程还在 → 发一条心跳 + 正常回复；有 → 走重连流程 |
| 用户问同样的问题，但本 session 还没启过 Monitor（少见） | 直接走重连流程 |

### 重连流程

1. `Get-CimInstance` 查本 session 绑定 bot 的 `event +subscribe` 进程在不在。
2. 在 → **判定为孤儿，必须先杀掉**：`Stop-Process -Id <PID> -Force`（只杀同一个
   bot 的 subscribe 进程，用 `--profile` 精确匹配，不要误杀其他 bot 或其他
   session 正在用的进程）。
3. 按启动自检里的参数重新起 `ensure-bot.ps1` + Monitor。
4. 发一条心跳 `messages-send`，确认返回 `ok=true`。
5. **在对话里记下新的 Monitor task ID**，后续判活都靠这个新 ID，不要再用旧的。

### 孤儿 subscribe 的危险（为什么会出现"表面正常但用户消息收不到"）

`lark-cli` 的 `event +subscribe` 子进程是用 `Start-Process -WindowStyle Hidden`
以**分离进程**方式起的，**不在 Monitor task 的进程组里**。所以 Monitor 死了（比
如 `/compact` 之后），这个子进程完全不受影响，继续拿着 WebSocket 连接收事件——但
这些事件只会被写进 ndjson 文件，没有 Monitor 在读，Claude 端就彻底静默。

表现出来的症状极具迷惑性：飞书 bot 显示在线、`messages-send` 返回 `ok=true`、
但用户在飞书上发的消息一条都到不了 Claude。**修复方式**：杀掉孤儿子进程 + 重启
Monitor（见上方重连流程），不要以为"bot 在线 + 能发消息"就代表链路正常。

---

## 外部 Watchdog（无人值守时的兜底）

上面的判活规则依赖"有人正在跟 Claude 对话、Monitor 推事件过来"。如果长时间没
人打开 session，daemon 死了也不会有人发现，直到下一条消息悄悄消失。

用 [`feishu-watchdog.ps1`](./feishu-watchdog.ps1) 兜底：注册成 Windows 计划任务，
每 ~30 分钟跑一次，**静默**检查对应 bot 的 `event +subscribe` 进程是否存活；
- 进程还在 → 什么都不做，不发任何消息（不要做成定时心跳，那样会变成骚扰）。
- 进程死了 → 发一条飞书告警到这个 bot 自己的 `<CHAT_ID>`，提示用户回到电脑前跟
  Claude 说一句话（触发 SessionStart / 启动自检自动恢复），或手动重启。

具体的 `schtasks` 注册命令见脚本文件头部注释。

---

## 故障符号速查

| 症状 | 处理 |
|------|------|
| `another event +subscribe instance is already running`（针对用户要绑的这个 bot）| **不要杀对方进程**。这说明同一个 bot 已经被另一个 session 占用了，本 session 不要绑这个 bot；问用户要不要换其他空闲 bot，或者暂不连接。 |
| 看到 `event +subscribe` 进程但识别不出属于哪个 bot（命令行里既没有 `--profile`，又不像默认 bot）| 报告用户"检测到一个来源不明的 subscribe 进程，PID=xxx"，让用户自己确认是哪个 bot 起的。**不要自作主张杀掉**。 |
| `stream ended`（用户明确要求连接这个 bot 时出现）| 单独手动跑一次 subscribe 命令看完整报错；如果确认是被占用，告知用户，**不要自己杀掉对方 session 的进程**。 |
| `permission_violations` | 打开报错信息里的 `console_url` 链接，让用户去开对应的 scope 权限——**bot 身份没法自己 `auth login`**，必须是用户去控制台授权。 |
| `file must be a relative path` | 先 `cd` 到目标目录，再用 `./文件名` 这种相对路径调用，不要传绝对路径。 |

---

## 风险操作的飞书确认

**仅当本 session 已经绑定飞书时适用**（没绑定的话直接在终端问用户就行）。

以下这类**高风险操作**执行前，必须先走飞书确认，不能自己直接推进：
删除文件、覆盖已有内容、`git push --force`、`rm -rf`、修改数据库或其他共享状态、
向外部系统发消息等。

1. 用 `lark-cli im +messages-send` 把下面内容发到绑定的 `<CHAT_ID>`：
   > ⚠️ 准备执行：`<具体命令>` / 影响：`<1-2 句话说清楚后果>` / 回复 `yes` 确认执
   > 行 / 回复 `no` 放弃 / 也可以直接说你想要的替代方案
2. 等用户在飞书上回复（这条回复会作为 Monitor 事件推回来，正常处理即可）。用户
   没回复之前，操作挂起，不要自行推进、也不要超时后默认执行。

**注意**：Claude Code 自身 harness 层的权限确认弹窗（`approval dialog`）**不会**
转发到飞书——如果卡在这种弹窗上，要主动发一条飞书消息告诉用户"当前卡在某个操作
的权限确认，需要回电脑处理，或者调整对应的 allow-list"，不要让用户以为是飞书链
路本身出了问题。
