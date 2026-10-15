"""Canonical SQL/outbox -> incremental graph and explicit rebuild regressions."""

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
)
from adapters.context.incremental import (
    IncrementalContextEngine,
    IncrementalProjector,
    ProjectionWorker,
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
    revisions = [
        deepcopy(r)
        for r in FIXTURE["understanding_item_revisions"]
        if r["context_space_id"] == space
    ]
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
    command.upgrade(empty_database, "0004_projection_outbox")
    projector = IncrementalProjector(graph, namespace="qh30-pipeline-" + url.database)
    projector.initialize()
    engine = IncrementalContextEngine(repo, projector)
    service = AuthorizedNativeContextService(
        policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=url).owner_for),
        engine=engine,
    )
    return repo, bob, projector, service, revisions


def drain(worker):
    """Test-owned bounded processing helper shared by all real pipeline suites."""
    for count in range(100):
        event = worker.claim()
        if event is None:
            return count
        assert worker.process(event), repr(worker.last_error)
    raise AssertionError("Unexpected unbounded queue")


def project(pipeline, scopes=(A,)):
    return drain(ProjectionWorker(pipeline[0], pipeline[2], scopes))


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


def updated(pipeline):
    repo, _, _, _, revisions = pipeline
    old = next(r for r in revisions if r["type_id"] == "qh.decision")
    new = deepcopy(old)
    new.update(id=str(uuid4()), revision_no=2, based_on_revision_id=old["id"])
    new["content"]["text"] = "Updated synthetic pilot"
    repo.save(revisions=[new])
    return old, new


def test_canonical_batch_rollback_conflicting_replay_and_bad_schema(pipeline):
    repo, _, _, _, revisions = pipeline
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
    project(pipeline)
    assert retrieve(pipeline).hits


def test_external_original_reference_does_not_require_vault_io(pipeline):
    repo = pipeline[0]
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
    project(pipeline)
    assert any(
        h.provenance[0].revision_id == source["id"] for h in retrieve(pipeline).hits
    )


def test_identity_writer_preflight_and_provisioning_after_0004(pipeline):
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


def test_repository_iterators_and_type_replay(pipeline):
    repo, _, _, _, revisions = pipeline
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
    project(pipeline)
    assert len(retrieve(pipeline).hits) == 3


def test_real_multidomain_sql_outbox_graph_and_policy(pipeline):
    repo, bob, graph, _, rows = pipeline
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline)
    assert project(pipeline) == len(rows)
    snapshot = repo.read_snapshot((A,))
    assert all("category" not in r for r in snapshot["understanding_item_revisions"])
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
    assert len(retrieve(pipeline).hits) == 3
    assert all(
        h.item_revision and h.provenance and h.context_id == A
        for h in retrieve(pipeline).hits
    )
    for scopes in ((B,), (A, B)):
        with pytest.raises(PermissionError):
            retrieve(pipeline, scopes=scopes)
    with pytest.raises(PermissionError):
        repo.read_snapshot((B,))
    with pytest.raises(PermissionError):
        repo.save(sources=records(B)[0])
    assert not bob.read_snapshot((B,), [rows[0]["id"]])["understanding_item_revisions"]
    with graph.driver.session() as s:
        result = s.run(
            "MATCH (a)<-[:SUBJECT]-(r:QH30Revision {slice_id:$id})-[:OBJECT]->(b) RETURN count(r) AS n,collect(a.category+'->'+b.category) AS shapes",
            id=graph.key(A),
        ).single()
        assert result["n"] == 3 and set(result["shapes"]) == {
            "item->entity",
            "item->item",
            "relation->item",
        }
    before = repo.sync_status((A,))
    repo.save(sources=records(A)[0], revisions=rows)
    assert project(pipeline) == 0 and repo.sync_status((A,)) == before


def test_update_preserves_history_and_blocks_even_empty_results(pipeline):
    repo = pipeline[0]
    project(pipeline)
    old, new = updated(pipeline)
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Absent")
    assert project(pipeline) == 1
    assert (
        str(retrieve(pipeline, "Updated").hits[0].item_revision.item_id)
        == new["item_id"]
    )
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


