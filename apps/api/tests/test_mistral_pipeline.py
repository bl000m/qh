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
            out=resumed, live=True, resume_from=folder,
            reviewed_resumption=True, case_names=["work"],
        )
    after = json.loads((folder / "ledger.json").read_text())
    assert seen == ["POST"] and len(after["calls"]) == 3 and after["blocked"]
    assert after["calls"][:2] == before
    assert after["calls"][2]["reserved_usd"] == "0.006"
    assert after["reconciliations"][0]["calls_retained"] == 2
    assert after["reconciliations"][0]["failed_reservations_retained_usd"] == "0.006"
    assert json.loads((resumed / "ledger-before-reconciliation.json").read_text())["calls"] == before
    assert not (resumed / "ledger.json").exists()
    diagnostic = json.loads((resumed / "experiment-error.json").read_text())
    assert diagnostic["provider_diagnostic"]["http_status"] == 429
    state = json.loads((resumed / "failure-state.json").read_text())
    assert state["source_revision_count"] == 1 and not state["understanding_item_revisions"]
    assert not (resumed / "work/raw.json").exists() and not (resumed / "evolving").exists()
