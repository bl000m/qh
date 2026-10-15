"""QH-30 real SQL tests. Refuse any server except the disposable test container."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
import time
from uuid import uuid4

from alembic import command
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pytest

from tests.test_migrations import (
    connect,
    empty_database as empty_database,
    insert_revision,
    table_names,
)

HEAD = "0003_native_semantics"
CATEGORIES = (
    "objective",
    "current_state",
    "decision",
    "hypothesis",
    "open_question",
    "constraint",
    "preference",
    "concept",
    "entity",
    "relationship",
    "uncertainty",
)
SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string", "minLength": 1}},
    "required": ["text"],
    "additionalProperties": False,
}


@pytest.fixture(autouse=True)
def dedicated_server_only():
    if os.environ.get("QH30_SQL_TEST") != "1":
        pytest.skip("Explicit QH30_SQL_TEST=1 dedicated server required; no production fallback")
    assert os.environ.get("POSTGRES_HOST") == "qh30-sql-test"


def force(c):
    c.execute("SET CONSTRAINTS ALL IMMEDIATE")
    c.execute("SET CONSTRAINTS ALL DEFERRED")


def register(
    c, name="test.observation", version=1, shape="item", schema=None, rules=None
):
    c.execute(
        "INSERT INTO semantic_type_versions (type_id,version,structural_kind,property_schema,relation_rules) VALUES (%s,%s,%s,%s,%s)",
        (
            name,
            version,
            shape,
            Jsonb(SCHEMA if schema is None else schema),
            None if rules is None else Jsonb(rules),
        ),
    )


def publish(
    c,
    d,
    *,
    type_id="qh.decision",
    version=1,
    item=None,
    revision=None,
    number=1,
    space=None,
    content=None,
    relation=None,
    times=None,
    state="proposed",
):
    item, revision, space = item or uuid4(), revision or uuid4(), space or d["space"]
    c.execute(
        "INSERT INTO understanding_items (id,context_space_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
        (item, space),
    )
    times = times or (None, None, None, None)
    c.execute(
        "INSERT INTO item_revision_types VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (revision, space, type_id, version, *times),
    )
    if relation:
        c.execute(
            "INSERT INTO relation_revision_details VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                revision,
                space,
                relation[0][0],
                relation[0][1],
                relation[1][0],
                relation[1][1],
                relation[2],
            ),
        )
    c.execute(
        "INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
        (revision, d["source_revision"], space),
    )
    insert_revision(
        c,
        d,
        revision_id=revision,
        item_id=item,
        space_id=space,
        number=number,
        category=None,
        content={"text": "Synthetic assertion"} if content is None else content,
        state=state,
    )
    return item, revision


@pytest.fixture
def legacy(empty_database):
    command.upgrade(empty_database, "0002_oidc_identities")
    d = {
        key: uuid4()
        for key in ("owner", "space", "other_space", "source", "source_revision")
    }
    d["config"] = empty_database
    d["items"] = {cat: (uuid4(), uuid4()) for cat in CATEGORIES}
    with connect() as c:
        c.execute(
            "INSERT INTO users(id,display_name) VALUES (%s,'Synthetic owner')",
            (d["owner"],),
        )
        for space in (d["space"], d["other_space"]):
            c.execute(
                "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic space')",
                (space, d["owner"]),
            )
        c.execute(
            "INSERT INTO sources(id,context_space_id,name) VALUES (%s,%s,'Synthetic source')",
            (d["source"], d["space"]),
        )
        c.execute(
            "INSERT INTO source_revisions(id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,1,'Synthetic source evidence','{}')",
            (d["source_revision"], d["source"], d["space"]),
        )
        for cat, (item, rev) in d["items"].items():
            c.execute(
                "INSERT INTO understanding_items(id,context_space_id) VALUES (%s,%s)",
                (item, d["space"]),
            )
            content = {"text": "Synthetic " + cat}
            if cat == "relationship":
                source, target = d["items"]["decision"], d["items"]["constraint"]
                content["relation"] = dict(
                    source_item_id=str(source[0]),
                    source_revision_id=str(source[1]),
                    target_item_id=str(target[0]),
                    target_revision_id=str(target[1]),
                    predicate="depends_on",
                )
            c.execute(
                "INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                (rev, d["source_revision"], d["space"]),
            )
            insert_revision(
                c,
                d,
                revision_id=rev,
                item_id=item,
                category=cat,
                content=content,
                state="confirmed" if cat == "decision" else "proposed",
            )
        c.execute(
            "UPDATE understanding_items SET current_revision_id=%s WHERE id=%s",
            (d["items"]["decision"][1], d["items"]["decision"][0]),
        )
    return d


@pytest.fixture
def migrated(legacy):
    command.upgrade(legacy["config"], HEAD)
    return legacy


def snapshot(c):
    return {
        name: c.execute(
            sql.SQL(
                "SELECT to_jsonb(t)::text FROM {} t ORDER BY to_jsonb(t)::text"
            ).format(sql.Identifier(name))
        ).fetchall()
        for name in (
            "understanding_item_revisions",
            "understanding_items",
            "source_revisions",
            "item_revision_provenance",
            "user_identities",
        )
    }


def test_safe_backfill_all_eleven_categories_and_reapply(legacy):
    with connect() as c:
        before, tables = snapshot(c), table_names(c)
    command.upgrade(legacy["config"], HEAD)
    command.upgrade(legacy["config"], HEAD)
    with connect() as c:
        assert snapshot(c) == before
        assert table_names(c) - tables == {
            "semantic_type_versions",
            "item_revision_types",
            "relation_revision_details",
        }
        assert c.execute("SELECT count(*) FROM item_revision_types").fetchone() == (11,)
        assert {r[0] for r in c.execute("SELECT type_id FROM item_revision_types")} == {
            "qh." + cat for cat in CATEGORIES
        }
        assert c.execute(
            "SELECT source_item_id,target_item_id FROM relation_revision_details"
        ).fetchone() == (
            legacy["items"]["decision"][0],
            legacy["items"]["constraint"][0],
        )
        assert c.execute(
            "SELECT count(*) FROM item_revision_types WHERE fact_from IS NOT NULL OR valid_from IS NOT NULL"
        ).fetchone() == (0,)


def test_empty_head_upgrade(empty_database):
    command.upgrade(empty_database, HEAD)
    with connect() as c:
        assert c.execute("SELECT count(*) FROM semantic_type_versions").fetchone() == (
            11,
        )
        assert "entity_revision_details" not in table_names(c)


@pytest.mark.parametrize("failure", ["incomplete_relation", "temporal", "mixed_shape"])
def test_incompatible_legacy_aborts_whole_migration(legacy, failure):
    # Add new historical rows through QH-4 API, never mutate an existing revision.
    with connect() as c:
        item, rev = uuid4(), uuid4()
        content, cat = {"text": "Legacy"}, "relationship"
        if failure == "temporal":
            cat, content = (
                "decision",
                {"text": "Legacy", "temporal": {"fact_from": "2020-01-01"}},
            )
        if failure == "mixed_shape":
            item, cat = legacy["items"]["decision"][0], "entity"
        else:
            c.execute(
                "INSERT INTO understanding_items(id,context_space_id) VALUES (%s,%s)",
                (item, legacy["space"]),
            )
        insert_revision(
            c,
            legacy,
            revision_id=rev,
            item_id=item,
            number=2,
            category=cat,
            content=content,
        )
    with connect() as c:
        before = snapshot(c)
    with pytest.raises(Exception, match="legacy|Legacy"):
        command.upgrade(legacy["config"], HEAD)
    with connect() as c:
        assert snapshot(c) == before
        assert "semantic_type_versions" not in table_names(c)
        assert c.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0002_oidc_identities",
        )


def test_registered_new_type_and_schema_versions_without_migration(migrated):
    with connect() as c:
        register(c)
        first = publish(c, migrated, type_id="test.observation")
        register(
            c,
            version=2,
            schema={
                "type": "object",
                "required": ["value"],
                "properties": {"value": {"type": "integer"}},
                "additionalProperties": False,
            },
        )
        second = publish(
            c, migrated, type_id="test.observation", version=2, content={"value": 7}
        )
        force(c)
        assert c.execute("SELECT version_num FROM alembic_version").fetchone() == (
            HEAD,
        )
        assert c.execute(
            "SELECT type_version FROM item_revision_types WHERE item_revision_id IN (%s,%s) ORDER BY type_version",
            (first[1], second[1]),
        ).fetchall() == [(1,), (2,)]
        for version, content in ((1, {"text": 7}), (2, {"text": "old shape"})):
            with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
                publish(
                    c,
                    migrated,
                    type_id="test.observation",
                    version=version,
                    content=content,
                )
                force(c)


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "unsupported": True},
        {"type": "object", "$ref": "https://example.invalid"},
        {"type": "object", "properties": {"a": {"type": "invalid"}}},
        {"type": "object", "required": None},
        {"type": "object", "additionalProperties": {}},
    ],
)
def test_unsupported_schema_rejected(migrated, schema):
    with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        register(c, schema=schema)


@pytest.mark.parametrize(
    "failure",
    [
        "unknown_type",
        "unknown_version",
        "missing_binding",
        "missing_provenance",
        "legacy_category",
        "shape_change",
        "isolation",
    ],
)
def test_invalid_publication_rejected(migrated, failure):
    with (
        connect() as c,
        pytest.raises(
            (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation)
        ),
    ):
        if failure in ("unknown_type", "unknown_version"):
            publish(
                c,
                migrated,
                type_id="unknown.type" if failure == "unknown_type" else "qh.decision",
                version=99,
            )
        elif failure == "missing_binding":
            item = uuid4()
            c.execute(
                "INSERT INTO understanding_items(id,context_space_id) VALUES (%s,%s)",
                (item, migrated["space"]),
            )
            insert_revision(c, migrated, item_id=item, category=None)
        elif failure == "missing_provenance":
            rev, item = uuid4(), uuid4()
            c.execute(
                "INSERT INTO understanding_items(id,context_space_id) VALUES (%s,%s)",
                (item, migrated["space"]),
            )
            c.execute(
                "INSERT INTO item_revision_types(item_revision_id,context_space_id,type_id,type_version) VALUES (%s,%s,'qh.decision',1)",
                (rev, migrated["space"]),
            )
            insert_revision(c, migrated, revision_id=rev, item_id=item, category=None)
        elif failure == "legacy_category":
            insert_revision(
                c, migrated, item_id=migrated["items"]["decision"][0], number=2
            )
        elif failure == "shape_change":
            publish(
                c,
                migrated,
                item=migrated["items"]["decision"][0],
                number=2,
                type_id="qh.entity",
            )
        else:
            c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            publish(c, migrated)
        force(c)


@pytest.mark.parametrize(
    "endpoints",
    [
        ("decision", "constraint"),
        ("hypothesis", "entity"),
        ("relationship", "decision"),
    ],
)
def test_universal_endpoint_shapes(migrated, endpoints):
    with connect() as c:
        relation = publish(
            c,
            migrated,
            type_id="qh.relationship",
            relation=(
                migrated["items"][endpoints[0]],
                migrated["items"][endpoints[1]],
                "related_to",
            ),
        )
        force(c)
        assert c.execute(
            "SELECT source_item_id,target_item_id FROM relation_revision_details WHERE item_revision_id=%s",
            (relation[1],),
        ).fetchone() == (
            migrated["items"][endpoints[0]][0],
            migrated["items"][endpoints[1]][0],
        )


@pytest.mark.parametrize(
    "failure",
    ["identity", "foreign_scope", "missing_anchor", "missing_detail", "wrong_shape"],
)
def test_endpoint_integrity_and_relation_shape(migrated, failure):
    with (
        connect() as c,
        pytest.raises(
            (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation)
        ),
    ):
        source = migrated["items"]["decision"]
        target = migrated["items"]["constraint"]
        if failure == "identity":
            source = (target[0], source[1])
        if failure == "missing_anchor":
            source = (source[0], uuid4())
        if failure == "foreign_scope":
            other_source, other_revision = uuid4(), uuid4()
            c.execute(
                "INSERT INTO sources(id,context_space_id,name) VALUES (%s,%s,'Other')",
                (other_source, migrated["other_space"]),
            )
            c.execute(
                "INSERT INTO source_revisions(id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,1,'Synthetic other-space evidence','{}')",
                (other_revision, other_source, migrated["other_space"]),
            )
            source = publish(
                c,
                {**migrated, "source_revision": other_revision},
                space=migrated["other_space"],
            )
            force(c)  # The foreign anchor is a valid, fully published item.
        publish(
            c,
            migrated,
            type_id="qh.decision" if failure == "wrong_shape" else "qh.relationship",
            relation=None
            if failure == "missing_detail"
            else (source, target, "related_to"),
        )
        force(c)


def rule(source, target, predicate="depends_on"):
    return {
        "mode": "allowlist",
        "entries": [
            {
                "predicate": predicate,
                "source_type": source,
                "source_version": 1,
                "target_type": target,
                "target_version": 1,
            }
        ],
    }


def test_rules_pinned_to_relation_type_version(migrated):
    with connect() as c:
        register(
            c, "test.link", shape="relation", rules=rule("qh.decision", "qh.constraint")
        )
        old = publish(
            c,
            migrated,
            type_id="test.link",
            relation=(
                migrated["items"]["decision"],
                migrated["items"]["constraint"],
                "depends_on",
            ),
        )
        force(c)
        register(
            c,
            "test.link",
            version=2,
            shape="relation",
            rules=rule("qh.preference", "qh.objective", "conflicts_with"),
        )
        force(c)
        assert c.execute(
            "SELECT type_version FROM item_revision_types WHERE item_revision_id=%s",
            (old[1],),
        ).fetchone() == (1,)
        with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
            publish(
                c,
                migrated,
                type_id="test.link",
                version=2,
                relation=(
                    migrated["items"]["decision"],
                    migrated["items"]["constraint"],
                    "depends_on",
                ),
            )
            force(c)
        new = publish(
            c,
            migrated,
            type_id="test.link",
            version=2,
            relation=(
                migrated["items"]["preference"],
                migrated["items"]["objective"],
                "conflicts_with",
            ),
        )
        force(c)
        assert new != old


@pytest.mark.parametrize(
    "rules",
    [
        None,
        {},
        {"mode": None},
        {"mode": "allowlist", "entries": []},
        {"mode": "allowlist", "entries": [{"predicate": None}]},
        {"mode": "any_registered", "unknown": True},
    ],
)
def test_malformed_rules_fail_closed(migrated, rules):
    with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        register(c, "test.link", shape="relation", rules=rules)


@pytest.mark.parametrize("kind", ["item", "entity", "relation"])
def test_universal_temporal_metadata(migrated, kind):
    with connect() as c:
        rel = (
            (
                migrated["items"]["decision"],
                migrated["items"]["constraint"],
                "depends_on",
            )
            if kind == "relation"
            else None
        )
        type_id = {
            "item": "qh.preference",
            "entity": "qh.entity",
            "relation": "qh.relationship",
        }[kind]
        known = publish(
            c,
            migrated,
            type_id=type_id,
            relation=rel,
            times=(
                "2020-01-01T10:00:00Z",
                "2020-01-01T10:00:00Z",
                "2020-01-01T00:00:00Z",
                "2020-02-01T00:00:00Z",
            ),
        )
        unknown = publish(c, migrated, type_id=type_id, relation=rel)
        force(c)
        assert c.execute(
            "SELECT fact_from IS NOT NULL, valid_from IS NOT NULL FROM item_revision_types WHERE item_revision_id=%s",
            (known[1],),
        ).fetchone() == (True, True)
        assert (
            c.execute(
                "SELECT fact_from,fact_to,valid_from,valid_to FROM item_revision_types WHERE item_revision_id=%s",
                (unknown[1],),
            ).fetchone()
            == (None,) * 4
        )


@pytest.mark.parametrize(
    "times",
    [
        ("2022-01-01", "2021-01-01", None, None),
        (None, None, "2022-01-01", "2022-01-01"),
    ],
)
def test_invalid_temporal_bounds(migrated, times):
    with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        publish(c, migrated, times=times)


@pytest.mark.parametrize(
    "table",
    [
        "semantic_type_versions",
        "item_revision_types",
        "relation_revision_details",
        "understanding_item_revisions",
        "item_revision_provenance",
        "source_revisions",
    ],
)
@pytest.mark.parametrize("operation", ["update", "delete", "truncate"])
def test_history_immutable(migrated, table, operation):
    query = {
        "update": "UPDATE {} SET context_space_id=context_space_id",
        "delete": "DELETE FROM {}",
        "truncate": "TRUNCATE {} CASCADE",
    }[operation]
    if table == "semantic_type_versions" and operation == "update":
        query = "UPDATE {} SET version=version"
    with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        c.execute(sql.SQL(query).format(sql.Identifier(table)))


def test_late_binding_or_detail_cannot_extend_history(migrated):
    with connect() as c:
        for table, values in (
            (
                "item_revision_types",
                (migrated["items"]["decision"][1], migrated["space"], "qh.decision", 1),
            ),
        ):
            with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
                c.execute(
                    sql.SQL(
                        "INSERT INTO {} (item_revision_id,context_space_id,type_id,type_version) VALUES (%s,%s,%s,%s)"
                    ).format(sql.Identifier(table)),
                    values,
                )
        with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
            c.execute(
                "INSERT INTO relation_revision_details VALUES (%s,%s,%s,%s,%s,%s,'x')",
                (
                    migrated["items"]["decision"][1],
                    migrated["space"],
                    *migrated["items"]["decision"],
                    *migrated["items"]["constraint"],
                ),
            )


def test_atomic_rollback_and_confirmed_current(migrated):
    with connect() as c:
        before = c.execute(
            "SELECT count(*) FROM understanding_item_revisions"
        ).fetchone()
        with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
            publish(c, migrated)
            publish(c, migrated, type_id="qh.relationship")
            force(c)
        assert (
            c.execute("SELECT count(*) FROM understanding_item_revisions").fetchone()
            == before
        )
        decision = migrated["items"]["decision"]
        newer = publish(c, migrated, item=decision[0], number=2)
        force(c)
        assert c.execute(
            "SELECT current_revision_id FROM understanding_items WHERE id=%s",
            (decision[0],),
        ).fetchone() == (decision[1],)
        with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
            c.execute(
                "UPDATE understanding_items SET current_revision_id=%s WHERE id=%s",
                (newer[1], decision[0]),
            )


def test_concurrent_different_shapes_cannot_publish(migrated):
    item = uuid4()
    with connect() as c:
        c.execute(
            "INSERT INTO understanding_items(id,context_space_id) VALUES (%s,%s)",
            (item, migrated["space"]),
        )
    app = "qh30_concurrency_" + uuid4().hex

    def second():
        with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
            c.execute("SELECT set_config('application_name',%s,false)", (app,))
            c.execute("SET statement_timeout='8s'")
            publish(c, migrated, item=item, number=2, type_id="qh.entity")
            force(c)

    with connect() as first, ThreadPoolExecutor(max_workers=1) as pool:
        publish(first, migrated, item=item)
        future = pool.submit(second)
        deadline = time.monotonic() + 5
        while first.execute(
            "SELECT wait_event_type FROM pg_stat_activity WHERE application_name=%s",
            (app,),
        ).fetchone() != ("Lock",):
            assert time.monotonic() < deadline, (
                "Second publisher did not block on item identity"
            )
            time.sleep(0.03)
            first.execute("SELECT pg_stat_clear_snapshot()")
        force(first)
        first.commit()
        future.result(timeout=8)
    with connect() as c:
        assert c.execute(
            "SELECT count(*) FROM understanding_item_revisions WHERE item_id=%s",
            (item,),
        ).fetchone() == (1,)


def test_forward_only_downgrade_refused_without_data_change(migrated):
    with connect() as c:
        before = snapshot(c)
    with pytest.raises(RuntimeError, match="forward-only"):
        command.downgrade(migrated["config"], "0002_oidc_identities")
    with connect() as c:
        assert snapshot(c) == before
        assert c.execute("SELECT version_num FROM alembic_version").fetchone() == (
            HEAD,
        )


@pytest.mark.parametrize(
    "schema,value,expected",
    [
        ({"type": "integer"}, True, False),
        ({"type": "integer"}, "2", False),
        ({"type": "integer"}, 2.5, False),
        ({"type": "integer"}, 2.0, True),
        ({"type": "object", "enum": [{"a": 1}]}, {"a": 1, "extra": 2}, False),
        ({"type": "object", "required": ["text"]}, {}, False),
        ({"type": "array", "items": {"type": "string"}}, ["a", 1], False),
        ({"type": "array", "items": {"type": "string"}}, ["a"], True),
        ({"type": "null"}, None, True),
    ],
)
def test_schema_validation_boundaries(migrated, schema, value, expected):
    with connect() as c:
        assert c.execute(
            "SELECT qh30_schema_matches(%s,%s)", (Jsonb(schema), Jsonb(value))
        ).fetchone() == (expected,)


def test_endpoint_rule_version_checks_anchor_not_current(migrated):
    with connect() as c:
        register(c, "test.observation")
        old = publish(c, migrated, type_id="test.observation")
        register(c, "test.observation", version=2)
        publish(
            c, migrated, item=old[0], number=2, type_id="test.observation", version=2
        )
        register(
            c,
            "test.link",
            shape="relation",
            rules=rule("test.observation", "qh.constraint"),
        )
        relation = publish(
            c,
            migrated,
            type_id="test.link",
            relation=(old, migrated["items"]["constraint"], "depends_on"),
        )
        force(c)
        assert c.execute(
            "SELECT source_revision_id FROM relation_revision_details WHERE item_revision_id=%s",
            (relation[1],),
        ).fetchone() == (old[1],)
        assert c.execute(
            "SELECT count(*) FROM understanding_item_revisions WHERE item_id=%s",
            (old[0],),
        ).fetchone() == (2,)


def test_concurrent_registration_cannot_change_shape(migrated):
    app = "qh30_type_race_" + uuid4().hex

    def second():
        with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
            c.execute("SELECT set_config('application_name',%s,false)", (app,))
            c.execute("SET statement_timeout='8s'")
            register(c, "test.concurrent", version=2, shape="entity")

    with connect() as first, ThreadPoolExecutor(max_workers=1) as pool:
        register(first, "test.concurrent")
        future = pool.submit(second)
        deadline = time.monotonic() + 5
        try:
            while first.execute(
                "SELECT wait_event_type FROM pg_stat_activity WHERE application_name=%s",
                (app,),
            ).fetchone() != ("Lock",):
                assert time.monotonic() < deadline
                time.sleep(0.02)
                first.execute("SELECT pg_stat_clear_snapshot()")
        finally:
            first.commit()
        future.result(timeout=8)


def test_binding_assembly_races_with_publication(migrated):
    app = "qh30_metadata_race_" + uuid4().hex

    def second(revision):
        with connect() as c, pytest.raises(psycopg.errors.CheckViolation):
            c.execute("SELECT set_config('application_name',%s,false)", (app,))
            c.execute("SET statement_timeout='8s'")
            c.execute(
                "INSERT INTO item_revision_types(item_revision_id,context_space_id,type_id,type_version) VALUES (%s,%s,'qh.decision',1)",
                (revision, migrated["space"]),
            )

    with connect() as first, ThreadPoolExecutor(max_workers=1) as pool:
        item, revision = publish(first, migrated)
        future = pool.submit(second, revision)
        deadline = time.monotonic() + 5
        try:
            while first.execute(
                "SELECT wait_event_type FROM pg_stat_activity WHERE application_name=%s",
                (app,),
            ).fetchone() != ("Lock",):
                assert time.monotonic() < deadline
                time.sleep(0.02)
                first.execute("SELECT pg_stat_clear_snapshot()")
            force(first)
        finally:
            first.commit()
        future.result(timeout=8)


def test_existing_qh4_data_upgrades_through_qh5(legacy):
    command.downgrade(legacy["config"], "0001_qh_schema")
    with connect() as c:
        before = c.execute(
            "SELECT to_jsonb(r)::text FROM understanding_item_revisions r ORDER BY id"
        ).fetchall()
        assert "user_identities" not in table_names(c)
    command.upgrade(legacy["config"], HEAD)
    with connect() as c:
        assert (
            c.execute(
                "SELECT to_jsonb(r)::text FROM understanding_item_revisions r ORDER BY id"
            ).fetchall()
            == before
        )
        assert "user_identities" in table_names(c)
        assert c.execute("SELECT count(*) FROM item_revision_types").fetchone() == (11,)


def test_temporal_retrieval_does_not_promote_unknown(migrated):
    with connect() as c:
        known = publish(
            c,
            migrated,
            times=("2020-01-01Z", "2020-01-01Z", "2020-01-01Z", "2021-01-01Z"),
        )
        unknown = publish(c, migrated)
        force(c)
        assert c.execute(
            "SELECT item_revision_id FROM item_revision_types WHERE valid_from <= '2020-06-01Z'::timestamptz AND valid_to > '2020-06-01Z'::timestamptz"
        ).fetchall() == [(known[1],)]
        assert c.execute(
            "SELECT fact_from IS NULL AND valid_from IS NULL FROM item_revision_types WHERE item_revision_id=%s",
            (unknown[1],),
        ).fetchone() == (True,)
