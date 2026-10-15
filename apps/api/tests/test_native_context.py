"""Native fixture slice. Real Neo4j tests require a dedicated explicit test URI."""

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from adapters.context.native import (
    AuthorizedNativeContextService,
    NativeContextEngine,
    NativeContextError,
    checked_rows,
)
from app.core.models import ContextId, ContextQuery, ContextRequest, SubjectId
from app.core.ports import ContextEngine
from app.policy.owner import OwnerPolicyService

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/qh30_canonical_snapshot.json").read_text()
)
A = ContextId(FIXTURE["source_revisions"][0]["context_space_id"])
B = ContextId(FIXTURE["source_revisions"][1]["context_space_id"])


# Specialized extension examples; SQL tests validate the real schema profile.
FIXTURE_TYPES = {r["type_id"]: r["structural_kind"] for r in FIXTURE["understanding_item_revisions"]}


def validate_fixture(snapshot):
    """Offline fixture checks belong to tests, never the production projector."""
    from datetime import datetime

    for row in snapshot["understanding_item_revisions"]:
        if row["type_version"] != 1 or FIXTURE_TYPES.get(row["type_id"]) != row["structural_kind"]:
            raise NativeContextError("Invalid fixture semantic binding")
        try:
            for field in ("fact_from", "fact_to", "valid_from", "valid_to"):
                if row[field] is not None and datetime.fromisoformat(row[field]).tzinfo is None:
                    raise ValueError("Timezone required")
        except ValueError as exc:
            raise NativeContextError("Invalid fixture semantic time") from exc
    return checked_rows(snapshot)


def loader(snapshot, calls):
    def load(scopes, ids):
        calls.append((scopes, ids))
        revisions = [
            deepcopy(r)
            for r in snapshot["understanding_item_revisions"]
            if r["context_space_id"] in scopes and r["id"] in ids
        ]
        refs = {ref for r in revisions for ref in r["provenance"]}
        return {
            "understanding_item_revisions": revisions,
            "source_revisions": [
                deepcopy(s)
                for s in snapshot["source_revisions"]
                if s["context_space_id"] in scopes and s["id"] in refs
            ],
        }

    return load


def test_policy_denies_before_engine_or_canonical_read():
    async def owner(context):
        return (
            SubjectId("alice")
            if context == A
            else SubjectId("bob")
            if context == B
            else None
        )

    engine = AsyncMock()
    service = AuthorizedNativeContextService(
        policy=OwnerPolicyService(owner_for=owner), engine=engine
    )
    for scopes in ((B,), (A, B), (ContextId("unknown"),)):
        with pytest.raises(PermissionError):
            asyncio.run(
                service.retrieve(
                    ContextRequest(
                        subject_id=SubjectId("alice"),
                        query=ContextQuery(text="Cedar", context_ids=scopes),
                    )
                )
            )
    engine.search.assert_not_awaited()


@pytest.mark.parametrize("bad", ["missing", "foreign", "duplicate", "state"])
def test_canonical_fixture_validation_before_projection(bad):
    snapshot = deepcopy(FIXTURE)
    row = snapshot["understanding_item_revisions"][0]
    if bad == "missing":
        row["provenance"] = ["missing"]
    if bad == "foreign":
        row["provenance"] = [snapshot["source_revisions"][1]["id"]]
    if bad == "duplicate":
        snapshot["understanding_item_revisions"].append(deepcopy(row))
    if bad == "state":
        row["validation_state"] = "silently_approved"
    with pytest.raises(NativeContextError):
        validate_fixture(snapshot)


@pytest.fixture
def real_engine():
    uri = os.environ.get("QH30_TEST_NEO4J_URI")
    if not uri:
        pytest.skip(
            "Dedicated QH30_TEST_NEO4J_URI required; no production graph fallback"
        )
    assert uri == "bolt://qh30-native-neo4j-test:7687", "Dedicated graph required"
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        uri,
        auth=("neo4j", os.environ["QH30_TEST_NEO4J_PASSWORD"]),
        max_transaction_retry_time=0,
    )
    driver.verify_connectivity()
    snapshot = deepcopy(FIXTURE)
    calls = []
    engine = NativeContextEngine(
        driver,
        slice_id="qh30-test-" + uuid4().hex,
        read_snapshot=loader(snapshot, calls),
    )
    engine.initialize()
    try:
        yield engine, snapshot, calls
    finally:
        driver.close()


