"""Create a uniquely named isolated database; retain it for inspection."""

from contextlib import contextmanager
import os
from uuid import uuid4

from alembic import command
from alembic.config import Config
import psycopg
from psycopg import sql

from adapters.postgres.config import database_url


def connect():
    url = database_url()
    return psycopg.connect(host=url.host, port=url.port, dbname=url.database,
                          user=url.username, password=url.password, connect_timeout=5)


def application_snapshot(connection):
    tables = {row[0] for row in connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchall() if "alembic_version" in tables else None
    users = connection.execute("SELECT count(*) FROM users").fetchone() if "users" in tables else None
    return tables, revision, users


@contextmanager
def isolated_database():
    original = os.environ["POSTGRES_DB"]
    if os.environ.get("QH30_SQL_TEST") == "1":
        assert os.environ["POSTGRES_HOST"] == "qh30-sql-test", "Dedicated QH-30 server required"
        assert original == "qh30_admin", "Dedicated disposable admin DB required"
    else:
        assert os.environ["POSTGRES_HOST"] == "postgres", "Only local Compose PostgreSQL permitted"
        assert original == "qh", "Unexpected application database: stop"
    name = "qh5_test_" + uuid4().hex
    with connect() as application:
        before = application_snapshot(application)
        assert before[1] in (None, [("0001_qh_schema",)], [("0002_oidc_identities",)],
                             [("0003_native_semantics",)], [("0004_projection_outbox",)]), "Unexpected application revision: stop"
        assert before[1] is not None or not before[0], "Unversioned nonempty schema: stop"
    with connect() as admin:
        admin.autocommit = True
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
    os.environ["POSTGRES_DB"] = name
    try:
        config = Config("adapters/postgres/alembic.ini")
        command.upgrade(config, "0001_qh_schema")
        print("Isolated retained database:", name)
        yield config
    finally:
        os.environ["POSTGRES_DB"] = original
        with connect() as application:
            assert application_snapshot(application) == before
