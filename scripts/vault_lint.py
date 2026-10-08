#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Full-vault lint for the knowledge-vault: frontmatter, titles (§6.2), links,
graph/log coverage, mobile formatting (§11). Read-only."""
import os, re, sys, json, io
from collections import defaultdict, Counter

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("report", nargs="?", default="vault_lint_report.md")
parser.add_argument("--vault", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
args = parser.parse_args()
VAULT = os.path.abspath(args.vault)
SRC = os.path.join(VAULT, "wiki", "sources")
OUT = args.report
if not os.path.isdir(SRC):
    raise SystemExit("missing wiki/sources: pass --vault <vault-root>")

try:
    import yaml
    HAVE_YAML = True
except Exception:
    raise SystemExit("PyYAML required: python -m pip install -r requirements.txt")

def read(p):
    with open(p, encoding="utf-8-sig", errors="replace") as f:
        return f.read()

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)

def split_fm(text):
    m = FM_RE.match(text)
    if not m:
        return None, text, None
    raw = m.group(1)
    body = text[m.end():]
    if HAVE_YAML:
        try:
            return yaml.safe_load(raw) or {}, body, None
        except Exception as e:
            return None, body, str(e).split("\n")[0][:160]
    # crude fallback
    d = {}
    for line in raw.splitlines():
        mm = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if mm:
            d[mm.group(1)] = mm.group(2)
    return d, body, None

FENCE_RE = re.compile(r"^```.*?^```", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

def strip_code(text):
    """Blank out fenced blocks and inline code — Obsidian does not linkify
    inside code, so link checks must ignore them (2026-07-25: 4 false 'dead
    links' came from exactly this)."""
    text = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return INLINE_CODE_RE.sub("", text)

notes = []          # dicts
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for fn in files:
        if not fn.endswith(".md") or fn == "_index.md":
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, VAULT).replace("\\", "/")
        domain = os.path.relpath(root, SRC).replace("\\", "/")
        text = read(p)
        fm, body, yerr = split_fm(text)
        notes.append(dict(
            path=rel, file=fn, stem=fn[:-3], domain=domain, text=text,
            body=body, fm=fm if isinstance(fm, dict) else None, yerr=yerr,
            size=len(text),
        ))

by_domain = defaultdict(list)
for n in notes:
    by_domain[n["domain"]].append(n)

# ---------- link graph ----------
LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\\?\|[^\]]*)?\]\]")

def norm_target(t):
    """Obsidian target → note stem: drop escaped-pipe leftovers, .md suffix, path."""
    t = str(t).strip().strip('"\'').rstrip("\\").strip()
    t = t.split("/")[-1]
    if t.endswith(".md"):
        t = t[:-3]
    return t.strip()
stems = {n["stem"]: n for n in notes}
# wiki/ 根与 meta/ 下的元文件也是合法 wikilink 目标（index / notes-graph / hot / log …）
for _d in [os.path.join(VAULT, "wiki"), os.path.join(VAULT, "wiki", "meta"),
           os.path.join(VAULT, "wiki", "术语表")]:
    if os.path.isdir(_d):
        for _f in os.listdir(_d):
            if _f.endswith(".md"):
                stems.setdefault(_f[:-3], None)
# also index attachments so image embeds don't count as dead links
attach = set()
for root, dirs, files in os.walk(VAULT):
    if os.sep + ".git" in root:
        continue
    for fn in files:
        if fn.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".svg", ".canvas", ".base")):
            attach.add(fn)
            attach.add(os.path.splitext(fn)[0])

inbound = defaultdict(set)
dead = defaultdict(list)
for n in notes:
    for tgt in LINK_RE.findall(strip_code(n["text"])):
        t = tgt.strip()
        base = norm_target(t)
        if base in stems:
            if base != n["stem"]:
                inbound[base].add(n["stem"])
        elif base in attach or base + ".png" in attach:
            pass
        else:
            dead[n["path"]].append(t)

# frontmatter related links (already counted above since related uses [[..]]? often plain)
def fm_list(n, key):
    if not n["fm"]:
        return []
    v = n["fm"].get(key)
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in re.split(r"[,\n]", v) if x.strip()]
    if isinstance(v, list):
        return [str(x).strip() for x in v]
    return [str(v)]

plain_related = defaultdict(list)   # related 写成裸字符串（Obsidian 不当链接）
for n in notes:
    for raw in fm_list(n, "related"):
        hits = LINK_RE.findall(raw)
        if not hits:
            base = norm_target(raw)
            if base:
                plain_related[n["path"]].append(base)
                if base in stems and base != n["stem"]:
                    inbound[base].add(n["stem"])
                elif base not in stems:
                    dead[n["path"]].append("(related 裸串) " + base)
            continue
        for tgt in hits:
            base = norm_target(tgt)
            if base in stems and base != n["stem"]:
                inbound[base].add(n["stem"])
            elif base and base not in stems and base not in attach:
                dead[n["path"]].append("(related) " + base)

