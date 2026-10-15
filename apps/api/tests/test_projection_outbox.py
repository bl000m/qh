"""Real 0004 outbox/worker tests, only dedicated SQL/Neo4j instances."""

import asyncio
from copy import deepcopy
from uuid import uuid4

from alembic import command
from alembic.config import Config
import psycopg
import pytest

from adapters.context.incremental import (
    IncrementalContextEngine,
    IncrementalProjector,
    ProjectionWorker,
    ProjectionOrderError,
)
from adapters.context.native import AuthorizedNativeContextService, NativeContextError
from app.core.models import ContextQuery, ContextRequest, SubjectId
from tests.test_canonical_graph_pipeline import pipeline as legacy_pipeline
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import A, B, real_engine as real_engine
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)


@pytest.fixture
def inc(legacy_pipeline):
    repo, bob, old, service, rows = legacy_pipeline
    command.upgrade(Config("adapters/postgres/alembic.ini"), "0004_projection_outbox")
    projector = IncrementalProjector(
        old.driver, namespace="qh30-inc-" + repo.url.database
    )
    projector.initialize()
    worker = ProjectionWorker(repo, projector, (A,))
    engine = IncrementalContextEngine(repo, projector)
    return dict(
        repo=repo,
        bob=bob,
        projector=projector,
        worker=worker,
        engine=engine,
        service=AuthorizedNativeContextService(policy=service.policy, engine=engine),
        rows=rows,
    )


def drain(worker):
    count = 0
    for _ in range(100):
        event = worker.claim()
        if event is None:
            return count
        assert worker.process(event), repr(worker.last_error)
        count += 1
    raise AssertionError("Unexpected unbounded queue")


def query(p, text="Cedar", scopes=(A,), subject=None):
    return asyncio.run(
        p["service"].retrieve(
            ContextRequest(
                subject_id=SubjectId(subject or p["repo"].subject_id),
                query=ContextQuery(text=text, context_ids=scopes, limit=100),
            )
        )
    )


def change(p, text="Incremental synthetic update"):
    old = next(r for r in p["rows"] if r["type_id"] == "qh.decision")
    new = deepcopy(old)
    new.update(id=str(uuid4()), revision_no=2, based_on_revision_id=old["id"])
    new["content"]["text"] = text
    p["repo"].save(revisions=[new])
    return new


def retry_now(p):
    with p["repo"].connect() as c:
        c.execute(
            "UPDATE projection_outbox SET available_at=clock_timestamp() WHERE state='failed'"
        )


def test_backfill_and_atomic_intent_without_canonical_rewrite(inc):
    repo = inc["repo"]
    before = repo.read_snapshot((A,))
    status = repo.sync_status((A,))[0]
    assert (
        status["desired_version"] == len(inc["rows"]) and status["applied_version"] == 0
    )
    with pytest.raises(NativeContextError, match="pending"):
        query(inc)
    assert drain(inc["worker"]) == len(inc["rows"])
    assert len(query(inc).hits) == 3
    repo.save(revisions=inc["rows"])
    assert repo.sync_status((A,))[0]["desired_version"] == status["desired_version"]
    assert repo.read_snapshot((A,)) == before
    bad = deepcopy(inc["rows"][0])
    bad.update(id=str(uuid4()), revision_no=2, type_id="unknown.type")
    good = deepcopy(inc["rows"][1])
    good.update(id=str(uuid4()), revision_no=2)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repo.save(revisions=[good, bad])
    assert repo.sync_status((A,))[0]["desired_version"] == status["desired_version"]


