"""QH-8 real SQL/outbox/Neo4j/runtime checks. Dedicated disposable databases only."""

import asyncio
from copy import deepcopy
import json
import subprocess
import sys
from uuid import uuid4

from fastapi.testclient import TestClient
import psycopg
import pytest

from adapters.context.incremental import ProjectionWorker
from adapters.context.native import NativeContextError
from adapters.llm.offline import (
    FixtureUnderstandingProvider,
    ReplayLLMProvider,
    request_hash,
)
from app.bootstrap import create_runtime_app
from app.core.models import ContextQuery, ContextRequest, SubjectId
from app.understanding.extractor import UnderstandingExtractor
from tests.test_canonical_graph_pipeline import drain
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_runtime import configure, wait_until
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)
from tests.test_understanding import CASES, BAD, corrupt


def run(coro):
    return asyncio.run(coro)


def extractor(p, case):
    provider = FixtureUnderstandingProvider(case["items"])
    return UnderstandingExtractor(
        repository=p["repo"], policy=p["service"].policy, provider=provider
    ), provider


def import_extract(p, case, key="run-1"):
    usecase, provider = extractor(p, case)
    owner, scope = p["repo"].subject_id, p["scope"]
    ref = run(
        usecase.import_conversation(
            subject_id=owner, context_id=scope, conversation=case["conversation"]
        )
    )
    cp = run(
        usecase.extract(
            subject_id=owner,
            context_id=scope,
            source_revision_id=ref,
            extraction_key=key,
        )
    )
    return usecase, provider, ref, cp


def selected(p, values, *, scopes=None, subject=None, include_tentative=False):
    return run(
        p["service"].select_descriptors(
            subject_id=subject or p["repo"].subject_id,
            context_ids=scopes or (p["scope"],),
            values=values,
            include_tentative=include_tentative,
            limit=100,
        )
    )


def counts(repo):
    with repo.connect() as c:
        return {
            table: c.execute("SELECT count(*) AS n FROM " + table).fetchone()["n"]
            for table in (
                "sources",
                "source_revisions",
                "understanding_items",
                "understanding_item_revisions",
                "item_revision_types",
                "relation_revision_details",
                "item_revision_provenance",
                "projection_outbox",
                "semantic_type_versions",
            )
        }


def canonical(p, ids):
    return p["repo"].read_snapshot((p["scope"],), ids)