# ---------- meta coverage ----------
graph_p = os.path.join(VAULT, "wiki", "meta", "notes-graph.md")
log_p   = os.path.join(VAULT, "wiki", "log.md")
graph   = read(graph_p) if os.path.exists(graph_p) else ""
logtxt  = read(log_p) if os.path.exists(log_p) else ""

def key_of(stem):
    # match by first 24 chars to survive minor title drift
    return stem[:24]

missing_graph = [n for n in notes if key_of(n["stem"]) not in graph]
missing_log   = [n for n in notes if key_of(n["stem"]) not in logtxt]

# ---------- §6.2 roundup title check ----------
ROUNDUP_HINT = re.compile(r"(周报|热榜|本周|最火|新秀|YYDS|盘点|合集|汇编|必读|逛逛|榜|排行|精选|top\s*\d+|\d+\s*个)", re.I)
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
# a "project name" heuristic: latin-alphabet token >=3 chars that isn't a stopword
STOP = {"github","the","and","for","with","from","llm"," llm","ai","api","cli","top","yyds","new","open","source"}
def latin_tokens(s):
    return [t for t in re.findall(r"[A-Za-z][A-Za-z0-9._\-]{2,}", s) if t.lower() not in STOP]

roundups, bad_titles = [], []
for n in notes:
    if ROUNDUP_HINT.search(n["stem"]):
        toks = latin_tokens(n["stem"])
        roundups.append((n, toks))
        if len(toks) < 2:
            bad_titles.append((n, toks))

# ---------- §6 abstract + §11 mobile formatting ----------
no_abstract, callout_tight, inline_enum, no_h1 = [], [], [], []
CALLOUT_START = re.compile(r"^>\s*\[!(\w+)\]")
for n in notes:
    b = n["body"]
    if "[!abstract]" not in b:
        no_abstract.append(n)
    if not re.search(r"^#\s+\S", b, re.M):
        no_h1.append(n)
    # inline enumeration ①②③ inside a paragraph — only flag what is actually
    # convertible: table rows / index list lines / headings / frontmatter are
    # legitimately left inline (2026-07-25 reflow pass established this)
    conv = 0
    for line in b.splitlines():
        body = line[1:].lstrip() if line.startswith(">") else line
        if len(re.findall(r"[①②③④⑤⑥⑦⑧⑨⑩]", body)) < 3:
            continue
        if body.lstrip().startswith(("|", "#")) or re.match(r"^\s*([-*+]|\d+\.)\s", body):
            continue
        # 「引用编号」不是罗列：①②④⑤ 连写、②–④ 区间、第 ⑤ 步 —— 判据是
        # 相邻两个圈号之间至少要有 4 个字的正文才算一项（2026-07-25 定）
        pos = [m.start() for m in re.finditer(r"[①②③④⑤⑥⑦⑧⑨⑩]", body)]
        gaps = [pos[k + 1] - pos[k] for k in range(len(pos) - 1)]
        if not gaps or min(gaps) < 5:
            continue
        conv += 1
    if conv:
        inline_enum.append(n)
    # callout blocks whose lines run >=4 consecutive non-empty '>' lines with no blank '>' separator
    lines = b.splitlines()
    i = 0
    tight = 0
    while i < len(lines):
        if CALLOUT_START.match(lines[i]):
            j = i + 1
            run = 0
            worst = 0
            in_fence_cb = False
            while j < len(lines) and lines[j].startswith(">"):
                if re.match(r"^>\s*```", lines[j]):
                    in_fence_cb = not in_fence_cb
                    run = 0
                    j += 1
                    continue
                if in_fence_cb:      # callout 内的代码块整段跳过
                    j += 1
                    continue
                if lines[j].strip() in (">", ">\t"):
                    run = 0
                elif re.match(r"^>\s*\|", lines[j]):
                    # callout 内的表格块：不能插空 > 行（会拆坏表格），不算违规
                    run = 0
                else:
                    run += 1
                    worst = max(worst, run)
                j += 1
            if worst >= 4:
                tight += 1
            i = j
        else:
            i += 1
    if tight:
        callout_tight.append((n, tight))

# ---------- frontmatter gaps ----------
REQ = ["title", "created", "tags"]
fm_gaps = defaultdict(list)
no_raw  = []
for n in notes:
    if n["fm"] is None:
        fm_gaps["YAML 解析失败"].append(n)
        continue
    for k in REQ:
        if not n["fm"].get(k):
            fm_gaps["缺 " + k].append(n)
    if not fm_list(n, "related"):
        fm_gaps["related 为空"].append(n)
    if not n["fm"].get("raw_path"):
        no_raw.append(n)

