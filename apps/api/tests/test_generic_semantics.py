"""Three generic types on deployed 0004 and prepared 0005; dedicated SQL/Neo4j only."""

import asyncio
from copy import deepcopy
from uuid import uuid4

from alembic import command
import psycopg
import pytest

from adapters.context.incremental import (
    IncrementalContextEngine,
    IncrementalProjector,
    ProjectionWorker,
)
from adapters.context.native import AuthorizedNativeContextService
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from app.core.models import ContextQuery, ContextRequest, SubjectId
from app.policy.owner import OwnerPolicyService
from tests.test_migrations import (
    empty_database as empty_database,
    persisted as persisted,
)
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)

CLEANUP = "0005_retire_legacy_category"
CONTENT = {
    "type": "object",
    "required": ["text"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
        "descriptors": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "properties": {"type": "object"},
    },
    "additionalProperties": True,
}
# Candidate provisioning for this experiment only; no automatic runtime seeds.
GENERIC_TYPES = [
    dict(
        type_id="qh.generic." + shape,
        version=1,
        structural_kind=shape,
        property_schema=CONTENT,
        relation_rules={"mode": "any_registered"} if shape == "relation" else None,
    )
    for shape in ("item", "entity", "relation")
]


def drain(worker):
    for _ in range(100):
        event = worker.claim()
        if event is None:
            return
        assert worker.process(event), repr(worker.last_error)
    raise AssertionError("Queue did not drain")


@pytest.fixture(params=["0004_projection_outbox", CLEANUP])
def generic(request, empty_database, real_engine):
    command.upgrade(empty_database, request.param)
    owner, other, scope, sibling, foreign = (str(uuid4()) for _ in range(5))
    repo = CanonicalRepository(url=database_url(), subject_id=owner)
    with repo.connect() as c:
        for who in (owner, other):
            c.execute(
                "INSERT INTO users(id,display_name) VALUES (%s,'Synthetic')", (who,)
            )
        for space, who in ((scope, owner), (sibling, owner), (foreign, other)):
            c.execute(
                "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic')",
                (space, who),
            )
    repo.register_types(GENERIC_TYPES)
    source = dict(
        id=str(uuid4()),
        source_id=str(uuid4()),
        context_space_id=scope,
        revision_no=1,
        content="Choose a pilot. It may help. What next? Report tiredness. Prefer quiet dinners. Invent a reversible pause.",
        origin={
            "locator": "synthetic://generic-conversation",
            "acquired_at": "2026-10-15T08:00:00Z",
        },
    )
    projector = IncrementalProjector(
        real_engine[0].driver, namespace="qh-generic-" + repo.url.database
    )
    projector.initialize()
    worker = ProjectionWorker(repo, projector, (scope,))
    service = AuthorizedNativeContextService(
        policy=OwnerPolicyService(
            owner_for=PostgresSecurityReader(url=repo.url).owner_for
        ),
        engine=IncrementalContextEngine(repo, projector),
    )
    return dict(
        repo=repo,
        scope=scope,
        sibling=sibling,
        foreign=foreign,
        source=source,
        projector=projector,
        worker=worker,
        service=service,
    )


def revision(p, text, *, shape="item", descriptors=None):
    content = {"text": "Generic " + text}
    if descriptors is not None:
        content["descriptors"] = descriptors
    return dict(
        id=str(uuid4()),
        item_id=str(uuid4()),
        context_space_id=p["scope"],
        revision_no=1,
        type_id="qh.generic." + shape,
        type_version=1,
        content=content,
        origin_kind="ai",
        validation_state="proposed",
        provenance=[p["source"]["id"]],
    )


def query(p, text="Generic", scopes=None):
    return asyncio.run(
        p["service"].retrieve(
            ContextRequest(
                subject_id=SubjectId(p["repo"].subject_id),
                query=ContextQuery(
                    text=text, context_ids=scopes or (p["scope"],), limit=100
                ),
            )
        )
    )


