"""Application factory/lifespan against the real dedicated SQL and Neo4j servers."""

import asyncio
import json
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

from alembic import command
from fastapi.testclient import TestClient
import pytest

from adapters.context.native import NativeContextError
from app.bootstrap import create_runtime_app
from app.core.models import ContextQuery, ContextRequest, SubjectId
from tests.test_canonical_graph_pipeline import pipeline as pipeline, records
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import A, B, real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only


def wait_until(check):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.05)
    raise AssertionError("Runtime did not reach expected state within 20s")


def retrieve(runtime, subject, scopes, text="Cedar"):
    return asyncio.run(runtime.context_for(subject).retrieve(ContextRequest(
        subject_id=SubjectId(subject),
        query=ContextQuery(text=text, context_ids=scopes, limit=100),
    )))


def configure(monkeypatch, namespace):
    monkeypatch.setenv("QH_NATIVE_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("QH_NATIVE_GRAPH_NAMESPACE", namespace)
    monkeypatch.setenv("NEO4J_URI", os.environ["QH30_TEST_NEO4J_URI"])
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", os.environ["QH30_TEST_NEO4J_PASSWORD"])


@pytest.mark.parametrize("schema", ["0004_projection_outbox", "0005_retire_legacy_category"])
def test_application_runtime_end_to_end_restart_and_error_recovery(pipeline, monkeypatch, caplog, schema):
    repo, bob, graph, _, rows = pipeline
    from alembic.config import Config
    command.upgrade(Config("adapters/postgres/alembic.ini"), schema)
    from adapters.postgres.semantic_profiles import register_generic_profiles
    register_generic_profiles(repo)
    namespace = "qh30-runtime-" + uuid4().hex
    configure(monkeypatch, namespace)
    runtimes = []
    try:
        with TestClient(create_runtime_app()) as client:
            runtime = client.app.state.native_context
            runtimes.append(runtime)
            assert client.get("/health").status_code == 200
            wait_until(lambda: repo.sync_status((A,))[0]["sync_state"] == "ready")
            wait_until(lambda: bob.sync_status((B,))[0]["sync_state"] == "ready")
            assert len(retrieve(runtime, repo.subject_id, (A,)).hits) == 3
            assert len(retrieve(runtime, bob.subject_id, (B,), "Birch").hits) == 3
            assert not retrieve(runtime, bob.subject_id, (B,)).hits
            with pytest.raises(PermissionError):
                retrieve(runtime, repo.subject_id, (B,))

            original_apply = runtime.projector.apply
            def fail(*args):
                raise ConnectionError("synthetic-private-message-never-logged")
            monkeypatch.setattr(runtime.projector, "apply", fail)
            source = deepcopy(records(A)[0][0])
            source.update(id=str(uuid4()), source_id=str(uuid4()), revision_no=1)
            updated = deepcopy(next(r for r in rows if r["type_id"] == "qh.decision"))
            updated.update(id=str(uuid4()), revision_no=2, based_on_revision_id=updated["id"])
            updated["content"]["text"] = "Cedar runtime incremental decision"
            updated["provenance"] = [source["id"]]
            runtime.repository(repo.subject_id).save(sources=[source], revisions=[updated])
            wait_until(lambda: runtime.last_error_type == "ConnectionError")
            assert repo.read_snapshot((A,), (updated["id"],))["understanding_item_revisions"]
            with pytest.raises(NativeContextError, match="pending"):
                retrieve(runtime, repo.subject_id, (A,), "runtime incremental")
            monkeypatch.setattr(runtime.projector, "apply", original_apply)
            # Shutdown with failed durable work; next application instance retries.
        assert not runtimes[0].thread
        with TestClient(create_runtime_app()) as client:
            runtime = client.app.state.native_context
            runtimes.append(runtime)
            wait_until(lambda: repo.sync_status((A,))[0]["sync_state"] == "ready")
            result = retrieve(runtime, repo.subject_id, (A,), "runtime incremental")
            assert len(result.hits) == 1
            assert str(result.hits[0].item_revision.revision_id) == updated["id"]
            assert runtime.thread.is_alive()
            probe = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[3] / "scripts/smoke_qh30_runtime.py"), "--write-synthetic"],
                capture_output=True, text=True, timeout=40,
            )
            assert probe.returncode == 0, probe.stdout + probe.stderr
            assert "PASS: backend worker" in probe.stdout
            retained = json.loads(probe.stdout.strip().splitlines()[-1])
        # Recreate the actual application runtime, then verify the very same IDs
        # via the read-only probe. No second source/import/extraction is needed.
        with TestClient(create_runtime_app()):
            checked = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[3] / "scripts/smoke_qh30_runtime.py"),
                 "--verify-scope", retained["scope"], "--owner-id", retained["owner"]],
                capture_output=True, text=True, timeout=40,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert json.loads(checked.stdout.strip().splitlines()[-1]) == retained
        assert all(r.thread is None for r in runtimes)
        assert "synthetic-private-message-never-logged" not in caplog.text
        assert "ConnectionError" in caplog.text
        assert str(result.hits[0].provenance[0].revision_id) == source["id"]
    finally:
        with graph.driver.session() as session:
            session.run("MATCH (n) WHERE n.key STARTS WITH $prefix OR n.id STARTS WITH $prefix OR n.slice_id STARTS WITH $prefix DETACH DELETE n", prefix=namespace + ":").consume()


