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
from tests.test_canonical_graph_pipeline import drain
from tests.test_migrations import (
    empty_database as empty_database,
    persisted as persisted,
)
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import (
    dedicated_server_only as dedicated_server_only,
)

from adapters.postgres.semantic_profiles import (
    generic_definitions,
    register_generic_profiles,
)

CLEANUP = "0005_retire_legacy_category"


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
    register_generic_profiles(repo)
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
        content["descriptors"] = [
            {"value": value, "certainty": "asserted"} for value in descriptors
        ]
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
        r
        for r in hydrated
        if {"value": "hypothesis", "certainty": "asserted"}
        in r["content"].get("descriptors", [])
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
    "bad",
    [
        "schema",
        "missing_evidence",
        "foreign_anchor",
        "mismatched_anchor",
        "validation",
        "temporal",
        "shape_change",
    ],
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
    elif bad == "validation":
        row["validation_state"] = "confirmed"  # No validator/validation timestamp.
    elif bad == "temporal":
        row.update(valid_from="2026-10-02T12:00:00Z", valid_to="2026-10-01T12:00:00Z")
    elif bad == "shape_change":
        row.update(item_id=item["item_id"], revision_no=2, type_id="qh.generic.entity")
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
    second_source = deepcopy(p["source"])
    second_source.update(id=str(uuid4()), source_id=str(uuid4()), context_space_id=p["sibling"])
    second = revision(p, "Second retained smoke")
    second.update(type_id="qh.decision", context_space_id=p["sibling"], provenance=[second_source["id"]])
    p["repo"].save(sources=[second_source], revisions=[second])
    drain(p["worker"])
    drain(ProjectionWorker(p["repo"], p["projector"], (p["sibling"],)))
    scopes = (p["scope"], p["sibling"])
    before = p["repo"].read_snapshot(scopes)
    markers_before = p["projector"].markers(scopes)
    assert len(query(p).hits) == 1
    with p["repo"].connect() as c:
        constraints = c.execute(
            "SELECT count(*) AS n FROM pg_constraint WHERE connamespace='public'::regnamespace"
        ).fetchone()["n"]
        triggers = c.execute(
            "SELECT count(*) AS n FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace)"
        ).fetchone()["n"]
    with p["repo"].connect() as c:
        outbox_before = c.execute(
            "SELECT to_jsonb(o) AS row FROM projection_outbox o ORDER BY id"
        ).fetchall()
        state_before = c.execute(
            "SELECT to_jsonb(s) AS row FROM context_projection_state s ORDER BY context_space_id"
        ).fetchall()
    command.upgrade(empty_database, CLEANUP)
    with p["repo"].connect() as c:
        assert (
            c.execute(
                "SELECT to_jsonb(o) AS row FROM projection_outbox o ORDER BY id"
            ).fetchall()
            == outbox_before
        )
        assert (
            c.execute(
                "SELECT to_jsonb(s) AS row FROM context_projection_state s ORDER BY context_space_id"
            ).fetchall()
            == state_before
        )
    assert p["repo"].read_snapshot(scopes) == before
    assert p["projector"].markers(scopes) == markers_before
    assert len(query(p).hits) == 1  # Existing graph usable without an epoch/rebuild.
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


def select(p, values, *, scopes=None, subject=None, **kwargs):
    return asyncio.run(
        p["service"].select_descriptors(
            subject_id=SubjectId(subject or p["repo"].subject_id),
            context_ids=scopes or (p["scope"],),
            values=values,
            **kwargs,
        )
    )