def search(engine, space=A, text="Cedar"):
    return asyncio.run(engine.search(ContextQuery(text=text, context_ids=(space,))))


def test_real_projection_replay_rebuild_and_hydration(real_engine):
    engine, snapshot, calls = real_engine
    assert isinstance(engine, ContextEngine)
    engine.replace(snapshot, generation="one")
    first = search(engine)
    assert len(first.hits) == 3
    assert len(calls) == 1 and set(calls[0][1]) == {
        r["id"]
        for r in snapshot["understanding_item_revisions"]
        if r["context_space_id"] == A and "Cedar" in r["content"]["text"]
    }
    assert {h.item_revision.revision_id for h in first.hits} == set(calls[0][1])
    assert all(
        h.context_id == A
        and h.provenance[0].source_id == snapshot["source_revisions"][0]["source_id"]
        for h in first.hits
    )
    assert not search(engine, B).hits
    assert len(search(engine, B, "Birch").hits) == 3
    engine.replace(snapshot, generation="one")  # Exact replay has no extra nodes/edges.
    assert search(engine) == first
    with engine.driver.session() as session:
        counts = session.run(
            'MATCH (r:QH30Revision {slice_id:$id,generation:"one"}) '
            "MATCH (r)-[e:EVIDENCED_BY]->() RETURN count(DISTINCT r) AS nodes,count(e) AS edges",
            id=engine.slice_id,
        ).single()
        assert (
            counts["nodes"]
            == counts["edges"]
            == len(snapshot["understanding_item_revisions"])
        )
    engine.replace(
        snapshot, generation="two"
    )  # Rebuild from canonical fixture, no API.
    assert search(engine) == first
    fresh = NativeContextEngine(
        engine.driver,
        slice_id=engine.slice_id,
        read_snapshot=loader(snapshot, []),
    )
    assert search(fresh) == first
    with pytest.raises(NativeContextError):
        engine.replace(snapshot, generation="one")
    assert search(engine) == first


def test_real_partial_failure_does_not_switch_or_modify_generation(real_engine):
    engine, snapshot, calls = real_engine
    engine.replace(snapshot, generation="one")
    original = search(engine)
    changed = deepcopy(snapshot)
    changed["understanding_item_revisions"][0]["content"]["text"] = (
        "changed immutable revision"
    )
    with pytest.raises(NativeContextError):
        engine.replace(changed, generation="one")
    assert search(engine) == original
    snapshot["understanding_item_revisions"][0]["content"]["text"] = "canonical changed"
    with pytest.raises(NativeContextError):
        search(engine)


@pytest.mark.parametrize("tampering", ["text", "evidence_scope", "missing_evidence"])
def test_real_graph_tampering_or_foreign_provenance_fails_closed(
    real_engine, tampering
):
    engine, snapshot, calls = real_engine
    engine.replace(snapshot, generation="one")
    with engine.driver.session() as session:
        if tampering == "text":
            session.run(
                'MATCH (r:QH30Revision {slice_id:$id, context_id:$scope}) SET r.text="Cedar tampered"',
                id=engine.slice_id,
                scope=str(A),
            ).consume()
        elif tampering == "missing_evidence":
            session.run(
                "MATCH (r:QH30Revision {slice_id:$id, context_id:$scope})-[e:EVIDENCED_BY]->() DELETE e",
                id=engine.slice_id,
                scope=str(A),
            ).consume()
        else:
            session.run(
                "MATCH (r:QH30Revision {slice_id:$id, context_id:$scope})-[:EVIDENCED_BY]->(e) "
                "SET e.context_id=$foreign",
                id=engine.slice_id,
                scope=str(A),
                foreign=str(B),
            ).consume()
    with pytest.raises(NativeContextError):
        search(engine)


def test_real_generation_not_ready_is_not_empty_success(real_engine):
    engine, _, _ = real_engine
    with pytest.raises(NativeContextError, match="not ready"):
        search(engine)


def test_real_transaction_failure_rolls_back_new_rows_and_manifest(real_engine):
    engine, snapshot, _ = real_engine
    engine.replace(snapshot, generation="one")
    original = search(engine)
    key = engine.slice_id + ":bad:" + snapshot["understanding_item_revisions"][0]["id"]
    with engine.driver.session() as session:
        session.run(
            "CREATE (:QH30Revision {key:$key, fingerprint:'conflict', slice_id:$id, generation:'bad'})",
            key=key,
            id=engine.slice_id,
        ).consume()
    with pytest.raises(NativeContextError):
        engine.replace(snapshot, generation="bad")
    assert search(engine) == original
    with engine.driver.session() as session:
        assert (
            session.run(
                "MATCH (r:QH30Revision {slice_id:$id,generation:'bad'}) RETURN count(r) AS n",
                id=engine.slice_id,
            ).single()["n"]
            == 1
        )
        assert (
            session.run(
                "MATCH (g:QH30Generation {key:$key}) RETURN count(g) AS n",
                key=engine.slice_id + ":bad",
            ).single()["n"]
            == 0
        )