def test_failed_rebuild_transaction_retains_old_epoch_and_canonical_data(
    pipeline, monkeypatch
):
    repo, _, graph, _, _ = pipeline
    project(pipeline)
    before = graph.markers((A,))
    _, new = updated(pipeline)
    original = NativeContextEngine.replace

    def poison(engine, snapshot, *, generation, transaction_guard=None):
        revision = snapshot["understanding_item_revisions"][0]["id"]
        with engine.driver.session() as s:
            s.run(
                "CREATE (:QH30Revision {key:$key,fingerprint:'conflict',slice_id:$id,generation:$g})",
                key=engine.slice_id + ":" + generation + ":" + revision,
                id=engine.slice_id,
                g=generation,
            ).consume()
        return original(
            engine, snapshot, generation=generation, transaction_guard=transaction_guard
        )

    with monkeypatch.context() as patch:
        patch.setattr(NativeContextEngine, "replace", poison)
        with pytest.raises(NativeContextError, match="immutable"):
            ProjectionWorker(repo, graph, (A,)).rebuild(A)
    assert graph.markers((A,)) == before
    assert repo.read_snapshot((A,), [new["id"]])["understanding_item_revisions"]
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Updated")
    ProjectionWorker(repo, graph, (A,)).rebuild(A)
    assert len(retrieve(pipeline, "Updated").hits) == 1


def test_rebuild_lost_sql_ack_fails_closed_and_retries(pipeline, monkeypatch):
    from contextlib import contextmanager

    repo, _, graph, _, _ = pipeline
    project(pipeline)
    connect, publish = repo.connect, NativeContextEngine.replace
    graph_committed = False

    @contextmanager
    def lost_ack(**kwargs):
        with connect(**kwargs) as c:
            yield c
            if graph_committed:
                raise ConnectionError("Synthetic rebuild SQL acknowledgement lost")

    def commit_graph(*args, **kwargs):
        nonlocal graph_committed
        result = publish(*args, **kwargs)
        graph_committed = True
        return result

    with monkeypatch.context() as patch:
        patch.setattr(repo, "connect", lost_ack)
        patch.setattr(NativeContextEngine, "replace", commit_graph)
        with pytest.raises(ConnectionError):
            ProjectionWorker(repo, graph, (A,)).rebuild(A)
    with pytest.raises(NativeContextError, match="rebuild"):
        retrieve(pipeline, "Absent")
    ProjectionWorker(repo, graph, (A,)).rebuild(A)
    assert len(retrieve(pipeline).hits) == 3


def test_second_context_projects_independently(pipeline):
    repo, bob, graph, service, _ = pipeline
    project(pipeline)
    drain(ProjectionWorker(bob, graph, (B,)))
    other = AuthorizedNativeContextService(
        policy=service.policy, engine=IncrementalContextEngine(bob, graph)
    )

    def query(text):
        return asyncio.run(
            other.retrieve(
                ContextRequest(
                    subject_id=SubjectId(bob.subject_id),
                    query=ContextQuery(text=text, context_ids=(B,)),
                )
            )
        )

    assert len(query("Birch").hits) == 3 and not query("Cedar").hits
    assert len(retrieve(pipeline).hits) == 3


def test_empty_scope_requires_no_reconciliation(pipeline):
    repo, _, graph, _, _ = pipeline
    scope = str(uuid4())
    with repo.connect() as c:
        c.execute(
            "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Empty')",
            (scope, repo.subject_id),
        )
    assert not retrieve(pipeline, "New", scopes=(scope,)).hits
    source, row = deepcopy(records(A)[0][0]), deepcopy(records(A)[1][0])
    source.update(id=str(uuid4()), source_id=str(uuid4()), context_space_id=scope)
    row.update(
        id=str(uuid4()),
        item_id=str(uuid4()),
        context_space_id=scope,
        provenance=[source["id"]],
    )
    row["content"]["text"] = "New synthetic content"
    repo.save(sources=[source], revisions=[row])
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "New", scopes=(scope,))
    drain(ProjectionWorker(repo, graph, (scope,)))
    assert len(retrieve(pipeline, "New", scopes=(scope,)).hits) == 1