def test_many_meanings_and_selective_candidates_without_type_registration(generic):
    p = generic
    meanings = [
        "decision",
        "hypothesis",
        "open_question",
        "observation",
        "preference",
        "reversible_pause",
    ]
    texts = [
        "Choose a pilot",
        "It may help",
        "What next?",
        "Report tiredness",
        "Prefer quiet dinners",
        "Invent a reversible pause",
    ]
    rows = [
        revision(p, text, descriptors=[meaning])
        for text, meaning in zip(texts, meanings)
    ]
    rows.append(revision(p, "Meaning without a descriptor"))
    p["repo"].save(sources=[p["source"]], revisions=rows)
    drain(p["worker"])
    hits = query(p).hits
    assert {str(h.item_revision.revision_id) for h in hits} == {r["id"] for r in rows}
    assert all(str(h.provenance[0].revision_id) == p["source"]["id"] for h in hits)
    hydrated = p["repo"].read_snapshot(
        (p["scope"],), [h.item_revision.revision_id for h in hits]
    )["understanding_item_revisions"]
    # Exact data predicate over this bounded candidate set, not universal semantic recall.
    selected = [
        r for r in hydrated if "hypothesis" in r["content"].get("descriptors", [])
    ]
    assert [r["id"] for r in selected] == [rows[1]["id"]]
    assert {r["type_id"] for r in hydrated} == {"qh.generic.item"}
    assert all(
        r["validation_state"] == "proposed"
        and r["current_revision_id"] is None
        and r["fact_from"] is None
        and "category" not in r
        for r in hydrated
    )
    with p["repo"].connect() as c:
        assert (
            c.execute("SELECT count(*) AS n FROM semantic_type_versions").fetchone()[
                "n"
            ]
            == 14
        )
    assert len(query(p, "reversible pause").hits) == 1
    assert not query(p, "pilot", (p["sibling"],)).hits
    with pytest.raises(PermissionError):
        query(p, scopes=(p["scope"], p["foreign"]))


def test_relations_keep_exact_anchors_when_descriptions_evolve(generic):
    p = generic
    item, entity = (
        revision(p, "Pilot decision"),
        revision(p, "Synthetic team", shape="entity"),
    )
    rel = revision(p, "Pilot selected by team", shape="relation")
    rel["relation"] = dict(
        source_item_id=item["item_id"],
        source_revision_id=item["id"],
        target_item_id=entity["item_id"],
        target_revision_id=entity["id"],
        predicate="selected_by",
    )
    rel.update(fact_from="2026-10-01T12:00:00Z", fact_to="2026-10-01T12:00:00Z")
    p["repo"].save(sources=[p["source"]], revisions=[rel, entity, item])
    drain(p["worker"])
    new = deepcopy(entity)
    new.update(id=str(uuid4()), revision_no=2, based_on_revision_id=entity["id"])
    new["content"]["text"] = "Team description evolved"
    p["repo"].save(revisions=[new])
    drain(p["worker"])
    anchored = p["repo"].read_snapshot((p["scope"],), [rel["id"]])[
        "understanding_item_revisions"
    ][0]
    assert anchored["relation"] == rel["relation"]
    assert anchored["fact_from"] == "2026-10-01T12:00:00+00:00"
    assert len(query(p, "selected by").hits) == 1
    # New repository/worker instances replay from durable state; explicit rebuild
    # exercises the retained full-generation publisher with generic types.
    fresh = CanonicalRepository(url=p["repo"].url, subject_id=p["repo"].subject_id)
    ProjectionWorker(fresh, p["projector"], (p["scope"],)).rebuild(p["scope"])
    assert len(query(p, "description evolved").hits) == 1
    with fresh.connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        c.execute(
            "UPDATE relation_revision_details SET predicate='rewritten' WHERE item_revision_id=%s",
            (rel["id"],),
        )


