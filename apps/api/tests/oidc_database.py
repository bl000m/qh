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


@contextmanager
def isolated_database():
    original = os.environ["POSTGRES_DB"]
    assert os.environ["POSTGRES_HOST"] == "postgres", "Only local Compose PostgreSQL permitted"
    assert original == "qh", "Unexpected application database: stop"
    name = "qh5_test_" + uuid4().hex
    with connect() as application:
        before = application.execute("SELECT version_num FROM alembic_version").fetchall()
        assert before in ([("0001_qh_schema",)], [("0002_oidc_identities",)]), "Unexpected application revision: stop"
        before_users = application.execute("SELECT count(*) FROM users").fetchone()
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
            assert application.execute("SELECT version_num FROM alembic_version").fetchall() == before
            assert application.execute("SELECT count(*) FROM users").fetchone() == before_users
