#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_pipeline.py — WB-02 正式轮（pipeline-approved）实际处理脚本
pharma-research-workflow (Plan -> Execute -> Verify) 的可复算执行体。

用途：对 examples/pipeline/ 的合成管线材料做真实读取 / 筛选 / 去重 / 阶段排序 / 核对，
产出资产表与来源矩阵的机器可验证数据，并打印审计项供 evidence-review.md 引用。

本轮相对预演轮（validation/pipeline/process_pipeline.py）的修复：
  - 预演脚本用「遍历行序里最后一个不同 highest_phase 值」决定历史最高阶段，
    会以较低阶段覆盖较高阶段。示例：截点含 R007(2026-10-11) 时，
    DEMO-003 current=preclinical 正确，但 highest_phase 会错序回成 discovery。
  - 本脚本改为按【明确阶段序】在窗口内记录里取历史最高：
        PHASE_ORDER = {"discovery": 0, "preclinical": 1, "phase_1": 2}
    未知/表外阶段值 -> 明确拒绝（抛错，退出码 3），不静默参与排序。
    `discontinued` 属 dev_status 语义，不作为阶段值参与排序。
  - 当前状态(dev_status)仍由窗口内【最新来源】决定，与 highest_phase 分离。

设计口径（策略 A：当前快照）：
  - 截点 cutoff = 2026-10-09（可覆盖，用于参数敏感性与边界复核）
  - 靶点 = DemoTarget-A（其余靶点排除）
  - 地区不限；适应症不限；全部模态；全部当前状态（含停研）
  - 按 asset_id 判定"同一资产"，别名/重复记录合并为一项
  - 当前状态(dev_status) = source_date <= cutoff 的最新记录决定
  - highest_phase = 窗口内记录按明确阶段序取历史最高
  - source_date > cutoff 的记录不得回填到过去（不进入 current 或 highest_phase）

