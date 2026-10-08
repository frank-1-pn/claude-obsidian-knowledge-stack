# WorkBuddy 上手

本版沿用朋友已经有的微信和飞书读取连接器。只需让 WorkBuddy 能读取和写入自己的 vault；连接器配置无需从本仓库复制。

## 初始化自己的 vault

让 AI 先检查 Obsidian 是否已经安装；有则复用，没有则自动从官方源下载安装并检查程序是否落盘。此步骤已接入默认初始化命令，无需再次询问同范围安装许可。在下载的分享仓库运行：

```powershell
python -m pip install -r requirements.txt
python scripts/init_vault.py --vault "D:/my-knowledge-vault"
python scripts/check_bootstrap.py --vault "D:/my-knowledge-vault"
```

`init_vault.py` 首先执行 `ensure_obsidian.py`：Windows 安装到当前用户，macOS 放入 `~/Applications`，Linux 使用当前用户的官方 AppImage；下载版本由官方最新稳定发布动态确定，校验 SHA-256 后才安装。安装失败就停止并报告具体问题，不把“下载完成”当成安装完成。纯脚本/无桌面环境可显式加 `--skip-obsidian`。

把生成的文件夹在 Obsidian 打开，并在 WorkBuddy 中选为工作区或授予相应本地文件访问。若宿主无本地写入能力，先解决文件访问，不能只在聊天中输出笔记就声称已入库。

初始化可重复执行，已有文件保留；它不会升级已有规则/skills。新版本升级时先比较差异，再定向迁移，保留自己的内容。

如需跨会话并发，先由用户在自己的 vault 配置 Git。无需并发时可以保持非 Git、单会话串行。默认不会替用户 git init，也不会创建系统定时任务。

## 首次给 WorkBuddy 的提示

```text
请完整读取 AGENTS.md、skills/wiki/SKILL.md 和 wiki/hot.md，遵循本地规则。
先运行 python scripts/ensure_obsidian.py；已安装则复用，未安装则自动下载安装并核对实际程序路径。
按任务读取 wiki-ingest、wiki-query、save、wiki-lint 或 autoresearch 的 SKILL.md。
微信文章和飞书用我现有的连接器取得；在 .raw/ 中保存实际取得的正文和来源信息。
先核对完整性，再生成一篇原子笔记，逐篇完成关系、索引、日志、latest、检查，manifest 最后写。
缺少子 agent 时说明串行执行。请先处理我明确指定的第一份来源。
```

## 连接器材料接入

- 微信：Markdown 放 `.raw/wechat/`；真实 HTML 若有则同名归档。记录原文标题、作者、日期、URL 与内容覆盖范围。
- 飞书文档：按实际导出格式存 `.raw/webfetch/` 的正文快照，或 `.raw/pdf/` 的 Office/PDF 原件；聊天记录用 `.raw/transcripts/`。保持权限和来源链接，不把“能读取”当作“能外发”。
- 截图：`.raw/screenshots/`；同主题多张用 01、02 编号目录。
- 截断、验证码或不可读内容：标 partial，保留有效材料，不编造段落或全文状态。

## 日常操作示例

| 需求 | 给 WorkBuddy 的话 |
|---|---|
| 整理新来源 | “按 wiki-ingest 整理这个来源，先归档，再入库” |
| 从库里找答案 | “按 wiki-query 查询 X，引用对应笔记，不写新笔记” |
| 保存讨论 | “按 save 保存这次讨论，只建一个 sessions 文件” |
| 检查 | “按 wiki-lint 检查，不自动改源笔记” |
| 研究 | “按 autoresearch 研究 X，默认一篇综述，说明来源与缺口” |

朋友实际验收时需验证：连接器正文完整、文件确实写到 vault、摘要可检索、source raw_path 可回溯、图片实际可显示、所有逐篇元数据已闭环。本仓库的脚本验证不代替 WorkBuddy 实机验收。