def test_exact_descriptor_selection_without_text_with_uncertainty_and_pagination(
    generic, monkeypatch
):
    from adapters.context.native import NativeContextEngine, NativeContextError

    p = generic
    meanings = ("decision", "hypothesis", "open_question", "reversible_pause")
    rows = [
        revision(p, "Identical neutral content", descriptors=[meaning])
        for meaning in meanings
    ]
    multiple = revision(
        p, "Identical neutral content", descriptors=["decision", "intention"]
    )
    unknown = revision(p, "Identical neutral content")
    tentative = revision(p, "Identical neutral content")
    tentative["content"]["descriptors"] = [
        {"value": "decision", "certainty": "tentative"}
    ]
    p["repo"].save(
        sources=[p["source"]], revisions=[*rows, multiple, unknown, tentative]
    )
    with pytest.raises(NativeContextError, match="pending"):
        select(p, ["not_present"])
    drain(p["worker"])

    # A semantic selection must not call text search or load the whole scope.
    async def no_text(*args, **kwargs):
        raise AssertionError("Unexpected text search")

    monkeypatch.setattr(NativeContextEngine, "search", no_text)
    original = p["repo"].read_snapshot

    def bounded(scopes, refs=None):
        assert refs is not None
        return original(scopes, refs)

    monkeypatch.setattr(p["repo"], "read_snapshot", bounded)
    for meaning, row in zip(meanings, rows):
        ids = {str(h.item_revision.revision_id) for h in select(p, [meaning]).hits}
        assert row["id"] in ids
    assert len(select(p, ["decision"]).hits) == 2
    assert len(select(p, ["decision"], include_tentative=True).hits) == 3
    assert not select(p, ["Decision"]).hits  # Exact spelling; no hidden aliases.
    assert not select(p, ["decision"], scopes=(p["sibling"],)).hits
    expected = {r["id"] for r in [*rows, multiple]}
    collected, cursor = [], None
    while True:
        page = select(p, meanings, limit=1, after_revision_id=cursor).hits
        if not page:
            break
        cursor = str(page[-1].item_revision.revision_id)
        collected.append(cursor)
    assert set(collected) == expected and len(collected) == len(expected)
    with pytest.raises(PermissionError):
        select(p, ["decision"], scopes=(p["scope"], p["foreign"]))
    # Canonical changes during even an otherwise empty selection fail closed.
    lookup = p["repo"].descriptor_candidates

    def advance(*args, **kwargs):
        result = lookup(*args, **kwargs)
        p["repo"].save(revisions=[revision(p, "Concurrent publication")])
        return result

    monkeypatch.setattr(p["repo"], "descriptor_candidates", advance)
    with pytest.raises(NativeContextError, match="advanced|pending"):
        select(p, ["not_present"])


@pytest.mark.parametrize(
    "descriptors",
    [
        ["decision"],
        [{"value": "", "certainty": "asserted"}],
        [{"value": "decision"}],
        [{"value": "decision", "certainty": "confirmed"}],
        [{"value": "decision", "certainty": "asserted", "owner": "invented"}],
    ],
)
def test_descriptor_schema_rejects_invalid_assignments(generic, descriptors):
    p = generic
    row = revision(p, "Invalid descriptors")
    row["content"]["descriptors"] = descriptors
    with pytest.raises(psycopg.errors.CheckViolation):
        p["repo"].save(sources=[p["source"]], revisions=[row])
    assert p["repo"].sync_status((p["scope"],))[0]["desired_version"] == 0


def test_controlled_profile_cli_is_idempotent_and_conflicts_fail(generic):
    import subprocess
    import sys
    from pathlib import Path

    p = generic
    script = str(
        Path(__file__).resolve().parents[3] / "scripts/provision_qh_semantics.py"
    )
    assert subprocess.run([sys.executable, script], capture_output=True).returncode != 0
    result = subprocess.run(
        [sys.executable, script, "--register-generic-profiles"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "PASS:" in result.stdout
    bad = generic_definitions()
    bad[0]["property_schema"]["required"].append("different")
    with pytest.raises(ValueError, match="registered type replay"):
        p["repo"].register_types(bad)
    register_generic_profiles(p["repo"])
    assert p["repo"].sync_status((p["scope"],))[0]["desired_version"] == 0


def test_oidc_signed_identity_and_authorized_selection_on_reviewed_schema(generic):
    import httpx
    import jwt
    from adapters.oidc import OIDCAuthenticator, InvalidCredentials
    from adapters.postgres.demo_identities import require_identity_schema
    from tests.oidc_database import application_snapshot, connect
    from tests.test_oidc_security import KEY, SETTINGS, token

    p = generic
    with connect() as c:
        require_identity_schema(c)
        assert application_snapshot(c)[1][0][0] in ("0004_projection_outbox", CLEANUP)
        c.execute(
            "INSERT INTO user_identities(issuer,subject,user_id) VALUES (%s,%s,%s)",
            (SETTINGS.issuer, "external-alice", p["repo"].subject_id),
        )
    key = jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True)
    auth = OIDCAuthenticator(
        settings=SETTINGS,
        resolve_identity=PostgresSecurityReader(url=p["repo"].url).resolve_identity,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"keys": [dict(key, kid="current", use="sig", alg="RS256")]}
            )
        ),
    )
    subject = asyncio.run(auth.authenticate(token()))
    assert str(subject) == p["repo"].subject_id
    row = revision(p, "Authenticated meaning", descriptors=["decision"])
    p["repo"].save(sources=[p["source"]], revisions=[row])
    drain(p["worker"])
    assert len(select(p, ["decision"], subject=subject).hits) == 1
    with pytest.raises(InvalidCredentials):
        asyncio.run(auth.authenticate(token(sub="unmapped")))


