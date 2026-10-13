"""Real PostgreSQL migration tests; each owns a newly created empty database."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time
from uuid import uuid4

from alembic import command
from alembic.config import Config
import psycopg
from psycopg import sql
import pytest
from psycopg.types.json import Jsonb

from adapters.postgres.config import database_url

CONFIG_PATH = Path(__file__).resolve().parents[1] / "adapters/postgres/alembic.ini"
TABLES = {"users", "context_spaces", "sources", "source_revisions", "understanding_items",
          "understanding_item_revisions", "item_revision_provenance"}


def connect():
    url = database_url()
    return psycopg.connect(host=url.host, port=url.port, dbname=url.database,
                          user=url.username, password=url.password, connect_timeout=10)


@pytest.fixture
def empty_database(monkeypatch):
    name = f"qh4_test_{uuid4().hex}"
    admin = connect()
    admin.autocommit = True
    # CREATE must succeed before entering cleanup: never touch a preexisting DB.
    admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
    monkeypatch.setenv("POSTGRES_DB", name)
    try:
        with connect() as connection:
            assert table_names(connection) == set()
        yield Config(str(CONFIG_PATH))
    finally:
        # Only this test-created database, no FORCE or persistent volume cleanup.
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        assert admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone() is None
        admin.close()


def table_names(connection) -> set[str]:
    return {row[0] for row in connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )}


def test_empty_database_upgrade_rollback_and_reapply(empty_database) -> None:
    config = empty_database
    command.upgrade(config, "0001_qh_schema")
    with connect() as connection:
        assert table_names(connection) == TABLES | {"alembic_version"}
        assert connection.execute("SELECT version_num FROM alembic_version").fetchall() == [("0001_qh_schema",)]
        connection.execute("CREATE TABLE unrelated_marker (value text)")
        connection.execute("INSERT INTO unrelated_marker VALUES ('retained')")
    command.downgrade(config, "-1")
    with connect() as connection:
        assert table_names(connection) == {"alembic_version", "unrelated_marker"}
        assert connection.execute("SELECT version_num FROM alembic_version").fetchall() == []
        assert connection.execute("SELECT value FROM unrelated_marker").fetchone() == ("retained",)
        assert connection.execute("SELECT count(*) FROM pg_proc WHERE proname LIKE 'qh_%'").fetchone() == (0,)
    command.upgrade(config, "0001_qh_schema")
    command.upgrade(config, "0001_qh_schema")
    with connect() as connection:
        assert table_names(connection) == TABLES | {"alembic_version", "unrelated_marker"}


def insert_revision(connection, data, *, revision_id=None, item_id=None, space_id=None,
                    number=1, state="proposed", category="hypothesis", content=None,
                    origin="ai", based_on=None):
    revision_id = revision_id or uuid4()
    connection.execute(
        "INSERT INTO understanding_item_revisions "
        "(id,item_id,context_space_id,revision_no,category,content,origin_kind,validation_state,"
        "validated_by,validated_at,based_on_revision_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,CASE WHEN %s = 'proposed' THEN NULL ELSE CURRENT_TIMESTAMP END,%s)",
        (revision_id, item_id or data["item"], space_id or data["space"], number, category,
         Jsonb(content if content is not None else {"text": "Hypothesis", "certainty": "uncertain"}),
         origin, state, None if state == "proposed" else data["owner"], state, based_on),
    )
    return revision_id


@pytest.fixture
def persisted(empty_database):
    command.upgrade(empty_database, "0001_qh_schema")
    data = {key: uuid4() for key in ("owner", "space", "other_space", "source", "source_revision", "item", "revision")}
    with connect() as connection:
        connection.execute("INSERT INTO users (id,display_name) VALUES (%s,'Owner')", (data["owner"],))
        for space in (data["space"], data["other_space"]):
            connection.execute("INSERT INTO context_spaces (id,owner_id,name) VALUES (%s,%s,'Space')", (space, data["owner"]))
        connection.execute("INSERT INTO sources (id,context_space_id,name) VALUES (%s,%s,'Source')", (data["source"], data["space"]))
        connection.execute("INSERT INTO source_revisions (id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,1,'Original evidence',%s)",
                           (data["source_revision"], data["source"], data["space"], Jsonb({"kind": "conversation"})))
        connection.execute("INSERT INTO understanding_items (id,context_space_id) VALUES (%s,%s)", (data["item"], data["space"]))
        # Assemble references before publishing the revision, in one transaction.
        connection.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                           (data["revision"], data["source_revision"], data["space"]))
        insert_revision(connection, data, revision_id=data["revision"], state="confirmed")
        connection.execute("UPDATE understanding_items SET current_revision_id=%s WHERE id=%s", (data["revision"], data["item"]))
    return data


def test_canonical_content_and_inherited_owner(persisted) -> None:
    with connect() as connection:
        assert connection.execute("SELECT content,category,validation_state FROM understanding_item_revisions").fetchone() == (
            {"text": "Hypothesis", "certainty": "uncertain"}, "hypothesis", "confirmed")
        assert connection.execute("SELECT content FROM source_revisions").fetchone() == ("Original evidence",)
        for table in TABLES - {"users", "context_spaces"}:
            columns = {row[0] for row in connection.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))}
            assert "owner_id" not in columns
        assert connection.execute("SELECT cs.owner_id FROM understanding_items i JOIN context_spaces cs ON cs.id=i.context_space_id").fetchone() == (persisted["owner"],)


@pytest.mark.parametrize("table", ["source_revisions", "understanding_item_revisions", "item_revision_provenance"])
@pytest.mark.parametrize("operation", ["update", "delete", "truncate"])
def test_immutable_payloads_and_provenance(persisted, table, operation) -> None:
    statements = {
        "update": sql.SQL("UPDATE {} SET context_space_id=context_space_id"),
        "delete": sql.SQL("DELETE FROM {}"),
        "truncate": sql.SQL("TRUNCATE {} CASCADE"),
    }
    with connect() as connection:
        with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
            connection.execute(statements[operation].format(sql.Identifier(table)))
        assert connection.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))).fetchone() == (1,)


@pytest.mark.parametrize("state", ["proposed", "rejected"])
def test_proposals_and_rejections_cannot_be_current(persisted, state) -> None:
    with connect() as connection:
        revision = insert_revision(connection, persisted, number=2, state=state)
        assert connection.execute("SELECT current_revision_id FROM understanding_items").fetchone() == (persisted["revision"],)
        with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
            connection.execute("UPDATE understanding_items SET current_revision_id=%s", (revision,))


def test_confirmation_is_new_revision_and_does_not_auto_promote(persisted) -> None:
    with connect() as connection:
        proposal = insert_revision(connection, persisted, number=2)
        confirmed = insert_revision(connection, persisted, number=3, state="confirmed", based_on=proposal)
        assert connection.execute("SELECT current_revision_id FROM understanding_items").fetchone() == (persisted["revision"],)
        connection.execute("UPDATE understanding_items SET current_revision_id=%s", (confirmed,))
        assert connection.execute("SELECT validation_state FROM understanding_item_revisions WHERE id=%s", (proposal,)).fetchone() == ("proposed",)
        assert connection.execute("SELECT category FROM understanding_item_revisions WHERE id=%s", (confirmed,)).fetchone() == ("hypothesis",)


@pytest.mark.parametrize("change", [
    {"number": 1}, {"number": 0}, {"category": "unknown"}, {"state": "unknown"},
    {"content": ["not an object"]}, {"origin": "unknown"},
])
def test_invalid_revision_values_are_rejected(persisted, change) -> None:
    with connect() as connection:
        with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.UniqueViolation)), connection.transaction():
            insert_revision(connection, persisted, number=change.get("number", 2),
                            **{key: value for key, value in change.items() if key != "number"})


@pytest.mark.parametrize("violation", ["item_space", "source_space", "current_item", "predecessor_item", "orphan_source", "missing_validator"])
def test_reference_integrity(persisted, violation) -> None:
    data = persisted
    with connect() as connection:
        with pytest.raises((psycopg.errors.ForeignKeyViolation, psycopg.errors.CheckViolation)), connection.transaction():
            if violation == "item_space":
                insert_revision(connection, data, number=2, space_id=data["other_space"])
            elif violation == "source_space":
                connection.execute("INSERT INTO source_revisions (id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,2,'x','{}')",
                                   (uuid4(), data["source"], data["other_space"]))
            elif violation in ("current_item", "predecessor_item"):
                other_item = uuid4()
                connection.execute("INSERT INTO understanding_items (id,context_space_id) VALUES (%s,%s)", (other_item, data["space"]))
                if violation == "current_item":
                    connection.execute("UPDATE understanding_items SET current_revision_id=%s WHERE id=%s", (data["revision"], other_item))
                else:
                    insert_revision(connection, data, item_id=other_item, based_on=data["revision"])
            elif violation == "orphan_source":
                connection.execute("INSERT INTO sources (id,context_space_id,name) VALUES (%s,%s,'orphan')", (uuid4(), uuid4()))
            else:
                connection.execute("INSERT INTO understanding_item_revisions (id,item_id,context_space_id,revision_no,category,content,origin_kind,validation_state) VALUES (%s,%s,%s,2,'decision','{}','ai','confirmed')",
                                   (uuid4(), data["item"], data["space"]))


def test_provenance_cannot_cross_spaces_even_for_same_owner(persisted) -> None:
    with connect() as connection:
        with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
            revision = uuid4()
            connection.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                               (revision, persisted["source_revision"], persisted["space"]))
            item = uuid4()
            connection.execute("INSERT INTO understanding_items (id,context_space_id) VALUES (%s,%s)", (item, persisted["other_space"]))
            insert_revision(connection, persisted, revision_id=revision, item_id=item, space_id=persisted["other_space"])
            connection.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_published_provenance_cannot_be_extended(persisted) -> None:
    with connect() as connection:
        other_source_revision = uuid4()
        connection.execute("INSERT INTO source_revisions (id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,2,'next','{}')",
                           (other_source_revision, persisted["source"], persisted["space"]))
        with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
            connection.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                               (persisted["revision"], other_source_revision, persisted["space"]))


def test_unpublished_provenance_cannot_commit_without_revision(persisted) -> None:
    with connect() as connection:
        with pytest.raises(psycopg.errors.ForeignKeyViolation), connection.transaction():
            connection.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                               (uuid4(), persisted["source_revision"], persisted["space"]))
            connection.execute("SET CONSTRAINTS ALL IMMEDIATE")


@pytest.mark.parametrize("number", [0, 1])
def test_source_revision_numbers_are_positive_and_unique(persisted, number) -> None:
    with connect() as connection:
        with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.UniqueViolation)), connection.transaction():
            connection.execute("INSERT INTO source_revisions (id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,%s,'copy','{}')",
                               (uuid4(), persisted["source"], persisted["space"], number))


def test_concurrent_publication_cannot_extend_provenance(persisted) -> None:
    name = f"qh4_provenance_{uuid4().hex}"

    def append(revision):
        with connect() as connection:
            connection.execute("SELECT set_config('application_name', %s, false)", (name,))
            connection.execute("SET statement_timeout = '5s'")
            with pytest.raises(psycopg.errors.CheckViolation):
                connection.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                                   (revision, persisted["source_revision"], persisted["space"]))

    with connect() as publisher, ThreadPoolExecutor(max_workers=1) as executor:
        revision = insert_revision(publisher, persisted, number=2)
        pending = executor.submit(append, revision)
        deadline = time.monotonic() + 3
        try:
            while True:
                wait = publisher.execute("SELECT wait_event_type FROM pg_stat_activity WHERE application_name=%s", (name,)).fetchone()
                if wait == ("Lock",):
                    break
                assert time.monotonic() < deadline, "Second writer did not wait on publication lock"
                time.sleep(0.02)
                publisher.execute("SELECT pg_stat_clear_snapshot()")
        finally:
            publisher.commit()  # Release the lock even if observation failed.
        pending.result(timeout=6)
