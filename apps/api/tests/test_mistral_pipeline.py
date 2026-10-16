"""Real SQL/Neo4j, mocked Mistral HTTP only. No paid calls in CI."""

import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from adapters.llm.mistral import ExperimentBudget, MistralProvider, MODEL, MistralError
from app.understanding.extractor import UnderstandingExtractor
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)
from tests.test_understanding_pipeline import selected
from tests.test_canonical_graph_pipeline import drain
from tests.test_understanding import CASES


def test_mistral_wire_adapter_to_canonical_outbox_retrieval_and_offline_replay(
    generic, tmp_path, monkeypatch
):
    p = generic
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic-mock-only")
    captured = []

    def handler(req):
        source = json.loads(json.loads(req.content)["messages"][-1]["content"])
        turn = source["turns"][0]
        quote = source["text"][turn["start"] : turn["end"]]
        body = {
            "items": [
                dict(
                    local_id="reported",
                    shape="item",
                    text=quote,
                    descriptors=[
                        {"value": "reported_statement", "certainty": "asserted"}
                    ],
                    evidence=[
                        dict(
                            source_revision_id=source["source_revision_id"],
                            start=turn["start"],
                            end=turn["end"],
                            quote=quote,
                        )
                    ],
                )
            ]
        }
        raw = dict(
            model=MODEL,
            usage=dict(prompt_tokens=150, completion_tokens=120),
            choices=[
                dict(
                    finish_reason="stop",
                    message=dict(role="assistant", content=json.dumps(body)),
                )
            ],
        )
        captured.append(raw)
        return httpx.Response(200, json=raw)

    budget = ExperimentBudget(tmp_path / "ledger.json", create=True)
    provider = MistralProvider(budget=budget, transport=httpx.MockTransport(handler))
    usecase = UnderstandingExtractor(
        repository=p["repo"], policy=p["service"].policy, provider=provider
    )
    owner = p["repo"].subject_id
    ref = asyncio.run(
        usecase.import_conversation(
            subject_id=owner,
            context_id=p["scope"],
            conversation=CASES[0]["conversation"],
        )
    )
    cp = asyncio.run(
        usecase.extract(
            subject_id=owner,
            context_id=p["scope"],
            source_revision_id=ref,
            extraction_key="mock-wire-v1",
        )
    )
    ids = asyncio.run(usecase.publish(subject_id=owner, checkpoint=cp))
    assert p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "pending"
    drain(p["worker"])
    assert [
        str(h.item_revision.revision_id)
        for h in selected(p, ["reported_statement"]).hits
    ] == list(ids)
    restored = json.loads(json.dumps(cp))
    assert asyncio.run(usecase.publish(subject_id=owner, checkpoint=restored)) == ids
    assert len(captured) == 1 and provider.last_exchange["response"] == captured[0]
    row = p["repo"].read_snapshot((p["scope"],), ids)["understanding_item_revisions"][0]
    assert row["validation_state"] == "proposed" and row["current_revision_id"] is None
    assert (
        row["provenance"] == [ref]
        and row["content"]["citations"][0]["source_revision_id"] == ref
    )