def test_change_during_projection_remains_pending_until_next_event(
    pipeline, monkeypatch
):
    repo, _, graph, _, _ = pipeline
    project(pipeline)
    _, second = updated(pipeline)
    third = deepcopy(second)
    third.update(id=str(uuid4()), revision_no=3, based_on_revision_id=second["id"])
    third["content"]["text"] = "Third synthetic update"
    original = graph.apply

    def advance(*args, **kwargs):
        result = original(*args, **kwargs)
        repo.save(revisions=[third])
        return result

    with monkeypatch.context() as patch:
        patch.setattr(graph, "apply", advance)
        assert ProjectionWorker(repo, graph, (A,)).run_once()
    with pytest.raises(NativeContextError, match="pending"):
        retrieve(pipeline, "Absent")
    assert project(pipeline) == 1
    assert len(retrieve(pipeline, "Third").hits) == 1


def test_graph_temporal_tampering_requires_explicit_rebuild(pipeline):
    repo, _, graph, _, _ = pipeline
    project(pipeline)
    with graph.driver.session() as s:
        s.run(
            "MATCH (r:QH30Revision {slice_id:$id}) WHERE r.text CONTAINS 'Cedar' SET r.fact_from='invented'",
            id=graph.key(A),
        ).consume()
    with pytest.raises(NativeContextError):
        retrieve(pipeline)
    ProjectionWorker(repo, graph, (A,)).rebuild(A)
    assert retrieve(pipeline).hits


def test_explicit_rebuild_recovers_partial_graph_loss(pipeline):
    repo, _, graph, _, _ = pipeline
    project(pipeline)
    prior = repo.sync_status((A,))[0]["epoch"]
    with graph.driver.session() as s:
        s.run(
            "MATCH (r:QH30Revision {slice_id:$id}) WHERE r.text CONTAINS 'Cedar' DETACH DELETE r",
            id=graph.key(A),
        ).consume()
    # Ordinary reads never certify arbitrary external deletion with a full scan.
    epoch = ProjectionWorker(repo, graph, (A,)).rebuild(A)
    assert epoch != prior and len(retrieve(pipeline).hits) == 3


def test_candidate_hydration_failure_preserves_sql_cause(pipeline, monkeypatch):
    project(pipeline)

    def unavailable(*args):
        raise psycopg.OperationalError("Synthetic SQL unavailable")

    monkeypatch.setattr(pipeline[0], "read_snapshot", unavailable)
    with pytest.raises(NativeContextError, match="Canonical read") as error:
        retrieve(pipeline)
    assert isinstance(error.value.__cause__, psycopg.OperationalError)


def test_rebuilds_serialize_on_the_scope_state_lock(pipeline, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import time

    repo, _, graph, _, _ = pipeline
    project(pipeline)
    entered, release, calls = Event(), Event(), []
    original = NativeContextEngine.replace

    def slow(*args, **kwargs):
        calls.append(kwargs["generation"])
        if len(calls) == 1:
            entered.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(NativeContextEngine, "replace", slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(ProjectionWorker(repo, graph, (A,)).rebuild, A)
        assert entered.wait(5)
        two = pool.submit(ProjectionWorker(repo, graph, (A,)).rebuild, A)
        try:
            deadline = time.monotonic() + 5
            with repo.connect(autocommit=True) as c:
                while not c.execute(
                    "SELECT count(*) AS n FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'"
                ).fetchone()["n"]:
                    assert time.monotonic() < deadline
                    time.sleep(0.02)
            assert len(calls) == 1
        finally:
            release.set()
        first, second = one.result(timeout=10), two.result(timeout=10)
    assert first != second and repo.sync_status((A,))[0]["epoch"] == second
    assert len(retrieve(pipeline).hits) == 3
