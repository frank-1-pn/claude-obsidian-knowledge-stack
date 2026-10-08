# -*- coding: utf-8 -*-
"""
refresh-latest.py —— 重新生成 vault 的「最新笔记」汇总入口页（卡片式）。
扫 wiki/sources/**/*.md（跳过 _index.md），按 frontmatter created: 倒序，
按日期分组，每篇笔记渲染成一张 Obsidian callout 卡片：显示【完整标题】+【文件夹】，
不含任何 emoji。手机端友好、互相分隔、一点即开。每次 ingest 末尾或定时任务调用刷新。

用法: python refresh-latest.py [vault_wiki_dir]
默认 vault_wiki_dir = 脚本所在 vault 的 wiki/
"""
import os, sys, io, re
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
WIKI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wiki")
SRC = os.path.join(WIKI, "sources")
OUT = os.path.join(WIKI, "最新笔记.md")

def read_created(path):
    try:
        s = io.open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", s, re.S)
    fm = m.group(1) if m else ""
    for line in fm.splitlines():
        if line.startswith("created:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""

rows = []
for dp, dn, fn in os.walk(SRC):
    for f in fn:
        if not f.endswith(".md") or f == "_index.md":
            continue
        full = os.path.join(dp, f)
        created = read_created(full)
        rel = os.path.relpath(dp, SRC).replace("\\", "/")
        top = rel.split("/")[0] if rel != "." else "(根)"
        sub = rel.split("/")[1] if "/" in rel else ""
        cat = top + ("／" + re.sub(r"^\d+-", "", sub) if sub else "")
        try:
            mt = os.path.getmtime(full)
        except Exception:
            mt = 0
        rows.append((created or "0000-00-00", mt, cat, f[:-3]))

rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
total = len(rows)

groups = OrderedDict()
for created, mt, cat, base in rows:
    groups.setdefault(created, []).append((cat, base))

L = []
L.append("---")
L.append("type: meta")
L.append('title: "最新笔记（卡片 · 时间倒序）"')
L.append("tags:")
L.append("  - meta")
L.append("  - latest")
L.append("---")
L.append("")
L.append("# 最新笔记")
L.append("")
L.append(f"> 共 **{total}** 篇 · 每篇一张卡片 · 最新在最上 · 点标题直接打开。新增/整理笔记自动刷新。")
L.append("")
L.append("> 导航：[[index|总索引]] | [[sources/_index|分类目录]] | [[log|操作日志]] | [[notes-graph|关系图]]")
L.append("")
for created, items in groups.items():
    day = created if created != "0000-00-00" else "（无日期）"
    L.append(f"## {day}　<small>（{len(items)} 篇）</small>")
    L.append("")
    for cat, base in items:
        # 一张 callout 卡片：完整标题(可点链接) + 文件夹，无 emoji
        L.append(f"> [!note] [[{base}]]")
        L.append(f"> {cat}")
        L.append("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
print(f"[refresh-latest] wrote {OUT}")
print(f"[refresh-latest] {total} notes (cards, full-title, no-emoji), {len(groups)} date groups")
