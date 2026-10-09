# WorkBuddy 运行入口与实际验收调查

核查日期：2026-10-09。调查范围为官方文档、已安装程序静态代码、进程与只读本地探针；未发送任务，未安装程序，未修改宿主配置，未读取凭据正文。本文件不构成业务功能验收。

## 结论

本机已安装并运行腾讯 WorkBuddy 桌面本体 5.7.6。当前原生窗口可见且启用，能够作为真实任务验收入口。尚未证明登录有效、模型请求可成功，或本项目技能已加载。只执行仓库脚本、独立 CodeBuddy CLI、生成测试文件，都不能证明在 WorkBuddy 中跑通。

WorkBuddy 使用内嵌 CodeBuddy engine。当前本体派生 daemon → sidecar → engine 的父子关系已确认；该 engine 的存在只能证明运行结构。任何新增任务必须由本体现有调度创建并能从 GUI/history 读回，才能作为 WorkBuddy 证据。

## 官方配置机制

- [WorkBuddy 项目配置](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)：支持项目 `.codebuddy/rules/`、`.codebuddy/agents/`、`.codebuddy/skills/`、`.codebuddy/commands/`、`.codebuddy/CODEBUDDY.md`；兼容 `CODEBUDDY.md` 与 `AGENTS.md`，同名配置以项目级优先。
- [WorkBuddy 技能](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)：可以导入本地技能包，安装后在对话调用；启停状态另存于用户配置，不修改 `SKILL.md`。
- [WorkBuddy 设置](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Setting)：用户级 `.codebuddy` 配置可与项目级配置共同使用。
- [WorkBuddy 首个任务](https://www.codebuddy.cn/docs/workbuddy/FirstTask)：官方桌面操作路径为登录 → 新建任务 → 描述任务 → 发送 → 查看结果与工作空间产物。
- [CodeBuddy CLI 参考](https://www.codebuddy.cn/docs/cli/cli-reference)：`codebuddy -p` 与 `--serve` 是 CodeBuddy Code 入口。不能据此声称腾讯 WorkBuddy 桌面任务验收通过。

复刻仓库应将可分享配置放到项目目录，让 WorkBuddy 打开或选用该项目；私有资料、账号配置、连接器凭据及本机状态不得纳入模板。

## 当前本机证据

安装目录：`%LOCALAPPDATA%/Programs/WorkBuddyAI/`。Windows 文件版本为 `5.7.6.0`。

只读请求：

```http
GET http://127.0.0.1:18488/workbuddy/probe
```

实际返回：

```json
{"ok":true,"app":"workbuddy-desktop","version":"5.7.6","platform":"win32"}
```

本体内嵌 engine 的首页标题为 `CodeBuddy Remote Control`，API 读取返回 HTTP 401，说明存在鉴权边界。本次没有提取其鉴权值。固定端口、PID、窗口句柄与会话标识会漂移，交接后必须重新发现，不应写入复刻脚本。

UI Automation 只暴露 Chromium 窗口与渲染 pane，没有暴露输入框或按钮；因此不能直接依靠 UIA 对象定位完成测试。可由集成人使用 GUI 截图与实际输入，或在本体页面上下文调用本体已存在的桥接。

## 本体页面内 daemon 调度接口

以下来自本次已安装程序静态代码。它是内部实现，非官方稳定 API；只适合当前本体的受控本机验收，不应作为朋友复刻的永久依赖。当前尚未实际调用这些业务接口。

本体 preload 接受页面 `MessageChannel`：

```javascript
const channel = new MessageChannel();
window.postMessage(
  { type: 'workbuddy:open-local-daemon-transport-port', target: null },
  '*',
  [channel.port2]
);
channel.port1.start();
```

调用帧：

```javascript
channel.port1.postMessage({
  kind: 'message',
  json: {
    id: 'owned-test-request-id',
    type: 'request',
    channel: 'session:create',
    args: [{ cwd: 'ABSOLUTE_ISOLATED_TEST_PROJECT', config: { mode: 'craft' } }]
  }
});
```

响应从 `port1.onmessage` 取得。native transport 返回 `kind: 'message'`，其中 `json` 为 `{ id, type: 'response', channel, result }` 或错误帧。模式与请求 schema 必须以实际本体返回校验；不要设置或提升 `permissionMode`。

已确认通道名称及参数形状：

| 操作 | channel | args |
| --- | --- | --- |
| 创建独立任务 | `session:create` | `[{cwd, config}]` |
| 发送本任务输入 | `session:sendMessage` | `[newSessionId, [{type:'text', text:prompt}]]` |
| 读取本任务状态与历史 | `session:get` | `[newSessionId]` |
| 列任务 | `session:list` | `[]`；应只筛选新建测试任务 |
| 取消本任务 | `session:cancel` | `[newSessionId]` |

事件帧为 `{ type: 'event', channel: 'session:event', result: ... }`。只保留本次自有测试任务事件，避免收集其他任务内容。`session:get` 的静态实现包含 `eventHistory`、`pendingPermissions`、`pendingQuestions`、`pendingElicitations`、`isProcessing`、`stopRequested` 和任务状态；适合区分真实完成、等待审批与仍在执行。

此页内桥接沿用本体现有 daemon，不需要读取 token，也不需要新启 CLI 或重启 WorkBuddy。它必须在真实 WorkBuddy 页面执行，普通浏览器页或本地 Node 不具有该 native bridge。主集成人负责真正提交、审批处理与结果验收。

## 不应使用的测试捷径

安装包内存在 `EvalProxyServer`，设计接口为 POST `/sessions`、POST `/chat/{sessionId}` 与 GET `/sessions`。当前该服务未启用。其创建任务代码硬编码 `permissionMode: 'bypassPermissions'`；本次没有启动它。不能为方便测试开启此路径或据此绕过现有审批。

内嵌 engine 的 ACP 使用 `/api/v1/acp/connect` 与 `/api/v1/acp`，涉及连接标识 header `acp-connection-id` 及认证。直接连接既有私有 engine 会造成任务归属和 history 证据不清；本次未使用。优先从本体 GUI 或页面 daemon transport 创建自有测试任务。

## 真实验收所需证据

1. 在隔离项目中启动新 WorkBuddy 任务，记录测试任务 ID、项目路径、本体版本与输入。
2. 证明项目规则和对应 skills 被本体加载；保留该任务的读取/调用记录。
3. 管线调研先执行 brainstorming 澄清范围，再形成可执行计划，执行后逐项核验来源与结果；不能只生成一段模拟对话。
4. 科学技能使用去标识化样例完成实际工具调用与可核查产物；模型输出能力不等同于真实药效或实验验证。
5. PPT Master 生成实际 PPTX，核对内容、页数、可编辑对象及视觉结果；不能把仅写 Markdown 当作 PPT 验收。
6. Obsidian 在临时 vault 完成 raw-first 入库、摘要标签、索引与关联、查询回读、检查；需要实际证据且不得污染个人 vault。
7. 从本体 `session:get` 和 GUI/history 对同一测试任务读回输出；产物按精确路径独立检查。`isProcessing: false` 本身不等同成功，仍需检查最终状态、错误与等待审批记录。
8. 智慧芽 MCP 与邮件按用户范围只提供接口与现场实施设计，状态明确为待接入，不假造成功连接。

当前未满足上述业务验收。安装、运行探针及接口发现只降低了下一步执行的不确定性。

## 可复刻工作区准备验证

本次另完成 `scripts/bootstrap_rd_assistant.py`、`scripts/check_rd_assistant.py` 与 `setup/10-rd-director-workbuddy.md`。真实操作在仓库外 OS 临时工作区执行，使用已有 Python 3.12.12 和独立 `.venv`，未修改全局配置或包。

2026-10-09 的 fresh bootstrap 返回 exit 0、`status: prepared`、`errors: []`：复制 1648 个文件并发现 39 个技能（10 Obsidian、24 scientific、2 工作流/PPT、3 未接入邮件模板）；上游固定 revision 与逐文件 SHA256 校验通过，7 个直接依赖和 6 个传递依赖的版本与实际 import 均通过。使用显式 `--git` 创建本地锁所需 Git，未提交或推送。测试使用显式 `--skip-obsidian`，没有据此声称桌面已安装或打开。

四个安全与迁移测试通过：冲突在写入前拒绝、工作区路径不能逃逸、完整源目录/技能迁移与篡改检测、既有已入库 wiki/raw/模板内容在重复初始化时保留。静态脚本/vendor 的 hash 冲突保持 partial，不覆盖；动态笔记内容不会回退。没有 Git 的默认工作区使用单会话串行写入，不假装拥有跨会话锁。

上述输出始终保留 `workbuddy_verified: false`。它证明安装包与指定离线环境准备，实际 WorkBuddy 任务链与桌面产物验收由主集成人独立完成。

## 复刻时的项目选择、信任与技能发现

补充核查日期：2026-10-09。主集成人在真实 WorkBuddy 项目选择器选用自己生成的工作区时，观察到 `Choose how to open`；选择 `Open normally` 后出现 `This workspace is now trusted`。本 worker 只读核对官方项目文档和已安装 5.7.6 静态代码，没有操作 GUI、提交任务或改变信任状态。

[官方项目说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)确认工作区 `.codebuddy/` 的项目规则、agents、skills、commands 与记忆入口可被发现，项目级同名配置优先。当前本体另有工作区信任门，不能仅凭目录存在或 deep-link 的 cwd 参数断言这些配置已经生效。

本机静态实现的判断关系为：按目录 realpath 形成 workspaceKey；检测 `.codebuddy` 并查询该工作区自己的信任决定；`Open normally` 保存此路径的 trusted 决定与 revision。限制模式的 UI 明确说明项目级设置不会自动加载，Agent Runtime Bash 被禁用。它与全局权限模式是不同概念，复刻无需改全局设置，也不要切换为 `fullAccess` 或使用 `bypassPermissions`。

朋友可按下面步骤操作：

1. 先审阅本仓库的角色、规则、适配入口、固定上游与 bootstrap；完成仓库外独立工作区的初始化。只选自己确认来源和内容的目录。
2. 用 WorkBuddy 项目/工作区选择器打开刚生成的助手工作区。项目路径必须是工作区根目录，能看到 `CODEBUDDY.md`、`agent.md`、`AGENTS.md` 和 `.codebuddy/skills/`；不要把源码仓库或旧个人 vault 当成验证工作区。
3. 如出现 `Choose how to open`，在已审阅的该目录选择 `Open normally`，确认 trusted 提示。这个动作是当前工作区的正常产品授权，不要求放宽全局权限。
4. 在已选用的工作区新建任务，再核对角色入口与项目技能的实际发现/读取。当前静态文案存在“对新任务或重启后生效”的分支；若已有任务仍显示限制模式，优先在同一已信任项目新建任务，不反复发送旧任务，也不为此改隐藏 flag。
5. 让任务读取所需适配 skill 与其真实原文路径，记录工具调用和产物。若技能目录有文件但菜单/模型未发现，保持未验证，先检查选用目录、信任状态与新任务上下文；显式读取入口只能证明读取，不单独证明自动发现成功。

限制模式适合继续审阅来源。若不选择信任，该模式下没有自动加载或执行证据，就应保留这一验收缺口；不要将 raw 文件复制、目录计数、deep-link 预填或独立 CLI 成功作为项目技能加载的替代。