@pytest.mark.parametrize("bad", ["unknown_type", "unknown_version", "properties"])
def test_versioned_schema_rejection(bad):
    snapshot = deepcopy(FIXTURE)
    row = snapshot["understanding_item_revisions"][0]
    if bad == "unknown_type":
        row["type_id"] = "unknown.domain_type"
    elif bad == "unknown_version":
        row["type_version"] = 999
    else:
        row["fact_from"] = "invalid-time"
    with pytest.raises(NativeContextError, match="semantic"):
        validate_fixture(snapshot)


def test_three_domain_fixtures_share_universal_contract():
    rows = {r["revision_id"]: r for r in validate_fixture(FIXTURE)}
    assert {case["domain"] for case in FIXTURE["cases"]} == {
        "professional",
        "health",
        "family",
    }
    assert {case["context_space_id"] for case in FIXTURE["cases"]} == {A}
    for case in FIXTURE["cases"]:
        revisions = [rows[key] for key in case["revision_ids"]]
        assert all(
            r["validation_state"] == "proposed" and r["evidence"] for r in revisions
        )
        assertion = revisions[2]
        event = assertion["temporal"]["fact_from"]
        assert (event is not None) == (case["domain"] == "professional")
        source = next(
            s
            for s in FIXTURE["source_revisions"]
            if s["id"] == case["source_revision_id"]
        )
        assert assertion["text"] in source["content"]
        assert revisions[3]["text"] in source["content"]
        assert source["created_at"] != event
        assert revisions[3]["structural_kind"] == "relation"
    health = next(c for c in FIXTURE["cases"] if c["domain"] == "health")
    assert (
        rows[health["revision_ids"][2]]["semantic_type"] == "qh.observation"
    )


def test_real_universal_relationship_projection_and_endpoint_integrity(real_engine):
    engine, snapshot, _ = real_engine
    engine.replace(snapshot, generation="domains")
    for case in snapshot["cases"]:
        hits = search(engine, A, "Synthetic " + case["domain"])
        assert hits.hits and all(h.context_id == A and h.provenance for h in hits.hits)
        assert not search(engine, B, "Synthetic " + case["domain"]).hits
    with engine.driver.session() as session:
        record = session.run(
            "MATCH (a)<-[:SUBJECT]-(r:QH30Revision {slice_id:$id})-[:OBJECT]->(b) "
            "RETURN count(r) AS n, collect(r.predicate) AS predicates, collect(a.category+'->'+b.category) AS shapes",
            id=engine.slice_id,
        ).single()
        assert record["n"] == 3 and set(record["predicates"]) == {"associated_with"}
        assert set(record["shapes"]) == {
            "item->entity",
            "item->item",
            "relation->item",
        }
    broken = deepcopy(snapshot)
    relation = next(
        r
        for r in broken["understanding_item_revisions"]
        if r["structural_kind"] == "relation"
    )
    relation["relation"]["source_revision_id"] = "unavailable"
    with pytest.raises(NativeContextError, match="endpoint"):
        engine.replace(broken, generation="invalid")
    foreign = deepcopy(snapshot)
    endpoint_id = relation["relation"]["target_revision_id"]
    endpoint = next(
        r for r in foreign["understanding_item_revisions"] if r["id"] == endpoint_id
    )
    endpoint["context_space_id"] = B
    endpoint["provenance"] = [snapshot["source_revisions"][1]["id"]]
    with pytest.raises(NativeContextError, match="endpoint"):
        engine.replace(foreign, generation="foreign")


def test_real_stable_id_must_match_anchor(real_engine):
    engine, snapshot, _ = real_engine
    relation = next(
        r
        for r in snapshot["understanding_item_revisions"]
        if r["structural_kind"] == "relation"
    )
    relation["relation"]["source_item_id"] = "wrong-logical-id"
    with pytest.raises(NativeContextError, match="stable item"):
        engine.replace(snapshot, generation="mismatched")
