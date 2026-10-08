---
name: wiki
description: 管理或搭建 Note-as-atom 的 Obsidian 知识库，并把 ingest、query、lint、save、research、canvas 请求路由到对应 skill。用于 /wiki、搭建 wiki/知识库、检查 vault 结构、维护 hot cache 或配置跨项目访问；普通的单篇笔记处理应路由到专用 skill。
---

# Wiki 编排入口

这个 skill 负责知识库架构、初始化、路由和热缓存。知识库是长期产物，对话只是操作界面。

开始前先读取 vault 根目录的 `AGENTS.md`。它是当前 vault 的最高优先级规则；本 skill 不得覆盖其中的用户硬规则。若 `wiki/hot.md` 存在，静默读取它以恢复近期上下文。不要因为调用 `/wiki` 就重建一个已经存在的 vault。

## 默认后台编排

凡是会生成或重写笔记的请求（`wiki-ingest`、`save`、生成综述的 `autoresearch`、整理或合并），主 agent 默认按根 `AGENTS.md` 的 **Default Sub-agent Execution for Note Jobs** 委派给 note worker。主 agent 先用 `scripts/note_integration_lock.py` 取得跨 session 批次锁，再保持可交互，只做任务拆分、路径分配、用户沟通和唯一串行集成；worker 不得写共享索引或再次委派同一任务。纯查询、lint、结构检查和无需写笔记的 canvas 操作可以直接执行。

如果运行时没有 sub-agent 能力，主 agent 可以内联完成，但必须如实说明这是 fallback。委派不会扩大 commit、push、发布或外部消息权限。

## 当前架构：Note-as-atom

```text
vault/
├── .raw/                  # 外部原始物，存档后不可改写
│   └── .manifest.json     # 已摄取原料与增量状态
├── wiki/
│   ├── sources/           # 每份来源对应一篇原子源笔记，可按稳定主题分目录
│   ├── meta/
│   │   ├── notes-graph.md # 分组、关键词和跨笔记关系
│   │   └── provenance.md  # provenance 字段与核实手段词表
│   ├── index.md           # 总入口
│   ├── 最新笔记.md        # 按日期倒序生成的入口
│   ├── log.md             # 最新记录在顶部的时间线
│   ├── hot.md             # 近期上下文缓存
│   └── overview.md        # 全库概览
├── _attachments/          # 笔记实际引用的本地图片和文件
├── _templates/            # 可选的笔记模板
└── AGENTS.md              # 跨 agent 的本地规则
```

一份来源就是一个内容节点。不要从源笔记拆出实体、概念或问答派生页；跨笔记分组、关键词和关系集中维护在 `wiki/meta/notes-graph.md`。除非用户明确要求改变架构，否则不要新增平行知识层。

## 不可破坏的约束

1. **保护源笔记正文。** 用户未明确说“整理这份”时，不改正文、标点、文件名或位置。可按需新增或更新 frontmatter 的 `tags`、`related` 等字段。
2. **默认只使用来源事实。** 用户未要求外部补充时，不加入模型记忆或额外检索所得事实。明确要求补充时，每条外部内容用 `> [!external]` 或 `（外部补充：…）` 标注。
3. **外部原料先存档。** URL、PDF、截图、文档、仓库、网页、视频字幕、社区帖等必须先保存到合适的 `.raw/<type>/`，再写 `wiki/sources/`。`.raw/` 中的原始物不可改写；只追加新快照或新版本。
4. **新笔记可追溯。** frontmatter 必须包含相对路径 `raw_path` 和 `provenance`。多个原始物用 YAML 数组。`provenance.verified` 只记录本次实际做过的核实手段；宁缺勿假。
5. **生成内容先摘要。** 所有整理、合并或综述笔记都在第一个 H1 后、第一节前放置 100–200 字的 `> [!abstract] 摘要`。遵守手机端排版：列表逐项换行，列表前后留空行，callout 内段落之间保留空的 `>` 行。
6. **标题表达内容。** 标题说明“它是什么”和必要的实现差异，不把 Star、许可证、版本号、作者或会过期的数据塞进标题；合集按根 `AGENTS.md` 的专用命名规则。
7. **每次变更都闭环。** 每完成一篇源/综述笔记，立即在 `wiki/log.md` 顶部写一条记录，并同步 `wiki/meta/notes-graph.md`。更新索引后，执行根 `AGENTS.md` 指定的“最新笔记”生成命令；不要手改生成器负责的区块。
8. **图片按需生成。** 仅在机制、流程、架构或对比确实因图更易理解时调用可用的图片生成 skill。图中文字默认使用简体中文，文件保存到 `_attachments/<note-slug>/`，用 Obsidian embed 引用，并在 log 和 provenance 中如实记录。
9. **不擅自同步。** 初始化、整理或修复不等于允许 commit、push 或发布。只有用户明确要求相应操作时才执行；当前 vault 的额外限制以根 `AGENTS.md` 为准。

`provenance` 的最小结构：

```yaml
provenance:
  schema: v1
  model: <本次实际模型 id>
  derived: false
  recorded: YYYY-MM-DD
  verified:
    - raw-archived
```

`raw-archived` 也必须是实际完成存档后才能写。其他值及含义以 `wiki/meta/provenance.md` 为准。

## 请求路由

