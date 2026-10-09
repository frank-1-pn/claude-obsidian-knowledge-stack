"""Numerical-oracle and invalid-input tests for the synthetic demo."""
import csv
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from jsonschema import validate, ValidationError
from scipy.stats import t

from analyze_preclinical import ROOT, analyze, analyze_efficacy, analyze_pk, holm
from verify_snapshot import verify


class ScientificPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze(ROOT / "fixtures/efficacy.csv", ROOT / "fixtures/pk.csv")

    def write_variant(self, source, mutate):
        with source.open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        mutate(rows)
        target = Path(self.temp.name) / source.name
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return target

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_schema_and_explicit_synthetic_scope(self):
        validate(self.report, json.loads((ROOT / "output.schema.json").read_text(encoding="utf-8")))
        self.assertEqual(self.report["data_kind"], "synthetic-preclinical-demo")
        self.assertEqual(self.report["efficacy"]["groups"]["vehicle"]["n_animals"], 8)
        self.assertTrue(any("no animal-level exposure-response" in text for text in self.report["pk"]["limitations"]))

    def test_welch_against_scalar_formula(self):
        # A separate scalar oracle from literal fixture values, not the analysis helper.
        vehicle = [460, 510, 490, 540, 520, 480, 560, 500]
        high = [270, 320, 300, 350, 330, 290, 340, 310]
        mean = lambda values: sum(values) / len(values)
        variance = lambda values: sum((value - mean(values))**2 for value in values) / (len(values) - 1)
        a, b = variance(high)/8, variance(vehicle)/8
        se = math.sqrt(a+b)
        df = (a+b)**2 / (a*a/7 + b*b/7)
        effect = mean(high) - mean(vehicle)
        result = self.report["efficacy"]["comparisons"][1]
        self.assertAlmostEqual(effect, -193.75)
        self.assertAlmostEqual(result["welch_t"], effect/se, places=11)
        self.assertAlmostEqual(result["welch_df"], df, places=11)
        self.assertAlmostEqual(result["p_raw"], 2*t.sf(abs(effect/se), df), places=13)
        self.assertAlmostEqual(result["mean_difference_ci95_unadjusted_mm3"][0], effect - t.ppf(0.975, df)*se, places=10)

    def test_holm_known_cases_and_order(self):
        actual = holm([0.03, 0.001, 0.02])
        for value, expected in zip(actual, [0.04, 0.003, 0.04]):
            self.assertAlmostEqual(value, expected)
        self.assertEqual(holm([0.8, 0.9]), [1.0, 1.0])

    def test_upstream_nca_analytic_terminal_truth(self):
        self.assertEqual(self.report["pk"]["exit_code"], 0)
        self.assertEqual(self.report["pk"]["report"]["findings"], [])
        tables = {row["title"]: row["rows"] for row in self.report["pk"]["report"]["tables"]}
        self.assertEqual(len(tables["per-subject parameters"]), 3)
        for profile in tables["per-subject parameters"]:
            self.assertAlmostEqual(profile["lambda_z"], math.log(2)/4, places=12)
            self.assertAlmostEqual(profile["t_half"], 4, places=12)
            self.assertEqual(profile["lambda_z_n"], 3)
            self.assertAlmostEqual(profile["auc_inf_obs"] - profile["auc_last"], profile["clast"]/(math.log(2)/4), places=12)
        # Independent integral of each exponential segment plus linear rising segments.
        times = [0, .5, 1, 2, 4, 8, 12, 24]
        values = [0, .05, .12, .10, .08, .04, .02, .0025]
        auc = 0
        for left, right, a, b in zip(times, times[1:], values, values[1:]):
            if a > b > 0:
                rate = math.log(a/b)/(right-left)
                auc += (a-b)/rate
            else:
                auc += (right-left)*(a+b)/2
        self.assertAlmostEqual(tables["per-subject parameters"][0]["auc_last"], auc, places=12)

    def test_duplicate_animal_rejected(self):
        path = self.write_variant(ROOT / "fixtures/efficacy.csv", lambda rows: rows.append(dict(rows[0])))
        with self.assertRaisesRegex(ValueError, "exactly once"):
            analyze_efficacy(path)

    def test_nonfinite_endpoint_rejected(self):
        path = self.write_variant(ROOT / "fixtures/efficacy.csv", lambda rows: rows[0].update(tumor_volume_mm3="nan"))
        with self.assertRaisesRegex(ValueError, "non-finite"):
            analyze_efficacy(path)

    def test_unknown_group_rejected(self):
        path = self.write_variant(ROOT / "fixtures/efficacy.csv", lambda rows: rows[0].update(group="ambiguous"))
        with self.assertRaisesRegex(ValueError, "permits only"):
            analyze_efficacy(path)

    def test_duplicate_pk_time_rejected(self):
        path = self.write_variant(ROOT / "fixtures/pk.csv", lambda rows: rows.append(dict(rows[1])))
        with self.assertRaisesRegex(ValueError, "distinct"):
            analyze_pk(path)

    def test_blq_not_silently_imputed(self):
        path = self.write_variant(ROOT / "fixtures/pk.csv", lambda rows: rows[1].update(conc="BLQ"))
        with self.assertRaises(ValueError):
            analyze_pk(path)

    def test_numeric_blq_flag_is_not_silently_dropped(self):
        def mark_blq(rows):
            for row in rows:
                row['blq'] = '0'
            rows[1]['blq'] = '1'
        path = self.write_variant(ROOT / 'fixtures/pk.csv', mark_blq)
        with self.assertRaisesRegex(ValueError, 'BLQ-marked'):
            analyze_pk(path)

    def test_duplicate_contrast_rejected_by_schema(self):
        modified = copy.deepcopy(self.report)
        modified['efficacy']['comparisons'][1]['contrast'] = 'low-vehicle'
        with self.assertRaises(ValidationError):
            validate(modified, json.loads((ROOT / 'output.schema.json').read_text(encoding='utf-8')))


    def test_invalid_terminal_fit_retains_upstream_findings(self):
        def replace_tail(rows):
            for row in rows:
                if row["id"] == "PK01" and float(row["time"]) >= 8:
                    row["conc"] = str(float(row["time"]) / 1000)
        path = self.write_variant(ROOT / "fixtures/pk.csv", replace_tail)
        pk = analyze_pk(path)
        self.assertEqual(pk["exit_code"], 1)
        self.assertTrue(any("lambda_z not estimable" in text for text in pk["report"]["findings"]))

    def test_vendor_byte_integrity(self):
        result = verify()
        self.assertEqual(result["skills"], 24)


if __name__ == "__main__":
    unittest.main()