# ---------- duplicate-topic detection ----------
tok_index = defaultdict(list)
for n in notes:
    for t in set(x.lower() for x in latin_tokens(n["stem"])):
        tok_index[t].append(n["stem"])
dupes = {t: v for t, v in tok_index.items() if len(v) > 1 and len(t) >= 5}

orphans = [n for n in notes if not inbound[n["stem"]]]

# ---------- report ----------
w = io.StringIO()
W = lambda s="": w.write(s + "\n")
W("# vault lint report")
W()
W(f"- 笔记总数：**{len(notes)}**（yaml lib={'yes' if HAVE_YAML else 'no'}）")
W(f"- 域数：{len(by_domain)}")
W()
W("## 各域笔记数")
for d in sorted(by_domain):
    W(f"- `{d}` — {len(by_domain[d])}")
W()
W(f"## A. YAML 解析失败（§7.5）：{sum(1 for n in notes if n['yerr'])}")
for n in notes:
    if n["yerr"]:
        W(f"- {n['path']} → {n['yerr']}")
W()
W(f"## B. §6.2 标题不含项目名的合集类：{len(bad_titles)} / 合集共 {len(roundups)}")
for n, toks in bad_titles:
    W(f"- `{n['domain']}` :: {n['stem']}  (latin tokens={toks})")
W()
W("### B2. 全部合集类笔记（供人工判断标题是否够表意）")
for n, toks in sorted(roundups, key=lambda x: x[0]["stem"]):
    W(f"- [{len(toks)}] {n['stem']}")
W()
W(f"## C. 缺 [!abstract] 摘要（§6）：{len(no_abstract)}")
for n in no_abstract:
    W(f"- {n['path']}")
W()
W(f"## D. callout 内连续 >=4 行无空 `>`（§11 手机糊成一坨）：{len(callout_tight)}")
for n, c in sorted(callout_tight, key=lambda x: -x[1])[:40]:
    W(f"- [{c} 处] {n['path']}")
W()
W(f"## E. 内联 ①②③ 罗列（§11 禁）：{len(inline_enum)}")
for n in inline_enum:
    W(f"- {n['path']}")
W()
W("## F. frontmatter 缺口")
for k in sorted(fm_gaps):
    W(f"### {k}：{len(fm_gaps[k])}")
    for n in fm_gaps[k][:60]:
        W(f"- {n['path']}")
W()
W(f"## G. 死链：{sum(len(v) for v in dead.values())} 条，涉及 {len(dead)} 篇")
for p, ts in sorted(dead.items()):
    W(f"- {p}")
    for t in sorted(set(ts)):
        W(f"    - [[{t}]]")
W()
W(f"## H. 孤儿（无任何入链）：{len(orphans)}")
for n in sorted(orphans, key=lambda x: x["domain"]):
    W(f"- `{n['domain']}` :: {n['stem']}")
W()
W(f"## I. notes-graph 未收录：{len(missing_graph)}")
for n in missing_graph:
    W(f"- {n['path']}")
W()
W(f"## J. log.md 未收录：{len(missing_log)}")
for n in missing_log:
    W(f"- {n['path']}")
W()
W(f"## K. 无 raw_path（2026-05-03 后应有）：{len(no_raw)}")
for n in no_raw:
    W(f"- {n['path']}")
W()
W(f"## M. related 写成裸字符串（Obsidian 不识别为链接）：{len(plain_related)} 篇")
for p, v in sorted(plain_related.items()):
    W(f"- {p}")
    for s in v:
        W(f"    - {s}")
W()
W(f"## L. 同名 token 出现在多篇（潜在重复/可交叉链）：{len(dupes)}")
for t, v in sorted(dupes.items(), key=lambda x: -len(x[1]))[:60]:
    W(f"- **{t}** ×{len(v)}")
    for s in v:
        W(f"    - {s}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(w.getvalue())
print("notes:", len(notes), "| report:", OUT, "| bytes:", len(w.getvalue()))
print("yaml-fail:", sum(1 for n in notes if n["yerr"]),
      "| bad-titles:", len(bad_titles), "/", len(roundups),
      "| no-abstract:", len(no_abstract),
      "| dead-links:", sum(len(v) for v in dead.values()),
      "| orphans:", len(orphans),
      "| missing-graph:", len(missing_graph),
      "| tight-callouts:", len(callout_tight))

if any(n["yerr"] for n in notes) or dead:
    raise SystemExit(1)
