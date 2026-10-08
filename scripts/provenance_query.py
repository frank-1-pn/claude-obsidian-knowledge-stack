# -*- coding: utf-8 -*-
"""
按 provenance 查笔记——这套元数据的全部用处就在这里：**选择性重做**。

典型用法:
    # 哪些笔记从没记录过用 gh api 核实（讲 GitHub 项目的尤其该补）
    python scripts/provenance_query.py --missing gh-api

    # 哪些是回溯推断的（不是当时如实记录的）
    python scripts/provenance_query.py --derived

    # 哪些一条核实手段都没记
    python scripts/provenance_query.py --missing-all

    # 某个域下、且没记 raw-archived 的
    python scripts/provenance_query.py --missing raw-archived --domain 09-GitHub

    # 总览
    python scripts/provenance_query.py --stats

⚠️ 读结果时记住 schema 的语义：`verified` 里没有某项，只说明**当时没记**，
   不等于**没做**。所以这里的输出是「候选复查清单」，不是「问题清单」。
"""

import argparse
import collections
import glob
import io
import os
import re

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(VAULT, "wiki", "sources")


def load():
    out = []
    for p in sorted(glob.glob(os.path.join(SOURCES, "**", "*.md"), recursive=True)):
        if os.path.basename(p).startswith("_"):
            continue
        t = io.open(p, encoding="utf-8", newline="").read()
        if not t.startswith("---"):
            continue
        m = re.search(r"^---(?=\r?\n|$)", t[3:], re.M)
        if not m:
            continue
        fm = t[3:3 + m.start()]
        pm = re.search(r"^provenance:\s*$(.*?)(?=^\S|\Z)", fm, re.M | re.S)
        rec = {"path": p,
               "rel": os.path.relpath(p, SOURCES).replace("\\", "/"),
               "created": (re.search(r"^created:\s*(\S+)", fm, re.M) or [None, "?"])[1],
               "model": "?", "derived": None, "verified": []}
        if pm:
            blk = pm.group(1)
            mm = re.search(r"model:\s*(\S+)", blk)
            if mm:
                rec["model"] = mm.group(1)
            dm = re.search(r"derived:\s*(\S+)", blk)
            if dm:
                rec["derived"] = dm.group(1) == "true"
            rec["verified"] = re.findall(r"^\s+-\s+(\S+)\s*$", blk, re.M)
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--missing", help="列出 verified 里没有该手段的笔记")
    ap.add_argument("--has", help="列出 verified 里有该手段的笔记")
    ap.add_argument("--derived", action="store_true", help="只看回溯推断的")
    ap.add_argument("--live", action="store_true", help="只看如实记录的")
    ap.add_argument("--missing-all", action="store_true", help="verified 为空的")
    ap.add_argument("--domain", help="按路径片段过滤，如 09-GitHub")
    ap.add_argument("--stats", action="store_true", help="总览")
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()

    rows = load()
    if a.domain:
        rows = [r for r in rows if a.domain in r["rel"]]

    if a.stats or not any([a.missing, a.has, a.derived, a.live, a.missing_all]):
        print("notes with provenance: %d / %d"
              % (sum(1 for r in rows if r["derived"] is not None), len(rows)))
        print("  derived:true  (回溯推断) : %d" % sum(1 for r in rows if r["derived"] is True))
        print("  derived:false (如实记录) : %d" % sum(1 for r in rows if r["derived"] is False))
        print("  verified == []           : %d"
              % sum(1 for r in rows if r["derived"] is not None and not r["verified"]))
        c = collections.Counter(v for r in rows for v in r["verified"])
        print()
        print("verified 手段分布:")
        for k, v in c.most_common():
            print("  %-14s %4d  (%4.1f%%)" % (k, v, 100.0 * v / max(len(rows), 1)))
        m = collections.Counter(r["model"] for r in rows)
        print()
        print("model:")
        for k, v in m.most_common():
            print("  %-18s %4d" % (k, v))
        return

    sel = rows
    if a.derived:
        sel = [r for r in sel if r["derived"] is True]
    if a.live:
        sel = [r for r in sel if r["derived"] is False]
    if a.missing:
        sel = [r for r in sel if a.missing not in r["verified"]]
    if a.has:
        sel = [r for r in sel if a.has in r["verified"]]
    if a.missing_all:
        sel = [r for r in sel if not r["verified"]]

    print("matched %d note(s)%s" % (len(sel), "" if len(sel) <= a.limit else
                                    " (showing first %d)" % a.limit))
    print("-" * 70)
    for r in sel[:a.limit]:
        print("%s  %s" % (r["created"], r["rel"][:100]))


if __name__ == "__main__":
    main()
