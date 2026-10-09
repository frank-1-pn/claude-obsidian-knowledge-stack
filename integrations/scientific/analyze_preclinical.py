#!/usr/bin/env python3
"""Offline synthetic endpoint analysis plus the pinned upstream NCA CLI.

This demonstrator deliberately accepts only the declared complete, independent
endpoint fixture design. It must not silently reinterpret real animal studies.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import scipy
from scipy import stats

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def read_rows(path: Path, columns: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not columns.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name}: missing required columns {sorted(columns)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty input")
    return rows


def finite(value: str, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field}: non-finite value")
    return number


def holm(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted


def analyze_efficacy(path: Path) -> dict:
    rows = read_rows(path, {"animal_id", "group", "tumor_volume_mm3", "body_weight_change_pct"})
    groups: dict[str, list[dict]] = {name: [] for name in ("vehicle", "low", "high")}
    seen = set()
    for row in rows:
        identifier = row["animal_id"].strip()
        if not identifier or identifier in seen:
            raise ValueError("each animal_id must appear exactly once; repeated measures need another model")
        seen.add(identifier)
        if row["group"] not in groups:
            raise ValueError("this demo permits only vehicle, low and high groups")
        tumor = finite(row["tumor_volume_mm3"], "tumor_volume_mm3")
        weight = finite(row["body_weight_change_pct"], "body_weight_change_pct")
        if tumor <= 0 or weight <= -100:
            raise ValueError("nonpositive tumor volume or impossible body weight change")
        groups[row["group"]].append({"tumor": tumor, "weight": weight})
    arrays = {}
    summaries = {}
    for name, data in groups.items():
        values = np.asarray([row["tumor"] for row in data], dtype=float)
        if len(values) < 3 or np.var(values, ddof=1) <= 0:
            raise ValueError("each group needs at least 3 animals and nonzero variance")
        arrays[name] = values
        diagnostic = stats.shapiro(values) if len(values) <= 5000 else None
        summaries[name] = {
            "n_animals": len(values), "mean_mm3": float(values.mean()),
            "sd_mm3": float(values.std(ddof=1)),
            "shapiro_p_descriptive": float(diagnostic.pvalue) if diagnostic else None,
            "mean_body_weight_change_pct": float(np.mean([row["weight"] for row in data])),
            "animals_with_weight_loss_ge_10pct": sum(row["weight"] <= -10 for row in data),
        }
    comparisons = []
    control = arrays["vehicle"]
    for name in ("low", "high"):
        treated = arrays[name]
        test = stats.ttest_ind(treated, control, equal_var=False, alternative="two-sided")
        ci = test.confidence_interval(confidence_level=0.95)
        difference = float(treated.mean() - control.mean())
        comparisons.append({
            "contrast": f"{name}-vehicle", "mean_difference_mm3": difference,
            "mean_difference_ci95_unadjusted_mm3": [float(ci.low), float(ci.high)],
            "relative_endpoint_reduction_pct": float(100 * (1 - treated.mean() / control.mean())),
            "welch_t": float(test.statistic), "welch_df": float(test.df),
            "p_raw": float(test.pvalue),
        })
    for comparison, adjusted in zip(comparisons, holm([row["p_raw"] for row in comparisons])):
        comparison["p_holm"] = adjusted
        comparison["reject_null_after_holm_at_0_05"] = adjusted < 0.05
    return {
        "experimental_unit": "animal; one prespecified endpoint per animal",
        "groups": summaries, "comparisons": comparisons,
        "analysis_plan": {
            "primary_endpoint": "synthetic terminal tumor_volume_mm3",
            "contrasts": ["low-vehicle", "high-vehicle"],
            "test": "two-sided independent Welch t-test, prespecified",
            "multiplicity": "Holm family-wise correction for the 2 prespecified contrasts",
            "ci": "95% pointwise mean-difference intervals; not simultaneous family intervals",
            "missing_data": "fail on missing, nonfinite or duplicate records; no deletion/imputation",
        },
        "limitations": [
            "Independence is a declared synthetic design assumption, not a normality-test conclusion.",
            "Shapiro p-values are descriptive; non-rejection does not prove normality.",
            "Endpoint reduction is not longitudinal tumor-growth inhibition (TGI).",
            "Body weight is descriptive tolerability context, not a toxicology/NOAEL assessment.",
            "Significance in invented data supplies no evidence about a real compound or disease.",
        ],
    }


def analyze_pk(path: Path) -> dict:
    rows = read_rows(path, {"id", "time", "conc"})
    seen = set()
    counts: dict[str, int] = {}
    for row in rows:
        identifier = row["id"].strip()
        if "blq" in row and row["blq"].strip().lower() not in ("", "0", "false", "no"):
            raise ValueError("BLQ-marked observations require a separately approved analysis plan; this demo refuses them")
        time = finite(row["time"], "time")
        concentration = finite(row["conc"], "conc")
        key = (identifier, time)
        if not identifier or key in seen or time < 0 or concentration < 0:
            raise ValueError("PK requires an ID, distinct nonnegative times and nonnegative concentration")
        seen.add(key)
        counts[identifier] = counts.get(identifier, 0) + 1
    if any(count < 4 for count in counts.values()):
        raise ValueError("each PK profile needs a peak plus 3 terminal samples")
    script = REPO / "vendor/scientific-agent-skills/skills/pkpd-modeling/scripts/nca.py"
    command = [sys.executable, "-B", str(script), "-i", str(path.resolve()), "--dose", "0.125",
               "--route", "extravascular", "--auc-method", "linup-logdown",
               "--lambda-z-window", "8-24", "--blq-rule", "missing", "--format", "json"]
    result = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=60)
    if result.returncode not in (0, 1):
        raise ValueError(f"upstream NCA rejected input: {result.stderr.strip()}")
    report = json.loads(result.stdout)
    return {
        "engine": "pinned K-Dense pkpd-modeling/scripts/nca.py",
        "exit_code": result.returncode, "report": report,
        "conventions": {"time_unit": "h", "concentration_unit": "mg/L", "dose_unit": "mg",
                        "dose_mg": 0.125, "auc_method": "linear-up/log-down",
                        "terminal_window_h": [8, 24], "blq": "none in fixture; numeric completeness enforced"},
        "limitations": [
            "Separate synthetic PK cohort: no animal-level exposure-response link to the efficacy cohort.",
            "Oral clearance and volume are apparent CL/F and V/F; F is not identified.",
            "A perfect synthetic terminal fit does not validate a real PK model or sampling design.",
            "Dose is illustrative arithmetic; no clinical dose or species safety inference.",
        ],
    }


def analyze(efficacy: Path, pk: Path) -> dict:
    upstream = json.loads((ROOT / "upstream-lock.json").read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0", "data_kind": "synthetic-preclinical-demo",
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
        "sources": {name: {"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                    for name, path in (("efficacy", efficacy), ("pk", pk))},
        "upstream_revision": upstream["revision"],
        "efficacy": analyze_efficacy(efficacy), "pk": analyze_pk(pk),
        "citation": "K-Dense Scientific Agent Skills; https://doi.org/10.48550/arXiv.2609.00065; see vendored CITATION.cff",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efficacy", type=Path, default=ROOT / "fixtures/efficacy.csv")
    parser.add_argument("--pk", type=Path, default=ROOT / "fixtures/pk.csv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = analyze(args.efficacy, args.pk)
        from jsonschema import validate
        validate(report, json.loads((ROOT / "output.schema.json").read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 2
    print(f"[OK] synthetic analysis written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