def test_native_start_refuses_old_schema_without_migration(empty_database, real_engine, monkeypatch):
    command.upgrade(empty_database, "0003_native_semantics")
    configure(monkeypatch, "qh30-runtime-old-" + uuid4().hex)
    with pytest.raises(RuntimeError, match="requires migration 0004"):
        with TestClient(create_runtime_app()):
            pass


def test_runtime_disabled_keeps_existing_factory_behavior(monkeypatch):
    monkeypatch.setenv("QH_NATIVE_CONTEXT_ENABLED", "false")
    with TestClient(create_runtime_app()) as client:
        assert client.app.state.native_context is None
        assert client.get("/health").status_code == 200


def test_0005_separate_backend_process_recovers_pending_intent(pipeline, monkeypatch):
    """Actual Uvicorn process exit/restart; no in-memory runtime object is reused."""
    from alembic.config import Config
    from adapters.postgres.semantic_profiles import register_generic_profiles
    from adapters.context.incremental import IncrementalContextEngine, IncrementalProjector
    from adapters.context.native import AuthorizedNativeContextService

    repo, _, graph, service, rows = pipeline
    command.upgrade(Config("adapters/postgres/alembic.ini"), "0005_retire_legacy_category")
    register_generic_profiles(repo)
    namespace = "qh005-process-" + uuid4().hex
    configure(monkeypatch, namespace)
    processes = []

    def start():
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.bootstrap:create_runtime_app", "--factory",
             "--host", "127.0.0.1", "--port", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        processes.append(process)
        return process

    def ready(process):
        assert process.poll() is None, "Temporary backend process failed"
        return repo.sync_status((A,))[0]["sync_state"] == "ready"

    try:
        first = start()
        wait_until(lambda: ready(first))
        first.terminate()
        # Uvicorn may re-raise SIGTERM after graceful lifespan shutdown.
        assert first.wait(timeout=30) in (0, -15)
        proposal = deepcopy(rows[0])
        proposal.update(id=str(uuid4()), item_id=str(uuid4()), revision_no=1,
                        type_id="qh.generic.item", based_on_revision_id=None)
        proposal["content"] = {"text": "Cedar pending process restart",
                               "descriptors": [{"value": "reversible_pause", "certainty": "asserted"}]}
        repo.save(revisions=[proposal])
        assert repo.sync_status((A,))[0]["sync_state"] == "pending"
        second = start()
        assert first.pid != second.pid
        wait_until(lambda: ready(second))
        reader = AuthorizedNativeContextService(policy=service.policy,
            engine=IncrementalContextEngine(repo, IncrementalProjector(graph.driver, namespace=namespace)))
        result = asyncio.run(reader.select_descriptors(subject_id=SubjectId(repo.subject_id),
            context_ids=(A,), values=["reversible_pause"]))
        assert [str(h.item_revision.revision_id) for h in result.hits] == [proposal["id"]]
        assert str(result.hits[0].provenance[0].revision_id) == proposal["provenance"][0]
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
        with graph.driver.session() as session:
            session.run("MATCH (n) WHERE n.key STARTS WITH $prefix OR n.id STARTS WITH $prefix OR n.slice_id STARTS WITH $prefix DETACH DELETE n", prefix=namespace + ":").consume()
