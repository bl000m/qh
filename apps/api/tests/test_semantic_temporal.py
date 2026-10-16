"""Existing evidence rule tightened; no model comprehension improvement claim."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "qh33_probe", ROOT / "scripts/evaluate_qh33.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture(scope="module")
def probes():
    b, cases = module.load_benchmark()
    return module.probe_engine(b, cases, "test"), cases


@pytest.mark.parametrize("index", range(13))
def test_complete_literal_timestamps_and_atomic_rejection(probes, index):
    result = probes[0]["temporal_literal_probes"][index]
    assert result["accepted"] is result["expected_accept"]
    if result["accepted"]:
        assert result["revisions"] == 2 and result["all_proposed"]
    else:
        assert result["revisions"] == 0 and result["source_retained"]


def test_originals_and_resolver_outcomes_do_not_become_semantic_certificates(probes):
    result, cases = probes
    original = ["work", "evolving", "personal", "multilingual"]
    assert sum(result["cases"][k]["original"]["accepted"] for k in original) == 1
    assert sum(result["cases"][k]["resolved"]["accepted"] for k in original) == 3
    assert (
        cases["multilingual"]["output"]["items"][4]["properties"]["discount_applied"]
        is True
    )
    assert result["cases"]["multilingual"]["resolved"]["revisions"] == 0
    assert result["provider_calls"] == 0


def test_semantically_mutated_controls_remain_proposed_not_confirmed(probes):
    result, _ = probes
    for name, case in result["cases"].items():
        if not name.startswith("control."):
            continue
        if name == "control.provenance_unicode.mutated":
            assert not case["resolved"]["accepted"] and not case["original"]["accepted"]
        else:
            # Reveals the remaining entailment gap; never a semantic PASS assertion.
            assert case["original"]["accepted"] and case["original"]["all_proposed"]
    assert result["provider_calls"] == 0