约束：只读输入；不写回 examples/；不联网；不提交 Git。
"""

import argparse
import csv
import hashlib
import io
import json
import os
import sys

# ---- 冻结的输入契约（SHA256 在 main 中现场复算，不信任硬编码） ----
FILES = {
    "assets": "examples/pipeline/assets.csv",
    "updates": "examples/pipeline/asset_updates.csv",
}
INPUT_SHA_EXPECTED = {
    "examples/pipeline/assets.csv": "fbb7663309855682cb240b7d601e9b7fcf3f15fb7a12d3e8ecd6a0a21974f4a3",
    "examples/pipeline/asset_updates.csv": "4f62c4ec3ccf38af44cbb84081810aea75ad2d27020936162b020372a0a3164c",
    "examples/pipeline/source-provenance.md": "26372b53aca68f2647e5550ef19e06ce8ec49d9b8cbd79311613871580613baa",
}
DEFAULT_CUTOFF = "2026-10-09"
TARGET = "DemoTarget-A"
FIELDS = ["record_id", "source_id", "source_date", "asset_id", "drug", "alias",
          "target", "indication", "modality", "organization", "country",
          "highest_phase", "dev_status"]

# 明确阶段序（由低到高）。仅本 fixture 明确定义的阶段值；表外值一律拒绝。
PHASE_ORDER = {"discovery": 0, "preclinical": 1, "phase_1": 2}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_records(repo_root):
    """读取两份 CSV，记录真实行号（含表头）。返回 (records, raw_lines)."""
    records = []
    raw_lines = {}
    for key in ("assets", "updates"):
        rel = FILES[key]
        abspath = os.path.join(repo_root, rel)
        with open(abspath, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        raw_lines[rel] = text.splitlines()
        reader = csv.DictReader(io.StringIO(text))
        for i, row in enumerate(reader, start=2):  # 第 1 行为表头
            rec = {k: (row.get(k) or "").strip() for k in FIELDS}
            rec["_file"] = rel
            rec["_line"] = i
            records.append(rec)
    return records, raw_lines


def phase_rank(value, asset_id, record_id):
    """返回明确阶段序。未知/表外阶段值 -> 明确拒绝（抛 ValueError）。"""
    if value not in PHASE_ORDER:
        raise ValueError(
            f"未知阶段值 highest_phase={value!r} (asset_id={asset_id}, record_id={record_id})；"
            f"允许值={sorted(PHASE_ORDER, key=PHASE_ORDER.get)}。"
            f"按规则明确拒绝，不静默参与排序。")
    return PHASE_ORDER[value]


def process(records, cutoff, target):
    """执行 筛选 -> 去重/合并 -> 当前状态判定 -> 明确阶段序历史最高。返回结构化结果与审计项。"""
    audit = {
        "cutoff": cutoff,
        "target": target,
        "total_records": len(records),
        "target_mismatch_excluded": [],   # 靶点不符
        "future_after_cutoff": [],        # 截点之后（不回填）
        "duplicate_alias_groups": [],     # 重复别名
        "same_day_conflicts": [],         # 同日记录（含一致与矛盾）
        "unresolved_conflicts": [],       # 同日【矛盾】状态：保持待核查，不产出确定当前状态
        "phase_order": PHASE_ORDER,       # 本轮明确阶段序（供证据审查引用）
    }
    unresolved = audit["unresolved_conflicts"]  # 同一列表引用（append 会同步进 audit）

    # 1) 靶点筛选（并记录靶点不符被排除的行）
    target_records = []
    for r in records:
        if r["target"] != target:
            audit["target_mismatch_excluded"].append(
                {"record_id": r["record_id"], "asset_id": r["asset_id"],
                 "target": r["target"], "file": r["_file"], "line": r["_line"]})
        else:
            target_records.append(r)

    # 2) 时间截点筛选：> cutoff 记录标记为"未来更新"，不参与当前状态/历史最高判定
    in_window, future = [], []
    for r in target_records:
        if r["source_date"] > cutoff:
            future.append(r)
            audit["future_after_cutoff"].append(
                {"record_id": r["record_id"], "asset_id": r["asset_id"],
                 "source_date": r["source_date"], "file": r["_file"],
                 "line": r["_line"]})
        else:
            in_window.append(r)

    # 3) 按 asset_id 分组（同一资产 = 同一 asset_id，别名/重复合并）
    groups = {}
    for r in in_window:
        groups.setdefault(r["asset_id"], []).append(r)

    assets = []
    for asset_id, rows in groups.items():
        drugs = sorted({x["drug"] for x in rows})
        aliases = sorted({x["alias"] for x in rows})
        rid_span = [x["record_id"] for x in sorted(rows, key=lambda z: (z["source_date"], z["_line"]))]
        if len(rows) > 1:
            pairs = []
            for x in rows:
                pairs.append((x["record_id"], x["drug"], x["alias"], x["_line"]))
            audit["duplicate_alias_groups"].append(
                {"asset_id": asset_id, "rows": pairs})

        # 当前状态：source_date 最大者。
        # 本轮修复（对应 Review Focus 第 3 条）：最新日期同一资产若出现【互相矛盾】的
        # dev_status，必须报告 资产/日期/record_ids/来源/冲突状态 并【停止给出确定当前状态】——
        # 不得挑某一行（如行序更后者）当作确定答案。一致的重复别名仍正常合并。
        max_date = max(x["source_date"] for x in rows)
        latest = [x for x in rows if x["source_date"] == max_date]
        conflict = False
        if len(latest) > 1:
            devs = {x["dev_status"] for x in latest}
            entry = {
                "asset_id": asset_id, "source_date": max_date,
                "statuses": sorted(devs),
                "records": [
                    {"record_id": x["record_id"], "source_id": x["source_id"],
                     "dev_status": x["dev_status"], "file": x["_file"], "line": x["_line"]}
                    for x in sorted(latest, key=lambda z: z["_line"])],
                "record_ids": [x["record_id"] for x in latest],
            }
            if len(devs) > 1:
                # 矛盾：标记 unresolved、不产出确定 current
                entry["resolved"] = False
                entry["reason"] = "same-day contradictory dev_status; not picking a row"
                audit["same_day_conflicts"].append(entry)
                unresolved.append(entry)
                conflict = True
            else:
                # 同日重复但状态一致：正常合并，当前状态可取（不视为矛盾）。
                # 取行序更后者作为代表（与预演轮一致，确定性）。
                entry["resolved"] = True
                entry["reason"] = "same-day duplicate statuses consistent; merged"
                audit["same_day_conflicts"].append(entry)
        # 一致的重复：取行序代表；矛盾（conflict）时为 None
        current = None if conflict else sorted(latest, key=lambda z: z["_line"])[-1]

        # 历史最高阶段（本轮修复）：按【明确阶段序】在窗口内记录取历史最高。
        # 未知阶段值由 phase_rank 明确拒绝（不静默参与）。
        phase_values = sorted({x["highest_phase"] for x in rows})
        ranked = []
        for x in rows:
            ranked.append((phase_rank(x["highest_phase"], asset_id, x["record_id"]),
                           x["highest_phase"], x["record_id"], x["source_date"], x["_line"]))
        ranked.sort(key=lambda t: (t[0], t[1]))  # 阶段序最高者最后
        highest_phase = ranked[-1][1]
        highest_phase_record_id = ranked[-1][2]
        highest_phase_source_date = ranked[-1][3]

        # 状态变更历史（用于演示"停研"来源）
        timeline = []
        for x in sorted(rows, key=lambda z: (z["source_date"], z["_line"])):
            timeline.append({
                "record_id": x["record_id"], "source_id": x["source_id"],
                "source_date": x["source_date"], "dev_status": x["dev_status"],
                "highest_phase": x["highest_phase"],
                "file": x["_file"], "line": x["_line"]})

        assets.append({
            "asset_id": asset_id,
            "drug": current["drug"] if current else None,
            "alias": current["alias"] if current else None,
            "indication": current["indication"] if current else None,
            "modality": current["modality"] if current else None,
            "organization": current["organization"] if current else None,
            "country": current["country"] if current else None,
            "current_status": current["dev_status"] if current else None,
            "current_status_source_date": current["source_date"] if current else None,
            "current_status_record_id": current["record_id"] if current else None,
            "current_status_source_id": current["source_id"] if current else None,
            "highest_phase": highest_phase,
            "highest_phase_record_id": highest_phase_record_id,
            "highest_phase_source_date": highest_phase_source_date,
            "phase_values_seen": phase_values,
            "record_ids_merged": rid_span,
            "timeline": timeline,
            "same_day_conflict": conflict,
            "current_status_resolved": not conflict,
        })

    assets.sort(key=lambda a: a["asset_id"])
    return assets, audit, unresolved


def print_report(assets, audit, acceptance_expected=None):
    print("=" * 72)
    print("WB-02 管线处理报告（正式轮 pipeline-approved）")
    print("=" * 72)
    print(f"截点 cutoff        : {audit['cutoff']}")
    print(f"目标靶点 target    : {audit['target']}")
    print(f"阶段序 PHASE_ORDER : {audit['phase_order']}")
    print(f"输入记录总数       : {audit['total_records']}")
    print(f"靶点不符排除       : {len(audit['target_mismatch_excluded'])} "
          f"{[(x['record_id'], x['asset_id'], x['target']) for x in audit['target_mismatch_excluded']]}")
    print(f"截点之后(不回填)   : {len(audit['future_after_cutoff'])} "
          f"{[(x['record_id'], x['asset_id'], x['source_date']) for x in audit['future_after_cutoff']]}")
    print(f"重复别名组         : {[(g['asset_id'], [p[0] for p in g['rows']]) for g in audit['duplicate_alias_groups']]}")
    print(f"同日记录(含一致)   : {audit['same_day_conflicts']}")
    print("-" * 72)
    unresolved = audit["unresolved_conflicts"]
    if unresolved:
        print(f"!! 同日矛盾状态 {len(unresolved)} 项 —— 保持待核查，不产出确定当前状态：")
        for c in unresolved:
            print(f"   asset={c['asset_id']} date={c['source_date']} "
                  f"statuses={c['statuses']} records={[r['record_id'] for r in c['records']]}")
            for r in c["records"]:
                print(f"       - {r['record_id']} | source_id={r['source_id']} | "
                      f"dev_status={r['dev_status']} | {r['file']}:{r['line']}")
        print("   => 处置：明确拒绝为确定答案；本资产当前状态标记 unresolved，退出码 3。")
        print("   => 注意：这是数据冲突导致的待核查，不等于'没有该管线'。")
        print("-" * 72)
    print(f"窗口内靶点资产数   : {len(assets)}")
    for a in assets:
        print(f"  {a['asset_id']} | drug={a['drug']} alias={a['alias']} | "
              f"当前={a['current_status']} (R={a['current_status_record_id']} @{a['current_status_source_date']}) | "
              f"highest_phase={a['highest_phase']} (R={a['highest_phase_record_id']} @{a['highest_phase_source_date']}) | "
              f"合并={a['record_ids_merged']}")
    print("-" * 72)
    got = {a["asset_id"]: (a["current_status"], a["highest_phase"]) for a in assets}
    print("GOT:", json.dumps(got, ensure_ascii=False))
    if audit["unresolved_conflicts"]:
        # 存在同日矛盾：不给出确定当前状态，也不做 PASS/FAIL 断言。
        print("RESULT: UNRESOLVED_CONFLICT")
        return "unresolved"
    if acceptance_expected is None:
        print("ACCEPTANCE: 参数敏感性/边界运行（未做固定 fixture 断言）")
        return None
    print(f"ACCEPTANCE expected: {json.dumps(acceptance_expected, ensure_ascii=False)}")
    ok = (got == acceptance_expected)
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


# 固定 fixture 验收真值（仅 cutoff=2026-10-09 + target=DemoTarget-A 时套用；合成材料明示值）
ACCEPTANCE = {
    ("2026-10-09", "DemoTarget-A"): {
        "DEMO-001": ("preclinical", "preclinical"),
        "DEMO-002": ("discontinued", "phase_1"),
        "DEMO-003": ("discovery", "discovery"),
    },
    # 边界复核：截点 2026-10-11 含 R007 -> DEMO-003 current 与最高阶段均为 preclinical
    ("2026-10-11", "DemoTarget-A"): {
        "DEMO-001": ("preclinical", "preclinical"),
        "DEMO-002": ("discontinued", "phase_1"),
        "DEMO-003": ("preclinical", "preclinical"),
    },
    # 参数敏感性：改变靶点 -> 仅剩 DEMO-004（可预期，非"事实失败"）
    ("2026-10-09", "DemoTarget-B"): {
        "DEMO-004": ("preclinical", "preclinical"),
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    ap.add_argument("--target", default=TARGET)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--verify-hashes", action="store_true")
    args = ap.parse_args()

    repo_root = os.path.abspath(args.repo_root)

    if args.verify_hashes:
        print("--- 输入 SHA256 现场复算 ---")
        all_ok = True
        for rel, exp in INPUT_SHA_EXPECTED.items():
            got = sha256_file(os.path.join(repo_root, rel))
            ok = (got == exp)
            all_ok = all_ok and ok
            print(f"{'OK ' if ok else 'BAD'} {rel}\n    sha256={got}")
        print("HASH_RESULT:", "PASS" if all_ok else "FAIL")
        if not all_ok:
            return 2

    records, raw_lines = load_records(repo_root)
    try:
        assets, audit, unresolved = process(records, args.cutoff, args.target)
    except ValueError as exc:
        print("PHASE_ERROR:", exc)
        print("RESULT: ERROR")
        return 3

    acceptance_expected = ACCEPTANCE.get((args.cutoff, args.target))
    ok = print_report(assets, audit, acceptance_expected)

    if args.json_out:
        if ok == "unresolved":
            acc_res = "unresolved"
        elif ok is None:
            acc_res = "n/a"
        else:
            acc_res = "PASS" if ok else "FAIL"
        payload = {"audit": audit, "assets": assets,
                   "acceptance_expected": acceptance_expected,
                   "acceptance_result": acc_res,
                   "input_sha256": {rel: sha256_file(os.path.join(repo_root, rel))
                                    for rel in INPUT_SHA_EXPECTED}}
        with open(os.path.join(repo_root, args.json_out), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"[json] 写出 {args.json_out}")

    if ok == "unresolved":
        return 3   # 数据冲突保持待核查：明确异常退出，不当成"没有该管线"
    if ok is None:
        return 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