def test_three_domains_two_providers_atomic_outbox_and_structured_retrieval(generic):
    p = generic
    all_ids = []
    providers = []
    references = []
    for case in CASES:
        usecase, provider, ref, cp = import_extract(p, case)
        providers.append(provider)
        references.append(ref)
        # Exact captured response through an independently implemented port adapter.
        replay = ReplayLLMProvider(
            expected_request_sha256=request_hash(provider.last_request),
            response_json=provider.last_result.message.content,
        )
        alternate = UnderstandingExtractor(
            repository=p["repo"], policy=p["service"].policy, provider=replay
        )
        same = run(
            alternate.extract(
                subject_id=p["repo"].subject_id,
                context_id=p["scope"],
                source_revision_id=ref,
                extraction_key="run-1",
            )
        )
        assert same == cp and replay.calls == 1
        ids = run(
            alternate.publish(
                subject_id=p["repo"].subject_id, checkpoint=json.loads(json.dumps(same))
            )
        )
        before = counts(p["repo"])
        assert (
            run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp)) == ids
        )
        assert counts(p["repo"]) == before
        all_ids.extend(ids)
    assert len(all_ids) == 18
    assert counts(p["repo"])["semantic_type_versions"] == 14
    assert p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "pending"
    for value in ("decision", "nonexistent-descriptor"):
        with pytest.raises(NativeContextError, match="pending"):
            selected(p, [value])
    drain(p["worker"])
    for meaning in ("decision", "hypothesis", "open_question", "reversible_pause"):
        hits = selected(p, [meaning]).hits
        assert len(hits) == 3
        assert all(str(h.item_revision.revision_id) in all_ids for h in hits)
    assert not selected(p, ["expected_effect"]).hits
    assert len(selected(p, ["expected_effect"], include_tentative=True).hits) == 3
    assert not selected(p, ["decision"], scopes=(p["sibling"],)).hits
    with pytest.raises(PermissionError):
        selected(p, ["decision"], scopes=(p["scope"], p["foreign"]))
    with pytest.raises(PermissionError):
        selected(p, ["decision"], subject=str(uuid4()))
    data = canonical(p, all_ids)
    assert {r["type_id"] for r in data["understanding_item_revisions"]} == {
        "qh.generic." + s for s in ("item", "entity", "relation")
    }
    by_id = {r["id"]: r for r in data["understanding_item_revisions"]}
    sources = {r["id"]: r for r in data["source_revisions"]}
    for row in by_id.values():
        assert (
            row["validation_state"] == "proposed" and row["current_revision_id"] is None
        )
        assert row["validated_by"] is None and row["validated_at"] is None
        assert all(
            row[k] is None for k in ("fact_from", "fact_to", "valid_from", "valid_to")
        )
        for e in row["content"]["citations"]:
            assert e["source_revision_id"] in row["provenance"]
            assert (
                sources[e["source_revision_id"]]["content"][e["start"] : e["end"]]
                == e["quote"]
            )
            assert any(
                t["turn_id"] == e["turn_id"]
                for t in sources[e["source_revision_id"]]["origin"]["turns"]
            )
        if row["relation"]:
            rel = row["relation"]
            assert rel["source_item_id"] == by_id[rel["source_revision_id"]]["item_id"]
            assert rel["target_item_id"] == by_id[rel["target_revision_id"]]["item_id"]
    text = run(
        p["service"].retrieve(
            ContextRequest(
                subject_id=SubjectId(p["repo"].subject_id),
                query=ContextQuery(
                    text="reversible pause", context_ids=(p["scope"],), limit=100
                ),
            )
        )
    )
    assert len(text.hits) == 3
    assert all(provider.calls == 1 for provider in providers)
    print(
        json.dumps(
            dict(
                status="PASS",
                mode="offline fake/replay; no real LLM",
                owner=p["repo"].subject_id,
                scope=p["scope"],
                source_revision_ids=references,
                item_revision_ids=all_ids,
                meanings=[
                    "decision",
                    "hypothesis",
                    "open_question",
                    "reversible_pause",
                ],
                profiles=3,
                provenance="exact Unicode spans + source FKs",
                sample_source=sources[references[0]],
                structured_understanding=[
                    {
                        "revision_id": r["id"],
                        "item_id": r["item_id"],
                        "profile": r["type_id"],
                        "validation_state": r["validation_state"],
                        "content": r["content"],
                        "relation": r["relation"],
                        "provenance": r["provenance"],
                    }
                    for r in by_id.values()
                    if r["id"] in all_ids[:6]
                ],
                sync_state="ready",
            )
        )
    )


def test_invalid_outputs_source_retention_no_partial_batch_and_scope_denial(generic):
    p = generic
    usecase, provider, ref, cp = import_extract(p, CASES[0])
    before = counts(p["repo"])
    for mode in BAD:
        bad = deepcopy(cp)
        corrupt(bad, mode)
        with pytest.raises((ValueError, PermissionError)):
            run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=bad))
        assert counts(p["repo"]) == before
    for scope in (p["sibling"], p["foreign"]):
        with pytest.raises(PermissionError):
            run(
                usecase.extract(
                    subject_id=p["repo"].subject_id,
                    context_id=scope,
                    source_revision_id=ref,
                    extraction_key="foreign",
                )
            )
    assert provider.calls == 1
    # Immutable import and conflicting checkpoint replay are atomic as well.
    ids = run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp))
    before = canonical(p, ids)
    before_counts = counts(p["repo"])
    conflict = deepcopy(cp)
    conflict["output"]["items"][-1]["text"] = "Conflicting relation interpretation"
    with pytest.raises(ValueError, match="immutable"):
        run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=conflict))
    assert counts(p["repo"]) == before_counts and canonical(p, ids) == before
    modified = deepcopy(CASES[0]["conversation"])
    modified["turns"][0]["text"] = "Mutated original"
    with pytest.raises(ValueError, match="immutable"):
        run(
            usecase.import_conversation(
                subject_id=p["repo"].subject_id,
                context_id=p["scope"],
                conversation=modified,
            )
        )
    assert p["repo"].read_sources((p["scope"],), (ref,))[0]["origin"]["turns"]
    # A failure at deferred SQL publication rolls back even earlier valid rows.
    fresh = deepcopy(cp)
    fresh["extraction_key"] = "sql-rollback"
    rows = usecase._resolve(fresh, p["repo"].read_sources((p["scope"],), (ref,))[0])
    rows[-1]["provenance"] = [str(uuid4())]
    with pytest.raises(psycopg.Error):
        p["repo"].save(revisions=rows)
    assert counts(p["repo"]) == before_counts


