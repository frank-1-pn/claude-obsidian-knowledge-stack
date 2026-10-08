# 持久记忆

核心记忆已在 vault 文件中：hot 保存近期状态，index 负责入口，notes-graph 记录关系，log 保存操作时间线，raw 与 provenance 提供回溯。新会话按需读取这些文件。

WorkBuddy 的会话记忆能力以用户实际环境为准，不能替代原料归档和逐篇日志。本版不要求 claude-mem、SQLite worker 或对其他 Agent SDK 打补丁。将来选择外部记忆插件时，另行核对许可、数据流和权限。