def test_live_harness_429_stops_without_retry_and_retains_artifacts(
    real_engine, tmp_path, monkeypatch
):
    # Exercise the manual harness on disposable infrastructure with a mock transport.
    # CI flag is removed only here, with the adapter factory explicitly replaced.
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic-mock-only")
    path = Path(__file__).resolve().parents[3] / "scripts/evaluate_qh8_mistral.py"
    spec = importlib.util.spec_from_file_location("evaluation_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seen = []

    def handler(req):
        seen.append(req.method)
        if req.method == "GET":
            return httpx.Response(
                200, json=dict(id=MODEL, capabilities={"completion_chat": True})
            )
        return httpx.Response(429, json={"message": "synthetic rate-limit failure"})

    monkeypatch.setattr(
        module,
        "MistralProvider",
        lambda **kw: MistralProvider(**kw, transport=httpx.MockTransport(handler)),
    )
    folder = tmp_path / "run"
    with pytest.raises(MistralError, match="429"):
        module.execute(out=folder, live=True)
    ledger = json.loads((folder / "ledger.json").read_text())
    assert seen == ["GET", "POST"] and len(ledger["calls"]) == 2 and ledger["blocked"]
    assert (folder / "work/source.json").exists() and not (
        folder / "work/raw.json"
    ).exists()
    state = json.loads((folder / "failure-state.json").read_text())
    assert state["source_revision_count"] == 1
    assert not state["understanding_item_revisions"]
    assert all(
        s["desired_version"] == s["applied_version"] == 0 for s in state["sync_status"]
    )
    assert not (folder / "evolving").exists()

    # Explicit reviewed resumption reuses the ledger and makes exactly one POST.
    resumed = tmp_path / "resumed"
    before = ledger["calls"]
    seen.clear()
    with pytest.raises(MistralError, match="429"):
        module.execute(
            out=resumed,
            live=True,
            resume_from=folder,
            reviewed_resumption=True,
            case_names=["work"],
        )
    after = json.loads((folder / "ledger.json").read_text())
    assert seen == ["POST"] and len(after["calls"]) == 3 and after["blocked"]
    assert after["calls"][:2] == before
    assert after["calls"][2]["reserved_usd"] == "0.006"
    assert after["reconciliations"][0]["calls_retained"] == 2
    assert after["reconciliations"][0]["failed_reservations_retained_usd"] == "0.006"
    assert (
        json.loads((resumed / "ledger-before-reconciliation.json").read_text())["calls"]
        == before
    )
    assert not (resumed / "ledger.json").exists()
    diagnostic = json.loads((resumed / "experiment-error.json").read_text())
    assert diagnostic["provider_diagnostic"]["http_status"] == 429
    state = json.loads((resumed / "failure-state.json").read_text())
    assert (
        state["source_revision_count"] == 1
        and not state["understanding_item_revisions"]
    )
    assert (
        not (resumed / "work/raw.json").exists() and not (resumed / "evolving").exists()
    )


def test_harness_text_lookup_matches_snapshot_row_when_publish_order_differs():
    from types import SimpleNamespace

    path = Path(__file__).resolve().parents[3] / "scripts/evaluate_qh8_mistral.py"
    spec = importlib.util.spec_from_file_location("evaluation_order_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [
        dict(
            id=identity,
            content={"text": text},
            validation_state="proposed",
            current_revision_id=None,
        )
        for identity, text in [
            ("revision-b", "second distinct assertion"),
            ("revision-a", "first distinct assertion"),
        ]
    ]

    async def retrieve(request):
        matches = [r for r in rows if r["content"]["text"] == request.query.text]
        return SimpleNamespace(
            hits=[
                SimpleNamespace(item_revision=SimpleNamespace(revision_id=r["id"]))
                for r in matches
            ]
        )

    async def deny(**kwargs):
        raise PermissionError("Foreign subject")

    repo = SimpleNamespace(
        sync_status=lambda scopes: [{"sync_state": "ready"}],
        read_snapshot=lambda scopes, ids: {"understanding_item_revisions": rows},
    )
    runtime = SimpleNamespace(
        context_for=lambda owner: SimpleNamespace(
            retrieve=retrieve, select_descriptors=deny
        )
    )
    result = module.collect_pipeline(
        runtime, repo, "owner", "scope", ["revision-a", "revision-b"]
    )
    assert result["status"] == "PASS" and result["foreign_subject_denied"]


def test_frozen_four_batch_resolution_and_atomic_native_replay(
    real_engine, tmp_path, monkeypatch
):
    from shutil import copyfile
    from uuid import uuid4
    from tests.test_citations import CAPTURES

    path = Path(__file__).resolve().parents[3] / "scripts/evaluate_qh8_mistral.py"
    spec = importlib.util.spec_from_file_location("citation_replay_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # No inference client may even be constructed; all responses are frozen replays.
    def no_live_provider(**kwargs):
        raise AssertionError("No provider construction in offline resolution")

    monkeypatch.setattr(module, "MistralProvider", no_live_provider)
    fixture = tmp_path / "frozen"
    fixture.mkdir()
    scopes = {}
    cases = ["work", "evolving", "personal", "multilingual"]
    for case in cases:
        (fixture / case).mkdir()
        copyfile(CAPTURES / case / "raw.json", fixture / case / "raw.json")
        scopes[case] = json.loads((CAPTURES / case / "source.json").read_text())[
            "context_space_id"
        ]
    manifest = dict(
        owner=str(uuid4()),
        scopes=scopes,
        dataset_sha256=module.source_digest(
            module.FIXTURES / "mistral_unseen_conversations.json"
        ),
        reference_sha256=module.source_digest(
            module.FIXTURES / "mistral_evaluation_reference.json"
        ),
    )
    (fixture / "manifest.json").write_text(json.dumps(manifest))
    original = module.execute(
        out=tmp_path / "original", live=False, replay_from=fixture
    )
    derived = module.execute(
        out=tmp_path / "derived",
        live=False,
        replay_from=fixture,
        resolve_citations=True,
    )
    assert [r["items"] for r in original] == [0, 0, 5, 0]
    assert [r["items"] for r in derived] == [9, 14, 5, 0]
    assert [r["original_raw_validation"] for r in derived] == [
        "FAIL",
        "FAIL",
        "PASS",
        "FAIL",
    ]
    assert [r.get("corrected_spans", 0) for r in derived] == [5, 6, 0, 0]
    assert all(r["offline_provider_replays"] == 1 for r in derived)
    for case, count in zip(cases[:3], [9, 14, 5], strict=True):
        folder = tmp_path / "derived" / case
        canonical = json.loads((folder / "canonical.json").read_text())
        assert len(canonical["export"]["understanding_item_revisions"]) == count
        assert (
            canonical["foreign_subject_denied"] and canonical["sync_state"] == "ready"
        )
        assert derived[cases.index(case)]["checkpoint_replay"] == "PASS"
        assert all(
            r["validation_state"] == "proposed" and r["current_revision_id"] is None
            for r in canonical["export"]["understanding_item_revisions"]
        )
    failed = tmp_path / "derived" / "multilingual"
    assert (
        not (failed / "derived-output.json").exists()
        and not (failed / "canonical.json").exists()
    )
    assert (
        len(json.loads((failed / "citation-resolution.json").read_text())["issues"])
        == 3
    )
    assert derived[-1]["items"] == 0 and derived[-1]["source_retained"]
    assert derived[-1]["rejected_scope_versions"] == {"desired": 0, "applied": 0}


def test_citation_derivation_rejects_live_mode_before_any_side_effect(tmp_path):
    path = Path(__file__).resolve().parents[3] / "scripts/evaluate_qh8_mistral.py"
    spec = importlib.util.spec_from_file_location("offline_only_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="offline capture replay"):
        module.execute(
            out=tmp_path / "must-not-exist", live=True, resolve_citations=True
        )
    assert not (tmp_path / "must-not-exist").exists()
