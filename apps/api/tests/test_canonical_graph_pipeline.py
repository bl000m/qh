"""Real SQL -> Neo4j pipeline; fixture data retained, fixture reader replaced."""

import asyncio
from copy import deepcopy
import os
from uuid import uuid4

from alembic import command
import psycopg
import pytest

from adapters.context.native import (
    AuthorizedNativeContextService,
    NativeContextEngine,
    NativeContextError,
    reconcile,
)
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from app.core.models import ContextQuery, ContextRequest, SubjectId
from app.policy.owner import OwnerPolicyService
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import A, B, FIXTURE, real_engine as real_engine
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)


def records(space):
    sources = [
        deepcopy(r)
        for r in FIXTURE["source_revisions"]
        if r["context_space_id"] == space
    ]
    revisions = []
    for original in FIXTURE["understanding_item_revisions"]:
        if original["context_space_id"] != space:
            continue
        r = deepcopy(original)
        category = r.pop("category")
        r["type_id"] = r["content"].pop("semantic_type")
        r["type_version"] = r["content"].pop("schema_version")
        props = r["content"]["properties"]
        event = props.pop("event_at")
        r.update(fact_from=event, fact_to=event, valid_from=None, valid_to=None)
        if category == "relationship":
            r["relation"] = {
                "source_item_id": props.pop("subject_item_id"),
                "source_revision_id": props.pop("subject_revision_id"),
                "target_item_id": props.pop("object_item_id"),
                "target_revision_id": props.pop("object_revision_id"),
                "predicate": props.pop("predicate"),
            }
        revisions.append(r)
    return sources, revisions


@pytest.fixture
def pipeline(empty_database, real_engine):
    assert os.environ["QH30_TEST_NEO4J_URI"] == "bolt://qh30-native-neo4j-test:7687"
    command.upgrade(empty_database, "0003_native_semantics")
    graph = real_engine[0].driver
    owner, other = str(uuid4()), str(uuid4())
    url = database_url()
    repo = CanonicalRepository(url=url, subject_id=owner)
    bob = CanonicalRepository(url=url, subject_id=other)
    with repo.connect() as c:
        for who in (owner, other):
            c.execute(
                "INSERT INTO users(id,display_name) VALUES (%s,'Synthetic owner')",
                (who,),
            )
        for scope, who in ((A, owner), (B, other)):
            c.execute(
                "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic context')",
                (scope, who),
            )
    repo.register_types(
        [
            dict(
                type_id="qh.observation",
                version=1,
                structural_kind="item",
                property_schema={
                    "type": "object",
                    "required": ["text"],
                    "properties": {"text": {"type": "string"}},
                },
            )
        ]
    )
    sources, revisions = records(A)
    repo.save(sources=sources, revisions=revisions)
    bob.save(sources=records(B)[0], revisions=records(B)[1])
    engine = NativeContextEngine(
        graph,
        slice_id="qh30-pipeline-" + uuid4().hex,
        read_snapshot=repo.read_snapshot,
        verify_readiness=True,
    )
    service = AuthorizedNativeContextService(
        policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=url).owner_for),
        engine=engine,
    )
    return repo, bob, engine, service, revisions


def retrieve(p, text="Cedar", scopes=(A,), subject=None):
    repo, _, _, service, _ = p
    return asyncio.run(
        service.retrieve(
            ContextRequest(
                subject_id=SubjectId(subject or repo.subject_id),
                query=ContextQuery(text=text, context_ids=scopes, limit=100),
            )
        )
    )


def test_real_multidomain_sql_to_graph_with_provenance_temporal_and_policy(pipeline):
    repo, bob, engine, _, revisions = pipeline
    with pytest.raises(NativeContextError, match="not ready"):
        retrieve(pipeline)
    first = reconcile(repo, engine, (A,))
    assert len(retrieve(pipeline).hits) == 3
    snapshot = repo.read_snapshot((A,))
    assert all(r["category"] is None for r in snapshot["understanding_item_revisions"])
    assert {r["type_id"] for r in snapshot["understanding_item_revisions"]} >= {
        "qh.observation",
        "qh.preference",
        "qh.decision",
    }
    for case in FIXTURE["cases"]:
        assertion = next(
            r
            for r in snapshot["understanding_item_revisions"]
            if r["id"] == case["revision_ids"][2]
        )
        assert (assertion["fact_from"] is not None) == (
            case["domain"] == "professional"
        )
        assert assertion["validation_state"] == "proposed"
    assert all(
        h.item_revision and h.provenance and h.context_id == A
        for h in retrieve(pipeline).hits
    )
    with pytest.raises(PermissionError):
        retrieve(pipeline, scopes=(B,))
    with pytest.raises(PermissionError):
        retrieve(pipeline, scopes=(A, B))
    with pytest.raises(PermissionError):
        repo.read_snapshot((B,))
    with pytest.raises(PermissionError):
        repo.save(sources=records(B)[0])
    assert not bob.read_snapshot((B,), [revisions[0]["id"]])[
        "understanding_item_revisions"
    ]
    assert reconcile(repo, engine, (A,)) == first
    with engine.driver.session() as s:
        result = s.run(
            "MATCH (a)<-[:SUBJECT]-(r:QH30Revision {slice_id:$id,generation:$g})-[:OBJECT]->(b) RETURN count(r) AS n,collect(a.category+'->'+b.category) AS shapes",
            id=engine.slice_id,
            g=first,
        ).single()
        assert result["n"] == 3 and set(result["shapes"]) == {
            "item->entity",
            "item->item",
            "relation->item",
        }
    repo.save(
        sources=records(A)[0], revisions=revisions
    )  # exact replay, no history mutation
    assert reconcile(repo, engine, (A,)) == first


