"""Synthetic native probe, or read-only verification of a retained smoke scope.

Never starts a worker, provisions schemas/profiles or deletes retained records.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from uuid import UUID, uuid4

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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-synthetic", action="store_true")
    mode.add_argument("--verify-scope", type=UUID)
    parser.add_argument("--owner-id", type=UUID)
    args = parser.parse_args()
    if args.verify_scope and not args.owner_id:
        parser.error("Read-only verification requires the retained owner ID")
    if os.environ.get("QH_NATIVE_CONTEXT_ENABLED") != "true":
        raise SystemExit("Native runtime must be explicitly enabled")
    namespace, url = os.environ["QH_NATIVE_GRAPH_NAMESPACE"], database_url()
    owner = str(args.owner_id) if args.verify_scope else str(uuid4())
    scope = str(args.verify_scope) if args.verify_scope else str(uuid4())
    repo = CanonicalRepository(url=url, subject_id=owner)
    if args.write_synthetic:
        # Registration must have happened through the explicit provisioning CLI.
        with repo.connect() as c:
            if c.execute("SELECT version_num FROM alembic_version").fetchone()["version_num"] not in ("0004_projection_outbox", "0005_retire_legacy_category", "0006_owner_organization"):
                raise SystemExit("Requires reviewed 0004 or 0005 schema")
            if not c.execute("SELECT 1 FROM semantic_type_versions WHERE type_id='qh.generic.item' AND version=1").fetchone():
                raise SystemExit("Run explicitly authorized generic profile provisioning first")
            c.execute("INSERT INTO users(id,display_name) VALUES (%s,'QH synthetic smoke')", (owner,))
            c.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic smoke')", (scope, owner))
        examples = [
            ("decision", "Synthetic team chooses Cedar."),
            ("hypothesis", "Synthetic Cedar may reduce waiting."),
            ("open_question", "Synthetic Cedar: which trial comes next?"),
            ("reversible_pause", "Synthetic Cedar experiment can pause and resume."),
        ]
        source = dict(id=str(uuid4()), source_id=str(uuid4()), context_space_id=scope,
                      revision_no=1, content="\n".join(text for _, text in examples),
                      origin={"locator": "synthetic://qh-semantic-smoke", "acquired_at": datetime.now(timezone.utc).isoformat()})
        rows = [dict(id=str(uuid4()), item_id=str(uuid4()), context_space_id=scope,
                     revision_no=1, type_id="qh.generic.item", type_version=1,
                     content={"text": text, "descriptors": [{"value": meaning, "certainty": "asserted"}]},
                     origin_kind="import", validation_state="proposed", provenance=[source["id"]])
                for meaning, text in examples]
        repo.save(sources=[source], revisions=rows)
        deadline = time.monotonic() + 30
        while repo.sync_status((scope,))[0]["sync_state"] != "ready":
            if time.monotonic() >= deadline:
                raise SystemExit("FAIL: backend worker did not synchronize the synthetic scope")
            time.sleep(0.1)
    policy = OwnerPolicyService(owner_for=PostgresSecurityReader(url=url).owner_for)
    with GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]), max_transaction_retry_time=5) as driver:
        service = AuthorizedNativeContextService(policy=policy, engine=IncrementalContextEngine(repo, IncrementalProjector(driver, namespace=namespace)))
        request = ContextRequest(subject_id=SubjectId(owner), query=ContextQuery(text="Cedar", context_ids=(scope,), limit=100))
        result = asyncio.run(service.retrieve(request))
        assert result.hits
        ids = [str(h.item_revision.revision_id) for h in result.hits]
        canonical = repo.read_snapshot((scope,), ids)
        assert all(r["validation_state"] == "proposed" and r["current_revision_id"] is None for r in canonical["understanding_item_revisions"])
        assert all(r["provenance"] for r in canonical["understanding_item_revisions"])
        if args.write_synthetic:
            assert set(ids) == {r["id"] for r in rows}
            for meaning, _ in examples:
                selected = asyncio.run(service.select_descriptors(subject_id=SubjectId(owner), context_ids=(scope,), values=[meaning]))
                assert len(selected.hits) == 1
        try:
            asyncio.run(service.retrieve(ContextRequest(subject_id=SubjectId(str(uuid4())), query=request.query)))
        except PermissionError:
            pass
        else:
            raise AssertionError("Foreign subject was not denied")
    print("PASS: backend worker -> authorized graph retrieval -> canonical hydration; foreign subject denied")
    print(json.dumps({"scope": scope, "owner": owner, "revision_ids": ids,
                      "source_revision_ids": sorted(s["id"] for s in canonical["source_revisions"])}))


if __name__ == "__main__":
    main()
