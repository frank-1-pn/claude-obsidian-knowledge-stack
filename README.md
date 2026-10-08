# claude-obsidian-knowledge-stack

把当前使用的 Obsidian 笔记流程分享给 WorkBuddy 用户：一份来源一篇笔记，先归档原料，再整理、关联、验收；后续按摘要、索引和原文检索。

本仓库提供 **10 个 skills、项目规则、空白 vault 模板和可运行脚本**。不含个人笔记、原始资料、附件、聊天记录、密钥或本机配置。

微信文章和飞书内容由朋友在 WorkBuddy 中已有的连接器读取。本分享版不提供这两类连接器的安装、抓取器、bot、bridge 或事件订阅。阅读整理规范仍保留。

## 给朋友的开始方式

1. 下载本仓库，或 `git clone https://github.com/frank-1-pn/claude-obsidian-knowledge-stack.git`。
2. 按 [WorkBuddy 上手](setup/00-workbuddy.md) 初始化自己的空白笔记库。
3. 在 Obsidian 打开生成的文件夹，在 WorkBuddy 打开或授权访问同一个文件夹。
4. 把下面这段话发给 WorkBuddy：

```text
请先完整读取当前笔记库的 AGENTS.md 和 skills/wiki/SKILL.md，再读取 wiki/hot.md。
以后根据我的任务按需读取对应 SKILL.md。微信文章与飞书内容用我已配置的连接器读取。
整理时先保存实际取得的原料，再按一份来源一篇笔记处理，完成索引、关系、日志与检查。
如果没有子 agent 能力，请说明改为串行执行。只有我明确说“同步”才提交和推送 Git。
```

不依赖 WorkBuddy 自动加载 AGENTS.md 或识别 `/wiki`。用自然语言即可：“整理这篇文章”“从库里查一下”“保存这次讨论”“检查笔记库”。

## 保留的系统

| 能力 | 文件入口 |
|---|---|
| 架构、初始化与任务路由 | skills/wiki/SKILL.md |
| 来源入库、阅读讲解、摘要与溯源 | skills/wiki-ingest/SKILL.md |
| 有引用的只读检索 | skills/wiki-query/SKILL.md |
| 结构与链接检查 | skills/wiki-lint/SKILL.md |
| 单文件会话保存 | skills/save/SKILL.md |
| 明确发起的研究与综述 | skills/autoresearch/SKILL.md |
| Canvas、Markdown、Bases、网页清理 | skills/canvas、obsidian-markdown、obsidian-bases、defuddle |

```text
skills/                当前 10 个技能与必要参考文件
scripts/               初始化、检查、latest、lint、provenance、集成锁
config/                新 vault 的 AGENTS.md 与 Claude 兼容入口
vault/skeletons/       空白入口、元数据、源笔记与综述模板
setup/                 WorkBuddy 优先的安装与可选能力说明
ARCHITECTURE.md         数据流与协作边界
CHANGELOG.md            分享仓库变更与实际验证
```

快速初始化（路径按自己电脑替换）：

```powershell
python -m pip install -r requirements.txt
python scripts/init_vault.py --vault "D:/my-knowledge-vault"
python scripts/check_bootstrap.py --vault "D:/my-knowledge-vault"
```

`init_vault.py` 只补缺失文件，不覆盖已有文件。Git 和 Obsidian Sync 都由朋友自行选择配置，不自动创建仓库、安装插件或同步。分享包验证可运行 `python scripts/verify_share.py`。

脚本在临时 vault 的归档、笔记、索引、日志、manifest 和最新笔记流程见 CHANGELOG.md，可运行 `python scripts/smoke_share.py` 重现；尚未在朋友的 WorkBuddy 环境实测。

## 许可与来源

源码与模板使用 MIT；保留 [LICENSE](LICENSE) 和 [ATTRIBUTION.md](ATTRIBUTION.md)。来源内容的权限另行判断。项目基于 AgriciDaniel/claude-obsidian，并按本地 Note-as-atom 流程适配。