def updated(pipeline):
    repo, _, _, _, revisions = pipeline
    old = next(r for r in revisions if r["type_id"] == "qh.decision")
    new = deepcopy(old)
    new.update(id=str(uuid4()), revision_no=2, based_on_revision_id=old["id"])
    new["content"]["text"] = "Updated synthetic pilot"
    repo.save(revisions=[new])
    return old, new


def test_updates_detect_pending_even_for_empty_candidates_then_reconcile(pipeline):
    repo, _, engine, _, _ = pipeline
    first = reconcile(repo, engine, (A,))
    old, new = updated(pipeline)
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Updated")
    second = reconcile(repo, engine, (A,))
    assert second != first
    hits = retrieve(pipeline, "Updated").hits
    assert len(hits) == 1 and hits[0].item_revision.item_id == new["item_id"]
    versions = repo.read_snapshot((A,), [old["id"], new["id"]])[
        "understanding_item_revisions"
    ]
    assert len(versions) == 2 and all(
        r["validation_state"] == "proposed" and r["current_revision_id"] is None
        for r in versions
    )
    assert (
        next(r for r in versions if r["id"] == old["id"])["content"] == old["content"]
    )


def test_canonical_batch_rollback_conflicting_replay_and_bad_schema(pipeline):
    repo, _, engine, _, revisions = pipeline
    before = repo.read_snapshot((A,))
    changed = deepcopy(revisions[0])
    changed["content"]["text"] = "Illegal rewrite"
    with pytest.raises(ValueError, match="immutable"):
        repo.save(revisions=[changed])
    good = deepcopy(revisions[0])
    good.update(id=str(uuid4()), revision_no=2)
    bad = deepcopy(revisions[1])
    bad.update(id=str(uuid4()), revision_no=2, type_id="missing.type")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repo.save(revisions=[good, bad])
    assert repo.read_snapshot((A,)) == before
    invalid = deepcopy(next(r for r in revisions if r["type_id"] == "qh.observation"))
    invalid.update(id=str(uuid4()), revision_no=2)
    invalid["content"] = {"text": 17}
    with pytest.raises(psycopg.errors.CheckViolation):
        repo.save(revisions=[invalid])
    assert repo.read_snapshot((A,)) == before
    reconcile(repo, engine, (A,))
    assert retrieve(pipeline).hits


def test_graph_transaction_failure_preserves_pg_and_recovers(pipeline, monkeypatch):
    repo, _, engine, _, _ = pipeline
    oldgen = reconcile(repo, engine, (A,))
    old, new = updated(pipeline)
    original = engine.replace

    def poison(snapshot, *, generation):
        revision = snapshot["understanding_item_revisions"][0]["id"]
        with engine.driver.session() as s:
            s.run(
                "CREATE (:QH30Revision {key:$key,fingerprint:'conflict',slice_id:$id,generation:$g})",
                key=engine.slice_id + ":" + generation + ":" + revision,
                id=engine.slice_id,
                g=generation,
            ).consume()
        original(snapshot, generation=generation)

    with monkeypatch.context() as patch:
        patch.setattr(engine, "replace", poison)
        with pytest.raises(NativeContextError, match="immutable"):
            reconcile(repo, engine, (A,))
    assert repo.read_snapshot((A,), [new["id"]])["understanding_item_revisions"]
    with engine.driver.session() as s:
        assert (
            s.run(
                "MATCH (s:QH30Slice {id:$id}) RETURN s.active_generation AS g",
                id=engine.slice_id,
            ).single()["g"]
            == oldgen
        )
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Updated")
    reconcile(repo, engine, (A,))
    assert len(retrieve(pipeline, "Updated").hits) == 1


