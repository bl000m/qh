"""Verify derived artifacts against frozen originals, offline with standard library."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "qh8-mistral-20261016"


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


if __name__ == "__main__":
    baseline = json.loads((ORIGINAL / "manifest.json").read_text())
    for name, expected in baseline["files_sha256"].items():
        assert hashlib.sha256((ORIGINAL / name).read_bytes()).hexdigest() == expected
    before_results = {
        r["case"]: r for r in json.loads((ROOT / "before-results.json").read_text())
    }
    after_results = {
        r["case"]: r for r in json.loads((ROOT / "after-results.json").read_text())
    }
    rows = []
    for case in ["work", "evolving", "personal", "multilingual"]:
        source = json.loads((ORIGINAL / case / "source.json").read_text())
        original = json.loads((ORIGINAL / case / "output.json").read_text())
        resolution = json.loads((ROOT / case / "citation-resolution.json").read_text())
        assert resolution["original_output_sha256"] == digest(original)
        original_refs = [e for i in original["items"] for e in i.get("evidence", [])]
        before = sum(
            source["content"][e["start"] : e["end"]] == e["quote"]
            for e in original_refs
        )
        if case == "multilingual":
            assert (
                resolution["status"] == "REJECTED"
                and resolution["derived_output_sha256"] is None
            )
            assert [i["item_index"] for i in resolution["issues"]] == [6, 7, 8]
            assert not (ROOT / case / "derived-output.json").exists()
            assert not (ROOT / case / "canonical.json").exists()
            assert after_results[case]["rejected_scope_versions"] == {
                "desired": 0,
                "applied": 0,
            }
            assert (
                after_results[case]["items"] == 0
                and after_results[case]["source_retained"]
            )
            rows.append(
                dict(
                    case=case,
                    original_exact_spans=before,
                    citations=len(original_refs),
                    original_valid=before_results[case]["raw_validation"] == "PASS",
                    derived_valid=after_results[case]["raw_validation"] == "PASS",
                    corrected_spans=0,
                    missing_evidence_items=3,
                    proposed_revisions=0,
                )
            )
            continue
        derived = json.loads((ROOT / case / "derived-output.json").read_text())
        checkpoint = json.loads((ROOT / case / "checkpoint.json").read_text())
        assert checkpoint["output"] == derived
        assert (
            checkpoint["extraction_key"]
            == resolution["derived_extraction_key"]
            != "mistral-initial-v1"
        )
        assert resolution["derived_output_sha256"] == digest(derived)
        assert resolution["input_sha256"] == digest(
            {
                k: source[k]
                for k in (
                    "id",
                    "source_id",
                    "context_space_id",
                    "revision_no",
                    "content",
                    "origin",
                )
            }
        )
        restore = deepcopy(derived)
        corrected = 0
        for index, (item, old) in enumerate(
            zip(derived["items"], original["items"], strict=True)
        ):
            for ei, (e, oe) in enumerate(
                zip(item["evidence"], old["evidence"], strict=True)
            ):
                assert e["source_revision_id"] == source["id"]
                assert (
                    source["content"][e["start"] : e["end"]]
                    == e["quote"]
                    == oe["quote"]
                )
                occurrences = [
                    (t["start"] + m.start(), t["start"] + m.start() + len(e["quote"]))
                    for t in source["origin"]["turns"]
                    for m in re.finditer(
                        "(?=" + re.escape(e["quote"]) + ")",
                        source["content"][t["start"] : t["end"]],
                    )
                ]
                assert occurrences == [(e["start"], e["end"])]
                corrected += (e["start"], e["end"]) != (oe["start"], oe["end"])
                restore["items"][index]["evidence"][ei].update(
                    start=oe["start"], end=oe["end"]
                )
        assert restore == original  # No semantic/candidate/property/quote change.
        assert corrected == sum(r["changed"] for r in resolution["citations"])
        canonical = json.loads((ROOT / case / "canonical.json").read_text())
        revisions = canonical["export"]["understanding_item_revisions"]
        assert len(revisions) == len(derived["items"])
        assert all(
            r["validation_state"] == "proposed"
            and r["current_revision_id"] is None
            and r["validated_by"] is None
            for r in revisions
        )
        assert (
            canonical["foreign_subject_denied"] and canonical["sync_state"] == "ready"
        )
        rows.append(
            dict(
                case=case,
                original_exact_spans=before,
                citations=len(original_refs),
                original_valid=before_results[case]["raw_validation"] == "PASS",
                derived_valid=after_results[case]["raw_validation"] == "PASS",
                corrected_spans=corrected,
                missing_evidence_items=0,
                proposed_revisions=len(revisions),
            )
        )
    print(
        json.dumps(
            dict(
                original_accepted_batches=sum(r["original_valid"] for r in rows),
                derived_accepted_batches=sum(r["derived_valid"] for r in rows),
                corrected_spans=sum(r["corrected_spans"] for r in rows),
                external_inference_requests=0,
                cases=rows,
            ),
            indent=2,
        )
    )
