"""Accounting/lineage guarantees; these tests do not validate semantic labels."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "qh33_evaluation", ROOT / "scripts/evaluate_qh33.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b, cls.cases = module.load_benchmark()

    def test_draft_and_human_metrics_never_conflate(self):
        result = module.evaluate(self.b, self.cases)
        self.assertIsNone(result["human_review"]["metrics"])
        self.assertEqual(result["human_review"]["accepted_units"], 0)
        self.assertEqual(
            result["original_locator_metrics"],
            {
                "candidates": 37,
                "supplied_citations": 34,
                "exact_spans": 23,
                "candidates_missing_evidence": 3,
            },
        )
        coverage = result["provisional_assistant_metrics"]["source_proposition"][
            "dimensions"
        ]["coverage"]
        self.assertEqual(
            (coverage["pass"], coverage["partial"], coverage["fail"]), (41, 1, 4)
        )
        self.assertEqual(coverage["assessed_denominator"], 46)

    def test_na_pending_and_disjoint_kinds_have_explicit_denominators(self):
        group = module.summarize(self.b["units"], {})
        semantic = group["source_proposition"]["dimensions"]["semantic"]
        self.assertEqual(semantic["pending"], 46)
        self.assertIsNone(semantic["pass_fraction"])
        self.assertEqual(group["control"]["units"], 20)
        self.assertEqual(group["extra_claim"]["units"], 3)
        self.assertEqual(group["output_annotation"]["units"], 5)

    def test_reordering_does_not_change_metrics(self):
        changed = deepcopy(self.b)
        changed["units"].reverse()
        a = module.evaluate(self.b, self.cases)
        b = module.evaluate(changed, self.cases)
        self.assertEqual(
            a["provisional_assistant_metrics"], b["provisional_assistant_metrics"]
        )
        self.assertNotEqual(a["benchmark_sha256"], b["benchmark_sha256"])

    def test_stale_duplicate_missing_and_incomplete_reviews_reject(self):
        base = module.review_template(self.b)
        for mode in ["hash", "duplicate", "missing", "incomplete", "applicability"]:
            with self.subTest(mode=mode):
                r = deepcopy(base)
                if mode == "hash":
                    r["benchmark_sha256"] = "wrong"
                if mode == "duplicate":
                    r["units"].append(deepcopy(r["units"][0]))
                if mode == "missing":
                    r["units"].pop()
                if mode in {"incomplete", "applicability"}:
                    r["units"][0]["decision"] = "accept"
                if mode == "applicability":
                    r["units"][0]["ratings"] = {d: "n/a" for d in module.DIMENSIONS}
                with self.assertRaises(ValueError):
                    module.human_review(self.b, r)

    def test_review_template_is_blank_and_never_auto_attests_identity(self):
        r = module.review_template(self.b)
        for row, u in zip(r["units"], self.b["units"], strict=True):
            self.assertEqual(row["decision"], "pending")
            self.assertTrue(all(v is None for v in row["ratings"].values()))
            row.update(decision="accept", ratings=deepcopy(u["draft_ratings"]))
        self.assertIsNone(module.human_review(self.b, r)["metrics"])
        # A test-supplied attestation exercises the import gate, not a real reviewer.
        r.update(
            reviewer="SYNTHETIC TEST ATTESTATION",
            reviewed_at="2030-01-01T00:00:00Z",
            independent_of_assistant_author=True,
            reference_completeness_checked=True,
            candidate_payloads_checked=True,
        )
        result = module.human_review(self.b, r)
        self.assertFalse(result["identity_verified_by_tool"])
        self.assertEqual(result["status"], "reviewer_declared_complete")
        r["units"][0]["decision"] = "changes_requested"
        self.assertIsNone(module.human_review(self.b, r)["metrics"])

    def test_modified_assets_labels_and_evidence_only_anchors_fail_before_scoring(self):
        for mode in [
            "asset",
            "anchor",
            "evidence_only",
            "duplicate",
            "rating",
            "source",
        ]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as t:
                b = deepcopy(self.b)
                if mode == "asset":
                    b["cases"][0]["output"]["sha256"] = "wrong"
                if mode == "anchor":
                    b["units"][0]["anchors"][0]["value_sha256"] = "wrong"
                if mode == "evidence_only":
                    b["units"][0]["anchors"][0]["pointer"] = "/items/0/evidence/0/quote"
                if mode == "duplicate":
                    b["units"].append(deepcopy(b["units"][0]))
                if mode == "rating":
                    b["units"][0]["draft_ratings"]["semantic"] = "probably"
                if mode == "source":
                    b["units"][0]["source_evidence"]["start"] += 1
                path = Path(t) / "benchmark.json"
                path.write_text(json.dumps(b))
                with self.assertRaises(ValueError):
                    module.load_benchmark(path, ROOT)

    def test_future_protocol_changes_one_variable_and_authorizes_nothing(self):
        protocol = module.future_protocol(self.cases)
        self.assertEqual(protocol["status"], "NOT AUTHORIZED / NOT EXECUTED")
        self.assertEqual(len(protocol["requests"]), 6)
        self.assertLessEqual(
            len(protocol["requests"]) + protocol["max_metadata_requests"],
            protocol["max_total_requests"],
        )
        for i in range(0, 6, 2):
            a, b = (
                deepcopy(protocol["requests"][i]),
                deepcopy(protocol["requests"][i + 1]),
            )
            self.assertNotEqual(
                a["payload"]["messages"][0]["content"],
                b["payload"]["messages"][0]["content"],
            )
            a["payload"]["messages"][0]["content"] = b["payload"]["messages"][0][
                "content"
            ]
            self.assertEqual(a["payload"], b["payload"])
            user = json.loads(a["payload"]["messages"][1]["content"])
            self.assertEqual(
                set(user), {"source_revision_id", "input_sha256", "text", "turns"}
            )
            self.assertLessEqual(a["conservative_input_bound"], 16000)

    def test_packet_exposes_full_payloads_but_does_not_supply_human_ratings(self):
        text = module.packet(self.b, self.cases)
        self.assertIn('"discount_applied": true', text)
        self.assertIn("Human decision/ratings: **pending**", text)
        self.assertNotIn('"draft_ratings"', text)
        self.assertEqual(len({c["source"]["sha256"] for c in self.b["cases"]}), 14)


if __name__ == "__main__":
    unittest.main()