def test_one_update_and_query_never_scan_scope(inc, monkeypatch):
    drain(inc["worker"])
    repo = inc["repo"]
    calls = []
    original = repo.read_snapshot

    def bounded(scopes, revision_ids=None):
        assert revision_ids is not None, (
            "Ordinary incremental path attempted a full scope read"
        )
        calls.append(tuple(revision_ids))
        return original(scopes, revision_ids)

    monkeypatch.setattr(repo, "read_snapshot", bounded)
    new = change(inc)
    with pytest.raises(NativeContextError, match="pending"):
        query(inc, "Incremental")
    assert inc["worker"].run_once()
    assert inc["worker"].last_revision_ids == (new["id"],)
    assert inc["worker"].last_applied_rows == 1
    hits = query(inc, "Incremental").hits
    assert len(hits) == 1 and hits[0].item_revision.revision_id == new["id"]
    assert calls and all(len(ids) == 1 for ids in calls)
    assert not query(inc, "Absent synthetic content").hits


def test_graph_failure_does_not_lose_canonical_data_and_retries(inc, monkeypatch):
    drain(inc["worker"])
    new = change(inc)

    def unavailable(*args):
        raise ConnectionError("Synthetic Neo4j unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(inc["projector"], "apply", unavailable)
        assert not inc["worker"].run_once()
    state = inc["repo"].sync_status((A,))[0]
    assert (
        state["next_state"] == "failed"
        and state["error_code"] == "projection_error"
        and state["attempts"] == 1
    )
    assert state["lag_seconds"] >= 0
    assert inc["repo"].read_snapshot((A,), [new["id"]])["understanding_item_revisions"]
    with pytest.raises(NativeContextError, match="pending"):
        query(inc, "Incremental")
    retry_now(inc)
    restarted = ProjectionWorker(inc["repo"], inc["projector"], (A,))
    assert restarted.run_once() and len(query(inc, "Incremental").hits) == 1


def test_expired_lease_recovers_after_worker_crash_and_fences_ack(inc):
    drain(inc["worker"])
    change(inc)
    abandoned = inc["worker"].claim()
    assert (
        abandoned
        and not ProjectionWorker(inc["repo"], inc["projector"], (A,)).run_once()
    )
    with inc["repo"].connect() as c:
        c.execute(
            "UPDATE projection_outbox SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s",
            (abandoned["id"],),
        )
    restarted = ProjectionWorker(inc["repo"], inc["projector"], (A,))
    replacement = restarted.claim()
    assert replacement["lease_token"] != abandoned["lease_token"]
    assert restarted.process(replacement)
    assert not inc["worker"]._finish(abandoned)
    assert len(query(inc, "Incremental").hits) == 1


def test_lost_ack_and_duplicate_do_not_reapply_or_regress(inc, monkeypatch):
    drain(inc["worker"])
    new = change(inc)
    original = inc["worker"]._finish

    def lost_ack(event, *, error=None):
        if error is None:
            raise ConnectionError("Synthetic PostgreSQL ack lost")
        return original(event, error=error)

    with monkeypatch.context() as patch:
        patch.setattr(inc["worker"], "_finish", lost_ack)
        assert not inc["worker"].run_once()
    retry_now(inc)
    assert inc["worker"].run_once() and inc["worker"].last_applied_rows == 0
    assert len(query(inc, "Incremental").hits) == 1
    epoch = inc["repo"].sync_status((A,))[0]["epoch"]
    with inc["projector"].driver.session() as s:
        n = s.run(
            "MATCH (r:QH30Revision {slice_id:$key,generation:$epoch}) RETURN count(r) AS n",
            key=inc["projector"].key(A),
            epoch=epoch,
        ).single()["n"]
        assert n == len(inc["rows"]) + 1
        head = s.run(
            "MATCH (i:QH30Item {key:$key}) RETURN i.latest_revision_no AS n",
            key=inc["projector"].key(A) + ":" + epoch + ":item:" + new["item_id"],
        ).single()
        assert head["n"] == 2


def test_out_of_order_is_deferred_and_old_duplicate_cannot_regress(inc):
    drain(inc["worker"])
    new = change(inc)
    later = deepcopy(new)
    later.update(id=str(uuid4()), revision_no=3, based_on_revision_id=new["id"])
    later["content"]["text"] = "Third synthetic revision"
    inc["repo"].save(revisions=[later])
    event = inc["worker"].claim()
    snapshot = inc["repo"].read_affected_snapshot(A, new["id"])
    future = dict(event, scope_version=event["scope_version"] + 1)
    with pytest.raises(ProjectionOrderError, match="Out-of-order"):
        inc["projector"].apply(future, snapshot, None)
    assert inc["worker"].process(event)
    assert inc["worker"].run_once()
    assert inc["projector"].apply(event, snapshot, None) == 0
    assert len(query(inc, "Third").hits) == 1
    state = inc["repo"].sync_status((A,))[0]
    assert state["desired_version"] == state["applied_version"]


def test_owner_isolation_and_two_contexts(inc):
    drain(inc["worker"])
    other = ProjectionWorker(inc["bob"], inc["projector"], (B,))
    drain(other)
    from app.policy.owner import OwnerPolicyService
    from adapters.postgres.security import PostgresSecurityReader

    service = AuthorizedNativeContextService(
        policy=OwnerPolicyService(
            owner_for=PostgresSecurityReader(url=inc["repo"].url).owner_for
        ),
        engine=IncrementalContextEngine(inc["bob"], inc["projector"]),
    )

    def bquery(text):
        return asyncio.run(
            service.retrieve(
                ContextRequest(
                    subject_id=SubjectId(inc["bob"].subject_id),
                    query=ContextQuery(text=text, context_ids=(B,)),
                )
            )
        )

    assert len(bquery("Birch").hits) == 3 and not bquery("Cedar").hits
    with pytest.raises(PermissionError):
        query(inc, scopes=(A, B))
    with pytest.raises(PermissionError):
        ProjectionWorker(inc["repo"], inc["projector"], (B,)).claim()


def test_rebuild_is_explicit_and_fences_old_worker(inc):
    drain(inc["worker"])
    change(inc)
    abandoned = inc["worker"].claim()
    before = inc["repo"].sync_status((A,))[0]
    epoch = inc["worker"].rebuild(A)
    assert epoch != before["epoch"]
    assert not inc["worker"].process(abandoned)
    assert len(query(inc, "Incremental").hits) == 1
    assert not inc["worker"].run_once()
    with inc["projector"].driver.session() as s:
        s.run(
            "MATCH (m:QH30Sync {key:$key}) DETACH DELETE m", key=inc["projector"].key(A)
        ).consume()
    with pytest.raises(NativeContextError, match="rebuild"):
        query(inc)
    inc["worker"].rebuild(A)
    assert len(query(inc).hits) == 3


def test_deferred_validation_rolls_back_intent_and_counter(inc):
    before = inc["repo"].sync_status((A,))[0]["desired_version"]
    row = deepcopy(next(r for r in inc["rows"] if r["type_id"] == "qh.observation"))
    row.update(id=str(uuid4()), revision_no=2)
    row["content"] = {"text": 99}
    with pytest.raises(psycopg.errors.CheckViolation):
        inc["repo"].save(revisions=[row])
    assert inc["repo"].sync_status((A,))[0]["desired_version"] == before
    with inc["repo"].connect() as c:
        assert not c.execute(
            "SELECT id FROM projection_outbox WHERE revision_id=%s", (row["id"],)
        ).fetchone()


def test_current_pointer_intents_and_stale_delivery(inc):
    drain(inc["worker"])
    row = deepcopy(next(r for r in inc["rows"] if r["type_id"] == "qh.decision"))
    row.update(
        id=str(uuid4()),
        revision_no=2,
        validation_state="confirmed",
        validated_by=inc["repo"].subject_id,
        validated_at="2026-10-15T10:00:00Z",
    )
    inc["repo"].save(revisions=[row])
    with inc["repo"].connect() as c:
        c.execute(
            "UPDATE understanding_items SET current_revision_id=%s WHERE id=%s",
            (row["id"], row["item_id"]),
        )
    assert drain(inc["worker"]) == 2
    with inc["repo"].connect() as c:
        event = c.execute(
            "SELECT o.*,s.epoch FROM projection_outbox o JOIN context_projection_state s USING(context_space_id) WHERE o.context_space_id=%s ORDER BY scope_version DESC LIMIT 1",
            (A,),
        ).fetchone()
        c.execute(
            "UPDATE understanding_items SET current_revision_id=NULL WHERE id=%s",
            (row["item_id"],),
        )
    assert drain(inc["worker"]) == 1
    assert (
        inc["projector"].apply(
            event, inc["repo"].read_affected_snapshot(A, row["id"]), None
        )
        == 0
    )
    with inc["projector"].driver.session() as s:
        head = s.run(
            "MATCH (i:QH30Item {key:$key}) RETURN i.current_revision_id AS selected,i.latest_revision_no AS number",
            key=inc["projector"].key(A)
            + ":"
            + inc["repo"].sync_status((A,))[0]["epoch"]
            + ":item:"
            + row["item_id"],
        ).single()
        assert head["selected"] is None and head["number"] == 2


def test_real_bolt_connection_failure_is_retryable(inc):
    from neo4j import GraphDatabase

    drain(inc["worker"])
    change(inc)
    # Real local network refusal, never an external service or the persistent graph.
    import os

    with GraphDatabase.driver(
        "bolt://qh30-native-neo4j-test:1",
        auth=("neo4j", os.environ["QH30_TEST_NEO4J_PASSWORD"]),
        connection_timeout=0.3,
        max_transaction_retry_time=0,
    ) as driver:
        unavailable = IncrementalProjector(driver, namespace=inc["projector"].namespace)
        failed = ProjectionWorker(inc["repo"], unavailable, (A,))
        assert not failed.run_once()
    state = inc["repo"].sync_status((A,))[0]
    assert (
        state["sync_state"] == "failed" and state["error_type"] == "ServiceUnavailable"
    )
    retry_now(inc)
    assert inc["worker"].run_once()
    assert inc["repo"].sync_status((A,))[0]["sync_state"] == "ready"


def test_worker_loop_survives_temporary_sql_failure(inc, monkeypatch):
    from threading import Event, Thread
    import time

    original = inc["worker"].claim
    calls = []

    def intermittent():
        calls.append(1)
        if len(calls) == 1:
            raise psycopg.OperationalError("Synthetic unavailable SQL")
        return original()

    monkeypatch.setattr(inc["worker"], "claim", intermittent)
    stop = Event()
    thread = Thread(
        target=inc["worker"].run, args=(stop,), kwargs={"poll_seconds": 0.01}
    )
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while inc["repo"].sync_status((A,))[0]["sync_state"] != "ready":
            assert time.monotonic() < deadline
            time.sleep(0.02)
    finally:
        stop.set()
        thread.join(timeout=5)
    assert not thread.is_alive() and len(calls) > 1
    assert len(query(inc).hits) == 3


def test_intent_identity_is_not_mutable(inc):
    with inc["repo"].connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        c.execute(
            "UPDATE projection_outbox SET scope_version=scope_version+100 WHERE context_space_id=%s",
            (A,),
        )


def test_0004_identity_writer_remains_compatible(inc):
    from adapters.postgres.demo_identities import (
        require_identity_schema,
        provision_demo,
    )
    from psycopg.rows import tuple_row

    with inc["repo"].connect() as c:
        c.row_factory = tuple_row
        require_identity_schema(c)
        provision_demo(c, issuer="synthetic://outbox-test")
        provision_demo(c, issuer="synthetic://outbox-test")
        assert c.execute("SELECT count(*) FROM user_identities").fetchone() == (2,)


def test_old_lease_can_write_graph_but_cannot_ack_new_lease(inc):
    drain(inc["worker"])
    change(inc)
    old = inc["worker"].claim()
    with inc["repo"].connect() as c:
        c.execute(
            "UPDATE projection_outbox SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s",
            (old["id"],),
        )
    second = ProjectionWorker(inc["repo"], inc["projector"], (A,))
    new = second.claim()
    assert not inc["worker"].process(old)
    state = inc["repo"].sync_status((A,))[0]
    assert (
        state["sync_state"] == "processing"
        and state["desired_version"] > state["applied_version"]
    )
    assert second.process(new) and second.last_applied_rows == 0
    assert len(query(inc, "Incremental").hits) == 1


def test_scope_sequence_is_gap_free_after_concurrent_rollback(inc):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from tests.test_native_semantics_sql import publish

    drain(inc["worker"])
    repo = inc["repo"]
    before = repo.sync_status((A,))[0]["desired_version"]
    data = {
        "owner": repo.subject_id,
        "space": A,
        "source_revision": inc["rows"][0]["provenance"][0],
    }
    first_item = next(
        r["item_id"] for r in inc["rows"] if r["type_id"] == "qh.decision"
    )
    second_item = next(
        r["item_id"] for r in inc["rows"] if r["type_id"] == "qh.hypothesis"
    )
    app = "qh30_scope_sequence_" + uuid4().hex

    def second():
        with repo.connect() as c:
            c.execute("SELECT set_config('application_name',%s,false)", (app,))
            c.execute("SET statement_timeout='8s'")
            return publish(c, data, item=second_item, number=2, type_id="qh.hypothesis")

    with repo.connect() as first, ThreadPoolExecutor(max_workers=1) as pool:
        abandoned = publish(first, data, item=first_item, number=2)
        pending = pool.submit(second)
        try:
            deadline = time.monotonic() + 5
            while True:
                row = first.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE application_name=%s",
                    (app,),
                ).fetchone()
                if row and row["wait_event_type"] == "Lock":
                    break
                assert time.monotonic() < deadline
                time.sleep(0.02)
                first.execute("SELECT pg_stat_clear_snapshot()")
        finally:
            first.rollback()
        committed = pending.result(timeout=8)
    assert repo.sync_status((A,))[0]["desired_version"] == before + 1
    assert not repo.read_snapshot((A,), [abandoned[1]])["understanding_item_revisions"]
    assert repo.read_snapshot((A,), [committed[1]])["understanding_item_revisions"]
    assert drain(inc["worker"]) == 1