def test_conversation_revision_and_combined_multidomain_scope(generic):
    p = generic
    case = deepcopy(CASES[0])
    case["conversation"]["id"] = "combined"
    case["conversation"]["turns"] = [
        deepcopy(t) for c in CASES for t in c["conversation"]["turns"]
    ]
    case["items"] = [
        {**deepcopy(i), "local_id": c["name"] + "-" + i["local_id"]}
        for c in CASES
        for i in c["items"]
        if i["shape"] != "relation"
    ]
    usecase, provider, ref, cp = import_extract(p, case)
    ids = run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp))
    original = canonical(p, ids)
    newer = deepcopy(case["conversation"])
    newer["revision_no"] = 2
    newer["turns"][-1]["text"] += " Additional source clarification."
    new_ref = run(
        usecase.import_conversation(
            subject_id=p["repo"].subject_id, context_id=p["scope"], conversation=newer
        )
    )
    assert new_ref != ref
    assert canonical(p, ids) == original
    assert run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp)) == ids
    assert provider.calls == 1
    assert len(p["repo"].read_sources((p["scope"],), (new_ref, ref))) == 2


def test_real_backend_process_restart_failure_pending_and_rebuild_without_extraction(
    generic, monkeypatch
):
    p = generic
    usecase, provider, ref, cp = import_extract(p, CASES[0])
    namespace = p["projector"].namespace
    configure(monkeypatch, namespace)
    # Application lifespan binds the actual runtime, not a separate test worker.
    with TestClient(create_runtime_app()) as client:
        runtime = client.app.state.native_context
        original_apply = runtime.projector.apply

        def fail(*args):
            raise ConnectionError("synthetic-extractor-test-error")

        monkeypatch.setattr(runtime.projector, "apply", fail)
        ids = run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp))
        wait_until(lambda: runtime.last_error_type == "ConnectionError")
        assert p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "failed"
        # PostgreSQL stays authoritative and readable while graph processing fails.
        before = canonical(p, ids)
        assert len(before["understanding_item_revisions"]) == 6
        with pytest.raises(NativeContextError, match="pending"):
            selected(p, ["decision"])
        monkeypatch.setattr(runtime.projector, "apply", original_apply)
    assert runtime.thread is None
    # Separate Uvicorn process retries failed work and is really stopped/restarted.
    processes = []

    def start():
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.bootstrap:create_runtime_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "0",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(proc)
        return proc

    def ready(proc):
        assert proc.poll() is None
        return p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "ready"

    try:
        first = start()
        wait_until(lambda: ready(first))
        assert len(selected(p, ["decision"]).hits) == 1
        first.terminate()
        assert first.wait(timeout=30) in (0, -15)
        # Another accepted extraction checkpoint is queued with the backend down.
        pending = deepcopy(cp)
        pending["extraction_key"] = "pending-offline-replay"
        pending_ids = run(
            usecase.publish(subject_id=p["repo"].subject_id, checkpoint=pending)
        )
        assert p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "pending"
        second = start()
        assert first.pid != second.pid
        wait_until(lambda: ready(second))
        assert {
            str(h.item_revision.revision_id) for h in selected(p, ["decision"]).hits
        } == {ids[0], pending_ids[0]}
        second.terminate()
        assert second.wait(timeout=30) in (0, -15)
        # Delete only this unique, test-owned graph namespace. Rebuild from SQL.
        with p["projector"].driver.session() as session:
            session.run(
                "MATCH (n) WHERE n.key STARTS WITH $prefix OR n.id STARTS WITH $prefix OR n.slice_id STARTS WITH $prefix DETACH DELETE n",
                prefix=namespace + ":",
            ).consume()
        with pytest.raises(NativeContextError):
            selected(p, ["decision"])
        ProjectionWorker(p["repo"], p["projector"], (p["scope"],)).rebuild(p["scope"])
        assert {
            str(h.item_revision.revision_id) for h in selected(p, ["decision"]).hits
        } == {ids[0], pending_ids[0]}
        assert canonical(p, ids) == before
        assert provider.calls == 1
        assert p["repo"].sync_status((p["scope"],))[0]["sync_state"] == "ready"
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=30)