def test_lost_ack_restart_and_graph_loss_rebuild(pipeline, monkeypatch):
    repo, _, engine, _, _ = pipeline
    original = engine.replace

    def lost_ack(snapshot, *, generation):
        original(snapshot, generation=generation)
        raise ConnectionError("Synthetic lost graph acknowledgement")

    with monkeypatch.context() as patch:
        patch.setattr(engine, "replace", lost_ack)
        with pytest.raises(ConnectionError):
            reconcile(repo, engine, (A,))
    # Recreate application adapters; no in-memory queue/checkpoint is necessary.
    fresh = CanonicalRepository(url=repo.url, subject_id=repo.subject_id)
    engine.read_snapshot = fresh.read_snapshot
    recovered = reconcile(fresh, engine, (A,))
    assert len(retrieve(pipeline).hits) == 3
    assert reconcile(fresh, engine, (A,)) == recovered
    with engine.driver.session() as s:
        s.run(
            "MATCH (n) WHERE (n:QH30Revision OR n:QH30Source) AND n.slice_id=$id OR n:QH30Slice AND n.id=$id OR n:QH30Generation AND n.key STARTS WITH $prefix DETACH DELETE n",
            id=engine.slice_id,
            prefix=engine.slice_id + ":",
        ).consume()
    with pytest.raises(NativeContextError, match="not ready"):
        retrieve(pipeline)
    assert reconcile(fresh, engine, (A,)) != recovered
    assert len(retrieve(pipeline).hits) == 3


def test_external_original_reference_does_not_require_vault_io(pipeline):
    repo, _, engine, _, _ = pipeline
    source = deepcopy(records(A)[0][0])
    source.update(
        id=str(uuid4()),
        revision_no=2,
        content="",
        origin={
            "opaque_original_reference": "synthetic-object-42",
            "representation": "not-inline",
        },
    )
    revision = deepcopy(records(A)[1][0])
    revision.update(id=str(uuid4()), revision_no=2, provenance=[source["id"]])
    repo.save(sources=[source], revisions=[revision])
    snapshot = repo.read_snapshot((A,), [revision["id"]])
    assert snapshot["source_revisions"][0]["content"] == ""
    assert snapshot["source_revisions"][0]["origin"] == source["origin"]
    reconcile(repo, engine, (A,))
    assert any(
        h.provenance[0].revision_id == source["id"] for h in retrieve(pipeline).hits
    )


def test_second_context_is_projected_independently(pipeline):
    repo, bob, engine, service, _ = pipeline
    reconcile(repo, engine, (A,))
    other = NativeContextEngine(
        engine.driver,
        slice_id="qh30-bob-" + uuid4().hex,
        read_snapshot=bob.read_snapshot,
        verify_readiness=True,
    )
    reconcile(bob, other, (B,))
    authorized = AuthorizedNativeContextService(policy=service.policy, engine=other)

    def query(text):
        return asyncio.run(
            authorized.retrieve(
                ContextRequest(
                    subject_id=SubjectId(bob.subject_id),
                    query=ContextQuery(text=text, context_ids=(B,)),
                )
            )
        )

    assert len(query("Birch").hits) == 3
    assert not query("Cedar").hits
    assert len(retrieve(pipeline).hits) == 3


def test_empty_scope_is_ready_until_canonical_content_arrives(pipeline):
    repo, _, engine, _, _ = pipeline
    scope = str(uuid4())
    with repo.connect() as c:
        c.execute(
            "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Empty synthetic space')",
            (scope, repo.subject_id),
        )
    empty = NativeContextEngine(
        engine.driver,
        slice_id="qh30-empty-" + uuid4().hex,
        read_snapshot=repo.read_snapshot,
        verify_readiness=True,
    )
    reconcile(repo, empty, (scope,))
    assert not asyncio.run(
        empty.search(ContextQuery(text="New", context_ids=(scope,)))
    ).hits
    source = deepcopy(records(A)[0][0])
    source.update(id=str(uuid4()), source_id=str(uuid4()), context_space_id=scope)
    row = deepcopy(records(A)[1][0])
    row.update(
        id=str(uuid4()),
        item_id=str(uuid4()),
        context_space_id=scope,
        provenance=[source["id"]],
    )
    row["content"]["text"] = "New synthetic content"
    repo.save(sources=[source], revisions=[row])
    with pytest.raises(NativeContextError, match="pending"):
        asyncio.run(empty.search(ContextQuery(text="New", context_ids=(scope,))))
    reconcile(repo, empty, (scope,))
    assert (
        len(
            asyncio.run(
                empty.search(ContextQuery(text="New", context_ids=(scope,)))
            ).hits
        )
        == 1
    )