@pytest.mark.parametrize(
    "bad", ["schema", "missing_evidence", "foreign_anchor", "mismatched_anchor"]
)
def test_generic_integrity_remains_relational_and_atomic(generic, bad):
    p = generic
    item = revision(p, "Synthetic target")
    p["repo"].save(sources=[p["source"]], revisions=[item])
    row = revision(p, "Invalid proposal")
    if bad == "schema":
        row["content"]["text"] = 42
    elif bad == "missing_evidence":
        row["provenance"] = [str(uuid4())]
    else:
        row["type_id"] = "qh.generic.relation"
        row["relation"] = dict(
            source_item_id=item["item_id"],
            source_revision_id=item["id"],
            target_item_id=str(uuid4()),
            target_revision_id=item["id"],
            predicate="refers_to",
        )
        if bad == "foreign_anchor":
            # Valid evidence in the relation scope: only its foreign endpoint
            # should fail, even though both spaces belong to the same owner.
            source = deepcopy(p["source"])
            source.update(
                id=str(uuid4()), source_id=str(uuid4()), context_space_id=p["sibling"]
            )
            target = revision(p, "Foreign target")
            target.update(context_space_id=p["sibling"], provenance=[source["id"]])
            p["repo"].save(sources=[source], revisions=[target])
            row["relation"].update(
                target_item_id=target["item_id"], target_revision_id=target["id"]
            )
    before = p["repo"].sync_status((p["scope"],))[0]["desired_version"]
    with pytest.raises(psycopg.IntegrityError):
        p["repo"].save(revisions=[row])
    assert p["repo"].sync_status((p["scope"],))[0]["desired_version"] == before


def test_cleanup_preserves_historical_bindings_and_replay(generic, empty_database):
    p = generic
    old = revision(p, "Historical smoke interpretation")
    old["type_id"] = "qh.decision"
    p["repo"].save(sources=[p["source"]], revisions=[old])
    before = p["repo"].read_snapshot((p["scope"],))
    with p["repo"].connect() as c:
        constraints = c.execute(
            "SELECT count(*) AS n FROM pg_constraint WHERE connamespace='public'::regnamespace"
        ).fetchone()["n"]
        triggers = c.execute(
            "SELECT count(*) AS n FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace)"
        ).fetchone()["n"]
    command.upgrade(empty_database, CLEANUP)
    assert p["repo"].read_snapshot((p["scope"],)) == before
    p["repo"].save(revisions=[old])
    with p["repo"].connect() as c:
        assert not c.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name='understanding_item_revisions' AND column_name='category'"
        ).fetchone()
        assert (
            c.execute(
                "SELECT count(*) AS n FROM pg_constraint WHERE connamespace='public'::regnamespace"
            ).fetchone()["n"]
            == constraints
        )
        assert (
            c.execute(
                "SELECT count(*) AS n FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace)"
            ).fetchone()["n"]
            == triggers
        )
    assert p["repo"].sync_status((p["scope"],))[0]["desired_version"] == 1
    p["repo"].save(revisions=[revision(p, "New generic interpretation")])
    drain(p["worker"])
    assert len(query(p).hits) == 2
    with pytest.raises(RuntimeError, match="Forward-only"):
        command.downgrade(empty_database, "0004_projection_outbox")


def test_cleanup_refuses_nonnull_history_without_partial_ddl(persisted, empty_database):
    command.upgrade(empty_database, "0004_projection_outbox")
    repo = CanonicalRepository(url=database_url(), subject_id=persisted["owner"])
    before = repo.read_snapshot((str(persisted["space"]),))
    with pytest.raises(
        Exception,
        match="Historical category data requires explicit preservation review",
    ):
        command.upgrade(empty_database, CLEANUP)
    with repo.connect() as c:
        assert (
            c.execute("SELECT version_num FROM alembic_version").fetchone()[
                "version_num"
            ]
            == "0004_projection_outbox"
        )
        assert (
            c.execute("SELECT category FROM understanding_item_revisions").fetchone()[
                "category"
            ]
            == "hypothesis"
        )
        assert (
            "NEW.category"
            in c.execute(
                "SELECT prosrc FROM pg_proc WHERE proname='qh30_publish'"
            ).fetchone()["prosrc"]
        )
    assert repo.read_snapshot((str(persisted["space"]),)) == before
