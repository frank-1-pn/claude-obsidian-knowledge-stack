# WorkBuddy 锁屏期间的后台任务入口调查

核查日期：2026-10-09。仅查询官方资料、已安装程序静态代码、注册协议与只读探针。未提交任务、读取凭据、修改配置、启用调试服务或操作锁屏。先前真实 GUI 任务与业务验收由主集成人记录，本调查不增加完成项。

**结论：有官方远程助理 API，但目前没有证据证明本会话拥有可直接调用、且能绑定本次独立工作区的后台入口。已注册 deep-link 只预填输入，不自动执行。恢复正常桌面后继续 GUI 验收仍是当前确定的路径。**

## 官方 Open API：存在，当前未接入

[WorkBuddy 官方 Open API](https://open.workbuddy.cn/docs/openapi)提供 PC 本地助理消息与历史接口；需要已注册第三方应用、用户 OAuth 2.1 授权及对应 scope。

| 接口 | 用途 / scope |
| --- | --- |
| GET `/openapi/v2/localassistant` | 在线状态；`user.localassistant.readable` |
| POST `/openapi/v2/localassistant/message` | 任务消息；`user.localassistant.invokable` |
| GET `/openapi/v2/localassistant/message` | 按 `message_id` 增量读回；`user.localassistant.readable` |

发送体包含 `content` 与 `msg_type`；`text` 为输入，`permission_response` 对应原请求的问答/审批。文档消息体没有独立项目、cwd 或新任务选择参数，不能直接认定会投递到本次自有验证项目。

当前会话没有可核实的第三方 OAuth 凭据与 scope；本次没有检查秘密内容，也不能断言账号从未授权过第三方应用。桌面登录不自动证明第三方 Open API 授权。云端 `/tasks` 另有沙箱环境，不替代本机工作区验收。

## 当前注册协议：只预填，不提交

Windows 注册表确认存在 `workbuddy-ai` URL Protocol，由 WorkBuddyAI.exe 接收 URL 参数。只读核对安装包中的 task deeplink parser 与 coordinator 后，支持的形态为：

```text
workbuddy-ai://task?action=start&prompt=<URL-encoded text>&cwd=<URL-encoded path>
```

名称 `start` 容易误解。当前实现实际为导航首页、准备新输入并应用 prompt/cwd；输入消费者设置输入内容，不调用 send/submit。已有草稿时还可能出现保护确认。该链接不能证明后台任务已经创建或执行。本次未打开链接。不要额外传权限提升参数。

上述是本机 5.7.6 静态实现证据，并非稳定公开 API 承诺。

## CLI、内部桥接与已启用服务

- 当前 PATH 未发现 `workbuddy`、`codebuddy` 或 `cbc` 命令。[官方 CLI 文档](https://www.codebuddy.cn/docs/cli/cli-reference)描述的是 CodeBuddy Code；独立启动其内嵌或外部 CLI 不能作为 WorkBuddy 桌面任务验收。
- 本体只读探针返回 `workbuddy-desktop` 5.7.6。邻近默认 eval 端口没有响应 `/ping`；本次没有启用该服务。静态 eval 创建代码使用 `bypassPermissions`，不作为候选入口。
- 本体页面的 MessageChannel 桥接依赖真实 renderer 页面上下文，当前没有已开放的合法外部控制入口；不能通过改 app flag、打开调试端口或抽取私有 engine token 来创造入口。
- 已有通讯连接器属于用户现有能力，本调查未读取绑定或自行发送消息。没有对应现行授权、目标与路由证据时，不能借其投递来绕过当前独立项目边界。

暂时没有新增业务链完成证据。等待用户恢复桌面不等于暂停整体项目：源码、介绍、计划与本地验证仍可继续独立审核；后续真实 WorkBuddy 科学、PPT、笔记链须保留未完成状态。