def test_change_during_projection_requires_next_reconciliation(pipeline, monkeypatch):
    repo, _, engine, _, _ = pipeline
    original = engine.replace

    def advance(snapshot, *, generation):
        original(snapshot, generation=generation)
        updated(pipeline)

    with monkeypatch.context() as patch:
        patch.setattr(engine, "replace", advance)
        with pytest.raises(NativeContextError, match="advanced"):
            reconcile(repo, engine, (A,))
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Updated")
    reconcile(repo, engine, (A,))
    assert len(retrieve(pipeline, "Updated").hits) == 1


def test_graph_temporal_tampering_is_rejected(pipeline):
    repo, _, engine, _, _ = pipeline
    reconcile(repo, engine, (A,))
    with engine.driver.session() as s:
        s.run(
            "MATCH (r:QH30Revision {slice_id:$id}) WHERE r.text CONTAINS 'Cedar' SET r.fact_from='invented'",
            id=engine.slice_id,
        ).consume()
    with pytest.raises(NativeContextError):
        retrieve(pipeline)
    reconcile(repo, engine, (A,), force_rebuild=True)
    assert retrieve(pipeline).hits


def test_identity_writer_preflight_and_provisioning_after_0003(pipeline):
    from adapters.postgres.demo_identities import (
        provision_demo,
        require_identity_schema,
    )

    repo = pipeline[0]
    # Dict-row repository connections are not the tuple-row identity writer contract.
    with psycopg.connect(
        host=repo.url.host,
        port=repo.url.port,
        dbname=repo.url.database,
        user=repo.url.username,
        password=repo.url.password,
    ) as c:
        require_identity_schema(c)
        provision_demo(c, issuer="synthetic://issuer")
        provision_demo(c, issuer="synthetic://issuer")
        assert c.execute("SELECT count(*) FROM user_identities").fetchone() == (2,)
    assert repo.read_snapshot((A,))["understanding_item_revisions"]


def test_partial_graph_loss_cannot_be_a_fresh_empty_result(pipeline):
    repo, _, engine, _, _ = pipeline
    generation = reconcile(repo, engine, (A,))
    with engine.driver.session() as s:
        s.run(
            "MATCH (r:QH30Revision {slice_id:$id}) WHERE r.text CONTAINS 'Cedar' DETACH DELETE r",
            id=engine.slice_id,
        ).consume()
    with pytest.raises(NativeContextError, match="incomplete"):
        retrieve(pipeline)
    assert reconcile(repo, engine, (A,)) == generation
    assert len(retrieve(pipeline).hits) == 3


def test_canonical_read_failure_preserves_cause(pipeline, monkeypatch):
    repo, _, engine, _, _ = pipeline
    reconcile(repo, engine, (A,))

    def unavailable(*args):
        raise psycopg.OperationalError("Synthetic SQL unavailable")

    monkeypatch.setattr(engine, "read_snapshot", unavailable)
    with pytest.raises(NativeContextError, match="Canonical read") as error:
        retrieve(pipeline)
    assert isinstance(error.value.__cause__, psycopg.OperationalError)


def test_reconciliation_serializes_projectors(pipeline, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, Lock
    import time

    repo, _, engine, _, _ = pipeline
    entered, release = Event(), Event()
    guard = Lock()
    calls = []
    original = engine.replace

    def slow(snapshot, *, generation):
        with guard:
            calls.append(generation)
            first = len(calls) == 1
        if first:
            entered.set()
            assert release.wait(8)
        return original(snapshot, generation=generation)

    monkeypatch.setattr(engine, "replace", slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(reconcile, repo, engine, (A,))
        assert entered.wait(5)
        two = pool.submit(reconcile, repo, engine, (A,))
        try:
            with repo.connect(autocommit=True) as c:
                deadline = time.monotonic() + 5
                while (
                    c.execute(
                        "SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory' AND NOT granted"
                    ).fetchone()["n"]
                    == 0
                ):
                    assert time.monotonic() < deadline
                    time.sleep(0.02)
            assert len(calls) == 1
        finally:
            release.set()
        assert one.result(timeout=8) == two.result(timeout=8)
    assert len(retrieve(pipeline).hits) == 3


def test_repository_iterators_and_type_replay(pipeline):
    repo, _, engine, _, revisions = pipeline
    repo.save(sources=iter(records(A)[0]), revisions=iter(revisions))
    selected = repo.read_snapshot((A,), iter([revisions[0]["id"]]))
    assert [r["id"] for r in selected["understanding_item_revisions"]] == [
        revisions[0]["id"]
    ]
    with repo.connect() as c:
        definition = c.execute(
            "SELECT * FROM semantic_type_versions WHERE type_id='qh.observation' AND version=1"
        ).fetchone()
    repo.register_types([definition])
    changed = deepcopy(definition)
    changed["property_schema"] = {"type": "object", "required": ["different"]}
    with pytest.raises(ValueError, match="registered type replay"):
        repo.register_types([changed])
    reconcile(repo, engine, (A,))
    assert len(retrieve(pipeline).hits) == 3