def test_two_owners_and_sibling_spaces_cannot_share_sources_or_proposals(generic):
    from adapters.postgres.canonical import CanonicalRepository
    from adapters.context.incremental import IncrementalContextEngine
    from adapters.context.native import AuthorizedNativeContextService

    p = generic
    usecase, provider, ref, cp = import_extract(p, CASES[0])
    alice_ids = run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=cp))
    with p["repo"].connect() as c:
        other = str(
            c.execute(
                "SELECT owner_id FROM context_spaces WHERE id=%s", (p["foreign"],)
            ).fetchone()["owner_id"]
        )
    bob_repo = CanonicalRepository(url=p["repo"].url, subject_id=other)
    bob = UnderstandingExtractor(
        repository=bob_repo,
        policy=p["service"].policy,
        provider=FixtureUnderstandingProvider(CASES[0]["items"]),
    )
    bob_ref = run(
        bob.import_conversation(
            subject_id=other,
            context_id=p["foreign"],
            conversation=CASES[0]["conversation"],
        )
    )
    bob_cp = run(
        bob.extract(
            subject_id=other,
            context_id=p["foreign"],
            source_revision_id=bob_ref,
            extraction_key="run-1",
        )
    )
    bob_ids = run(bob.publish(subject_id=other, checkpoint=bob_cp))
    sibling_ref = run(
        usecase.import_conversation(
            subject_id=p["repo"].subject_id,
            context_id=p["sibling"],
            conversation=CASES[0]["conversation"],
        )
    )
    sibling_cp = run(
        usecase.extract(
            subject_id=p["repo"].subject_id,
            context_id=p["sibling"],
            source_revision_id=sibling_ref,
            extraction_key="run-1",
        )
    )
    sibling_ids = run(
        usecase.publish(subject_id=p["repo"].subject_id, checkpoint=sibling_cp)
    )
    assert (
        len({ref, bob_ref, sibling_ref}) == 3
        and len(set(alice_ids + bob_ids + sibling_ids)) == 18
    )
    for repo, scope in (
        (p["repo"], p["scope"]),
        (p["repo"], p["sibling"]),
        (bob_repo, p["foreign"]),
    ):
        drain(ProjectionWorker(repo, p["projector"], (scope,)))
    bob_service = AuthorizedNativeContextService(
        policy=p["service"].policy,
        engine=IncrementalContextEngine(bob_repo, p["projector"]),
    )
    bob_result = run(
        bob_service.select_descriptors(
            subject_id=other, context_ids=(p["foreign"],), values=["decision"]
        )
    )
    assert [str(h.item_revision.revision_id) for h in bob_result.hits] == [bob_ids[0]]
    assert [
        str(h.item_revision.revision_id) for h in selected(p, ["decision"]).hits
    ] == [alice_ids[0]]
    assert [
        str(h.item_revision.revision_id)
        for h in selected(p, ["decision"], scopes=(p["sibling"],)).hits
    ] == [sibling_ids[0]]
    with pytest.raises(PermissionError):
        run(bob.publish(subject_id=other, checkpoint=cp))
    poisoned = deepcopy(cp)
    poisoned["context_space_id"] = p["sibling"]
    with pytest.raises(PermissionError):
        run(usecase.publish(subject_id=p["repo"].subject_id, checkpoint=poisoned))
    assert (
        provider.calls == 2
    )  # One per explicitly requested extraction; no worker/rebuild call.
