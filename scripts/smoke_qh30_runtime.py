"""Explicit synthetic write probe; requires an already running backend worker.

Retains its immutable synthetic rows. Never starts a worker or applies migrations.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))

from neo4j import GraphDatabase  # noqa: E402
from adapters.context.incremental import IncrementalContextEngine, IncrementalProjector  # noqa: E402
from adapters.context.native import AuthorizedNativeContextService  # noqa: E402
from adapters.postgres.canonical import CanonicalRepository  # noqa: E402
from adapters.postgres.config import database_url  # noqa: E402
from adapters.postgres.security import PostgresSecurityReader  # noqa: E402
from app.core.models import ContextQuery, ContextRequest, SubjectId  # noqa: E402
from app.policy.owner import OwnerPolicyService  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-synthetic", action="store_true", required=True)
    parser.parse_args()
    if os.environ.get("QH_NATIVE_CONTEXT_ENABLED") != "true":
        raise SystemExit("Native runtime must be explicitly enabled")
    namespace = os.environ["QH_NATIVE_GRAPH_NAMESPACE"]
    url = database_url()
    owner, foreign, scope = (str(uuid4()) for _ in range(3))
    repo = CanonicalRepository(url=url, subject_id=owner)
    with repo.connect() as c:
        if c.execute("SELECT version_num FROM alembic_version").fetchone()["version_num"] != "0004_projection_outbox":
            raise SystemExit("Requires explicitly migrated 0004 schema")
        for subject in (owner, foreign):
            c.execute("INSERT INTO users(id,display_name) VALUES (%s,'QH native synthetic smoke')", (subject,))
        c.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic cutover smoke')", (scope, owner))
    source = dict(id=str(uuid4()), source_id=str(uuid4()), context_space_id=scope,
                  revision_no=1, content="Synthetic team chooses Cedar.",
                  origin={"locator": "synthetic://qh30-runtime-smoke", "acquired_at": datetime.now(timezone.utc).isoformat()})
    revision = dict(id=str(uuid4()), item_id=str(uuid4()), context_space_id=scope,
                    revision_no=1, type_id="qh.decision", type_version=1,
                    content={"text": "Synthetic team chooses Cedar."},
                    origin_kind="import", validation_state="proposed",
                    validated_by=None, validated_at=None, based_on_revision_id=None,
                    provenance=[source["id"]])
    repo.save(sources=[source], revisions=[revision])
    # This probe deliberately does not claim/process events. Only the application
    # backend worker can make this newly created scope ready.
    deadline = time.monotonic() + 30
    while repo.sync_status((scope,))[0]["sync_state"] != "ready":
        if time.monotonic() >= deadline:
            raise SystemExit("FAIL: backend worker did not synchronize the synthetic scope")
        time.sleep(0.1)
    policy = OwnerPolicyService(owner_for=PostgresSecurityReader(url=url).owner_for)
    with GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]), max_transaction_retry_time=5) as driver:
        service = AuthorizedNativeContextService(policy=policy, engine=IncrementalContextEngine(repo, IncrementalProjector(driver, namespace=namespace)))
        def request(subject):
            return ContextRequest(subject_id=SubjectId(subject), query=ContextQuery(text="Cedar", context_ids=(scope,)))
        result = asyncio.run(service.retrieve(request(owner)))
        assert len(result.hits) == 1
        assert str(result.hits[0].item_revision.revision_id) == revision["id"]
        assert str(result.hits[0].provenance[0].revision_id) == source["id"]
        try:
            asyncio.run(service.retrieve(request(foreign)))
        except PermissionError:
            pass
        else:
            raise AssertionError("Foreign subject was not denied")
    print("PASS: backend worker -> authorized graph retrieval -> canonical hydration; foreign subject denied")
    print("Retained synthetic Context Space:", scope)


if __name__ == "__main__":
    main()