def test_empty_install_0005_then_controlled_profiles(empty_database):
    import subprocess
    import sys
    from pathlib import Path

    command.upgrade(empty_database, CLEANUP)
    repo = CanonicalRepository(url=database_url(), subject_id="")
    with repo.connect() as c:
        assert (
            c.execute("SELECT version_num FROM alembic_version").fetchone()[
                "version_num"
            ]
            == CLEANUP
        )
        assert (
            c.execute("SELECT count(*) AS n FROM semantic_type_versions").fetchone()[
                "n"
            ]
            == 11
        )
        assert (
            c.execute(
                "SELECT count(*) AS n FROM understanding_item_revisions"
            ).fetchone()["n"]
            == 0
        )
    script = str(
        Path(__file__).resolve().parents[3] / "scripts/provision_qh_semantics.py"
    )
    result = subprocess.run(
        [sys.executable, script, "--register-generic-profiles"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    with repo.connect() as c:
        registered = c.execute(
            "SELECT type_id, structural_kind FROM semantic_type_versions WHERE type_id LIKE 'qh.generic.%' ORDER BY type_id"
        ).fetchall()
        assert {r["structural_kind"] for r in registered} == {
            "item",
            "entity",
            "relation",
        }
        assert len(registered) == 3
        assert (
            c.execute("SELECT count(*) AS n FROM projection_outbox").fetchone()["n"]
            == 0
        )


def test_descriptor_selection_denies_before_access_and_rejects_missing_graph(
    generic, monkeypatch
):
    from adapters.context.native import NativeContextError

    p = generic
    row = revision(p, "Meaning", descriptors=["decision"])
    p["repo"].save(sources=[p["source"]], revisions=[row])
    drain(p["worker"])

    def no_sql(*args, **kwargs):
        raise AssertionError("Unauthorized canonical access")

    with monkeypatch.context() as patch:
        patch.setattr(p["repo"], "descriptor_candidates", no_sql)
        with pytest.raises(PermissionError):
            select(p, ["decision"], subject=str(uuid4()))
    with p["projector"].driver.session() as session:
        session.run(
            "MATCH (r:QH30Revision {revision_id:$id}) WHERE r.slice_id STARTS WITH $prefix DETACH DELETE r",
            id=row["id"],
            prefix=p["projector"].key(p["scope"]),
        ).consume()
    with pytest.raises(NativeContextError, match="missing from graph"):
        select(p, ["decision"])



def test_publication_still_requires_read_committed(generic, monkeypatch):
    from contextlib import contextmanager
    p = generic
    original = p["repo"].connect
    @contextmanager
    def repeatable(**kwargs):
        with original(**kwargs) as c:
            c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            yield c
    with monkeypatch.context() as patch:
        patch.setattr(p["repo"], "connect", repeatable)
        with pytest.raises(psycopg.errors.CheckViolation, match="requires READ COMMITTED"):
            p["repo"].save(sources=[p["source"]], revisions=[revision(p, "Wrong isolation")])
    assert p["repo"].sync_status((p["scope"],))[0]["desired_version"] == 0
