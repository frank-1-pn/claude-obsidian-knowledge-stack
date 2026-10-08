# 最小环境

必需：能访问本地文件的宿主、Python 3.10+ 和 PyYAML。Obsidian 用于阅读，Git 用于可选版本管理与跨会话锁。

```powershell
python --version
python -m pip install -r requirements.txt
```

默认初始化需要联网检查并安装缺少的 Obsidian；已安装时不会下载或重装。纯脚本环境可加 `--skip-obsidian`。初始化器和检查器不需要 Node、API key、Claude Code、daemon 或新增连接器。网络来源由已有连接器/可用工具读取。额外工具按实际需要自行选择。