def test_new_empty_space_bootstraps_state_and_first_intent(inc, monkeypatch):
    import json

    scope = str(uuid4())
    repo = inc["repo"]
    with repo.connect() as c:
        c.execute(
            "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'New synthetic scope')",
            (scope, repo.subject_id),
        )
    assert repo.sync_status((scope,))[0]["desired_version"] == 0
    original = repo.read_snapshot

    def bounded(scopes, revision_ids=None):
        assert revision_ids is not None, "New-space path attempted full snapshot"
        return original(scopes, revision_ids)

    monkeypatch.setattr(repo, "read_snapshot", bounded)
    assert not query(inc, scopes=(scope,)).hits
    from tests.test_canonical_graph_pipeline import records

    source = deepcopy(records(A)[0][0])
    source.update(id=str(uuid4()), source_id=str(uuid4()), context_space_id=scope)
    row = deepcopy(inc["rows"][0])
    row.update(
        id=str(uuid4()),
        item_id=str(uuid4()),
        context_space_id=scope,
        provenance=[source["id"]],
    )
    repo.save(sources=[source], revisions=[row])
    assert repo.sync_status((scope,))[0]["desired_version"] == 1
    with pytest.raises(NativeContextError, match="pending"):
        query(inc, scopes=(scope,))
    worker = ProjectionWorker(repo, inc["projector"], (scope,))
    assert worker.run_once() and len(query(inc, scopes=(scope,)).hits) == 1
    assert json.dumps(repo.sync_status((scope,)))
