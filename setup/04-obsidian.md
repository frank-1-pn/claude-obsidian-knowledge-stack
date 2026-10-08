# 在 Obsidian 阅读

## AI 先检查，缺少时自动安装

```powershell
python scripts/ensure_obsidian.py
```

脚本检查程序路径、Windows 注册信息及 Linux 的 Flatpak/Snap 安装信息。发现已有程序就复用；缺少则下载 [Obsidian 官方发布](https://obsidian.md/download) 的最新稳定版本，校验发布元数据中的 SHA-256，再安装到当前用户可写位置。Windows 的 `/currentuser` 参考 [WinGet 官方 Obsidian 清单](https://github.com/microsoft/winget-pkgs/tree/master/manifests/o/Obsidian/Obsidian)，`/S` 参考 [NSIS 静默安装说明](https://nsis.sourceforge.io/Docs/Chapter3.html#installerusage)。

初始化脚本默认调用此检查。安装器结束后再检查实际程序路径；失败返回非零状态。遇到系统阻止、网络失败或校验不符，AI 应报告具体原因和完成到哪一步。只读检测可运行 `python scripts/ensure_obsidian.py --check-only`。

macOS 安装于 `~/Applications/Obsidian.app`；Linux AppImage 位于 `~/.local/opt/obsidian/Obsidian.AppImage`，可由 `~/.local/bin/obsidian` 启动。若 Linux 缺少 AppImage 的运行依赖，须说明运行限制，按 [官方安装说明](https://help.obsidian.md/install)处理，不能把“文件已安装”当作“桌面启动已验证”。

## 打开笔记库

使用 scripts/init_vault.py 生成自己的 vault，然后在 Obsidian 选择“打开文件夹作为仓库”。从 wiki/index.md 或 wiki/最新笔记.md 开始。

附件在 vault 根 `_attachments/`，不是 `wiki/_attachments/`。双链与 callout 使用标准 Markdown/Obsidian 语法，不依赖额外插件。Bases 和 Canvas 是可选展示层。

如需多设备同步，由朋友选择并配置 Obsidian Sync、Git 或其他文件同步方案。先用一篇测试笔记和附件确认双向同步，再用于自己的资料；本仓库不设置同步账号、自动提交或定时推送。