| 用户意图 | 处理方式 |
|---|---|
| `/wiki`、搭建/检查知识库、维护 hot cache、跨项目引用 | 本 skill |
| ingest、整理/加入一个或一批来源 | `wiki-ingest` |
| query、询问库里已知内容 | `wiki-query` |
| lint、健康检查、孤立笔记或死链 | `wiki-lint` |
| `/save`、归档本次对话 | `save` |
| 明确要求 autoresearch 或建立研究综述 | `autoresearch` |
| `/canvas`、把笔记或附件加入 Obsidian Canvas | `canvas` |
| 清理网页正文 | `defuddle` |
| Obsidian Markdown 或 Bases 语法 | `obsidian-markdown` / `obsidian-bases` |

调用子 skill 前完整读取它的 `SKILL.md`。只有用户明确要求“建研究子页”时，`autoresearch` 才可产生研究子页；否则只产出一个综述源笔记。`save` 只把对话归档为 `wiki/sources/sessions/` 中的单文件，不再拆页。

## Scaffold 工作流

仅在用户明确要求搭建新 vault，或现有 vault 缺少核心结构时执行。

先运行 `python scripts/ensure_obsidian.py` 检查桌面程序：已有 Obsidian 就复用，没有则自动下载安装并检查实际程序路径。默认初始化器已调用此步骤。脚本来自官方发布源，失败则说明安装停在哪一步；不要重复询问已经包含在本次搭建流程里的安装许可。纯脚本/无桌面环境显式用 `--skip-obsidian`；不安装 Obsidian 插件或配置同步账号。

1. 检查现有 `AGENTS.md`、`.raw/`、`wiki/`、`_attachments/` 和 git 状态。已存在内容时只补缺失项，禁止覆盖或迁移用户文件。
2. 若用途仍不明确，只问一个问题：“这个 vault 主要用来积累什么知识？”得到答案后直接继续。
3. 创建最小目录：`.raw/`、`wiki/sources/`、`wiki/meta/`、`_attachments/`；`_templates/` 仅在确有模板需求时创建。
4. 创建缺失的入口和元文件：`.raw/.manifest.json`、`wiki/index.md`、`wiki/最新笔记.md`、`wiki/log.md`、`wiki/hot.md`、`wiki/overview.md`、`wiki/sources/_index.md`、`wiki/meta/notes-graph.md`、`wiki/meta/provenance.md`。
5. 在根 `AGENTS.md` 记录 Note-as-atom、raw-first、源正文保护、日志/关系图/最新笔记/provenance 的约束。若用户已有规则，只做兼容性补充，不整文件替换。
6. 为“最新笔记”配置或复用一个确定性的刷新命令，并把实际命令记录在 `AGENTS.md`；不得假设某台机器固定的 home 路径。
7. 用一个最小示例或 dry-run 验证：原始物先进入 `.raw/`，源笔记能链接到它，log、notes-graph、index、最新笔记能正确更新，YAML 可解析，wikilink 无死链。验证产生的临时内容不得留在正式库中。
8. 汇报创建和保留了哪些路径、验证结果及仍需用户决定的选项。不要自动初始化 git、commit、push、安装 Obsidian 插件或写外部系统。

## Hot cache

`wiki/hot.md` 是近期上下文缓存，不是权威计数或操作日志。读取顺序是：`hot.md` → `index.md` / `sources/_index.md` → `notes-graph.md` → 具体源笔记。

在以下时机刷新 hot cache：

- 一次 ingest 或架构变更完成后；
- 一次会影响后续工作的重大 query 后；
- 用户要求保存当前工作状态时。

缓存应简短记录最近变化、关键事实、活动线程和未决问题。页数、日期等可计算状态必须从实际文件或生成器得出，不能沿用旧手工数字。若文件含自动生成标记，只更新允许手工维护的部分，不覆盖生成区块。权威历史在 `wiki/log.md`，权威关系在 `wiki/meta/notes-graph.md`。

## 跨项目引用

用户明确要求另一个项目访问本 vault 时，在对方项目的 `AGENTS.md` 中记录实际绝对路径和渐进读取顺序：

```markdown
## Wiki Knowledge Base
Path: <absolute-vault-path>

需要本项目之外的知识时：
1. 先读 `wiki/hot.md`；
2. 不足时读 `wiki/index.md` 或 `wiki/sources/_index.md`；
3. 需要关系或主题线索时读 `wiki/meta/notes-graph.md`；
4. 最后只读相关的 `wiki/sources/` 原子笔记。

不要为一般语法问题、项目文件已经回答的问题或无关任务读取该知识库。
```

不要在跨项目复制笔记内容；链接到唯一 vault。修改对方项目文件前仍需用户授权。

## 完成检查

一次会写入知识库的操作只有在以下项目全部满足后才算完成：

- 原始物已先存档，且 source frontmatter 的 `raw_path` 可解析；
- `provenance` 只写真正执行过的核实手段；
- 新笔记含摘要，YAML 与移动端 Markdown 排版有效；
- 没有建立派生拆分页；
- `wiki/log.md` 顶部已追加记录；
- `wiki/meta/notes-graph.md` 与必要索引已同步；
- “最新笔记”已通过配置的生成命令刷新；
- `wiki/hot.md` 没有保留已知过期的手工状态；
- 未经明确要求，没有 commit、push 或发布。


## 宿主适配

先读根 AGENTS.md。使用宿主实际提供的文件、搜索、网页和连接器工具；本文的 Claude 工具名与斜杠命令表示能力或意图，不要求在 WorkBuddy 安装同名工具。缺少自动 skill 发现时，直接按相对路径读取本文件。
