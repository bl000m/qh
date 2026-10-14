"""The existing identity test preflight must handle a fresh CI database read-only."""

from uuid import uuid4

import psycopg
from psycopg import sql

from adapters.postgres.config import database_url
from tests.oidc_database import application_snapshot, connect


def test_unmigrated_ci_database_snapshot_is_read_only():
    name = "qh6_test_" + uuid4().hex
    with connect() as admin:
        admin.autocommit = True
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
    url = database_url()
    # Keep the fresh test DB for inspection, never touch application data.
    with psycopg.connect(host=url.host, port=url.port, dbname=name,
                        user=url.username, password=url.password) as connection:
        assert application_snapshot(connection) == (set(), None, None)
        assert application_snapshot(connection) == (set(), None, None)
