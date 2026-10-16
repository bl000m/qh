"""Version lineage/review integrity, not validation of semantic truth."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "qh33_v2_tests", ROOT / "scripts/evaluate_qh33_v2.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b, cls.cases, cls.rubric = module.load_benchmark()
        cls.units = {u["id"]: u for u in cls.b["units"]}

    def test_v1_preserved_and_all_74_ids_evidence_assets_retained(self):
        parent, _ = module.v1.load_benchmark()
        self.assertEqual(self.b["cases"], parent["cases"])
        self.assertEqual(set(self.units), {u["id"] for u in parent["units"]})
        self.assertEqual(len(self.units), 74)
        for prefix in ("parent", "reassessment", "evaluator_v1"):
            self.assertEqual(
                module.file_hash(ROOT / self.b["lineage"][prefix + "_path"]),
                self.b["lineage"][prefix + "_file_sha256"],
            )

    def test_historical_exclusions_remain_reconstructible_not_passes(self):
        rows = [
            u
            for u in self.b["units"]
            if u["coverage_scope"] == "historical_reconstructible"
        ]
        self.assertEqual(len(rows), 2)
        for u in rows:
            self.assertTrue(all(v == "n/a" for v in u["draft_ratings"].values()))
            e = u["source_evidence"]
            self.assertEqual(
                self.cases[u["case"]]["source"]["content"][e["start"] : e["end"]],
                e["quote"],
            )
        result = module.evaluate(self.b, self.cases)
        coverage = result["provisional_assistant_metrics"]["source_proposition"][
            "dimensions"
        ]["active_coverage"]
        self.assertEqual(coverage["assessed_denominator"], 44)
        self.assertEqual(
            (coverage["pass"], coverage["partial"], coverage["fail"], coverage["n/a"]),
            (41, 1, 2, 2),
        )

    def test_d1_wording_and_d3_positive_controls_do_not_depend_on_fixture_name(self):
        self.assertIn("prevista", self.units["evolving.trial_duration"]["meaning"])
        self.assertIn(
            "preferirebbe", self.units["personal.temporary_avoidance"]["meaning"]
        )
        self.assertIn("non sappiamo", self.units["personal.ask_intent"]["meaning"])
        self.assertEqual(
            self.units["control.conditional_es.good"]["draft_ratings"][
                "active_coverage"
            ],
            "partial",
        )
        self.assertEqual(
            self.units["control.conditional_es.good"]["draft_ratings"]["negation"],
            "fail",
        )
        for name in ("lifecycle_de", "future_intent_en", "past_completed_it"):
            self.assertEqual(
                self.units[f"control.{name}.good"]["draft_ratings"]["temporality"],
                "partial",
            )

    def test_d4_citation_quality_and_semantic_support_stay_separate(self):
        a = self.units["control.negation_en.mutated"]["draft_ratings"]
        b = self.units["control.provenance_unicode.mutated"]["draft_ratings"]
        self.assertEqual(
            (a["semantic_support"], a["citation_traceability"]), ("fail", "pass")
        )
        self.assertEqual(
            (b["semantic_support"], b["citation_traceability"]), ("pass", "fail")
        )
        result = module.evaluate(self.b, self.cases)
        self.assertEqual(
            result["original_locator_metrics_unchanged"]["exact_spans"], 23
        )
        self.assertEqual(
            result["citation_resolution_diagnostics"]["multilingual"]["batch"],
            "rejected_whole_batch",
        )
        for group in result["provisional_assistant_metrics"].values():
            self.assertEqual(set(group["dimensions"]), set(module.DIMENSIONS))
            self.assertNotIn("provenance", group["dimensions"])

    def test_decision_approval_never_attests_personal_review(self):
        result = module.evaluate(self.b, self.cases)
        self.assertEqual(
            self.b["owner_decisions"]["approved"], ["D1", "D2", "D3", "D4", "D5"]
        )
        self.assertIsNone(result["human_review"]["metrics"])
        self.assertEqual(result["human_review"]["accepted_units"], 0)
        self.assertFalse(result["human_review"]["identity_verified_by_tool"])
        review = module.review_template(self.b)
        self.assertIsNone(review["reviewer"])
        self.assertIsNone(review["reviewed_at"])
        self.assertIsNone(review["independent_of_assistant_author"])
        self.assertFalse(review["reference_completeness_checked"])
        self.assertFalse(review["candidate_payloads_checked"])
        for row in review["units"]:
            self.assertEqual(row["decision"], "pending")
            self.assertTrue(all(v is None for v in row["ratings"].values()))

    def accepted_test_review(self):
        r = module.review_template(self.b)
        for row in r["units"]:
            row.update(
                decision="accept",
                ratings=deepcopy(self.units[row["id"]]["draft_ratings"]),
            )
        r.update(
            reviewer="SYNTHETIC TEST ONLY",
            reviewed_at="2030-01-01T00:00:00Z",
            independent_of_assistant_author=True,
            reference_completeness_checked=True,
            candidate_payloads_checked=True,
        )
        return r

    def test_each_actual_attestation_and_every_unit_still_required(self):
        for field, value in {
            "reviewer": None,
            "reviewed_at": None,
            "independent_of_assistant_author": None,
            "reference_completeness_checked": False,
            "candidate_payloads_checked": False,
        }.items():
            with self.subTest(field=field):
                r = self.accepted_test_review()
                r[field] = value
                self.assertIsNone(module.human_review(self.b, r)["metrics"])
        r = self.accepted_test_review()
        r["units"][0]["decision"] = "changes_requested"
        self.assertIsNone(module.human_review(self.b, r)["metrics"])
        r["units"][0]["decision"] = "pending"
        self.assertIsNone(module.human_review(self.b, r)["metrics"])

    def test_existing_protocol_records_only_test_declared_completion_not_identity(self):
        # Exercising the gate in memory is not a real review and is never archived.
        result = module.human_review(self.b, self.accepted_test_review())
        self.assertEqual(result["status"], "reviewer_declared_complete")
        self.assertFalse(result["identity_verified_by_tool"])
        self.assertEqual(result["required_units"], 74)
        self.assertIsNotNone(result["metrics"])

    def test_stale_version_rubric_and_changed_applicability_fail_closed(self):
        for mode in (
            "version",
            "hash",
            "rubric",
            "duplicate",
            "missing",
            "applicability",
            "v1_names",
        ):
            with self.subTest(mode=mode):
                r = self.accepted_test_review()
                if mode == "version":
                    r["benchmark_version"] = 1
                if mode == "hash":
                    r["benchmark_sha256"] = "stale"
                if mode == "rubric":
                    r["rubric_sha256"] = "stale"
                if mode == "duplicate":
                    r["units"].append(deepcopy(r["units"][0]))
                if mode == "missing":
                    r["units"].pop()
                if mode == "applicability":
                    r["units"][0]["ratings"] = {d: "n/a" for d in module.DIMENSIONS}
                if mode == "v1_names":
                    r["units"][0]["ratings"]["semantic"] = r["units"][0]["ratings"].pop(
                        "semantic_support"
                    )
                with self.assertRaises(ValueError):
                    module.human_review(self.b, r)
        with self.assertRaises(ValueError):
            module.human_review(
                self.b, module.v1.review_template(module.v1.load_benchmark()[0])
            )

    def test_lineage_capture_annotation_and_false_approval_mutations_rejected(self):
        for mode in ("parent", "case", "rating", "source", "meaning", "scope", "owner"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                b = deepcopy(self.b)
                if mode == "parent":
                    b["lineage"]["parent_file_sha256"] = "wrong"
                if mode == "case":
                    b["cases"][0]["output"]["sha256"] = "wrong"
                if mode == "rating":
                    b["units"][0]["draft_ratings"]["semantic_support"] = "fail"
                if mode == "source":
                    b["units"][0]["source_evidence"]["quote"] = "invented"
                if mode == "meaning":
                    b["units"][0]["meaning"] = "unsupported revision"
                if mode == "scope":
                    b["units"][0]["coverage_scope"] = "historical_reconstructible"
                if mode == "owner":
                    b["owner_decisions"]["personal_review_attestations"] = "complete"
                path = Path(temp) / "benchmark.json"
                path.write_text(json.dumps(b))
                with self.assertRaises(ValueError):
                    module.load_benchmark(path)

    def test_compact_matrix_has_every_id_and_targets_with_critical_attention(self):
        docs = module.render(self.b, self.cases, self.rubric)
        matrix = docs["review-matrix.it.md"]
        for id in self.units:
            self.assertEqual(matrix.count("[" + id + "](unit-details.it.md#"), 1)
        for id in (
            "multilingual.discount_applied",
            "multilingual.initial_tax_uncertainty",
            "control.conditional_es.good",
        ):
            self.assertIn("| ★ [" + id + "]", matrix)
        for name, content in docs.items():
            for target, anchor in re.findall(r"\]\(([^()#]+\.md)#([^()]+)\)", content):
                self.assertIn(
                    'id="' + anchor + '"', docs[target], (name, target, anchor)
                )
        payloads = re.findall(r"```json\n(.*?)\n```", docs["case-payloads.it.md"], re.S)
        self.assertEqual(
            [json.loads(x) for x in payloads],
            [c["output"] for c in self.cases.values()],
        )
        self.assertEqual(
            len(re.findall(r"^## Fonte ", docs["case-payloads.it.md"], re.M)), 14
        )
        self.assertEqual(
            docs["case-payloads.it.md"].count("Identità, turni e metadati originali"),
            14,
        )

    def test_cli_new_directory_and_invalid_review_never_emit_human_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "packet"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/evaluate_qh33_v2.py"),
                    "--out",
                    str(out),
                ],
                check=True,
                capture_output=True,
            )
            m = json.loads((out / "metrics.json").read_text())
            self.assertIsNone(m["human_review"]["metrics"])
            self.assertEqual(m["new_inference_requests"], 0)
            bad = Path(temp) / "bad.json"
            bad.write_text("{}")
            failed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/evaluate_qh33_v2.py"),
                    "--out",
                    str(Path(temp) / "absent"),
                    "--review",
                    str(bad),
                ],
                capture_output=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((Path(temp) / "absent").exists())


if __name__ == "__main__":
    unittest.main()
