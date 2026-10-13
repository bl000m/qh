"""Disposable DB persistence markers, executed only inside the backend container.

An explicit UUID identifies an isolated SQL schema and one Neo4j node. Cleanup
removes only that probe's data; it never resets databases or deletes volumes.
"""

import argparse
import os
from uuid import UUID

from neo4j import GraphDatabase
import psycopg
from psycopg import sql


def probe(mode: str, token: str) -> None:
    schema = sql.Identifier(f"qh3_probe_{token}")
    table = sql.SQL("{}.marker").format(schema)
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        if mode == "write":
            connection.execute(sql.SQL("CREATE SCHEMA {}").format(schema))
            connection.execute(sql.SQL("CREATE TABLE {} (value text NOT NULL)").format(table))
            connection.execute(sql.SQL("INSERT INTO {} VALUES (%s)").format(table), (token,))
        elif mode == "read":
            row = connection.execute(sql.SQL("SELECT value FROM {}").format(table)).fetchall()
            if row != [(token,)]:
                raise RuntimeError("PostgreSQL persistence marker missing")
        else:
            connection.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(table))
            # No CASCADE: refuse to remove any unexpected objects in this schema.
            connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {}").format(schema))
            if connection.execute("SELECT to_regnamespace(%s)", (f"qh3_probe_{token}",)).fetchone() != (None,):
                raise RuntimeError("PostgreSQL probe cleanup incomplete")

    with GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        connection_timeout=10,
    ) as driver:
        if mode == "write":
            driver.execute_query(
                "CREATE (:QH3PersistenceProbe {probe_id: $token, value: $token})", token=token,
            )
        elif mode == "read":
            records, _, _ = driver.execute_query(
                "MATCH (n:QH3PersistenceProbe {probe_id: $token}) RETURN n.value AS value", token=token,
            )
            if [record["value"] for record in records] != [token]:
                raise RuntimeError("Neo4j persistence marker missing")
        else:
            # No DETACH: no unrelated relationships or nodes are removed.
            driver.execute_query("MATCH (n:QH3PersistenceProbe {probe_id: $token}) DELETE n", token=token)
            records, _, _ = driver.execute_query(
                "MATCH (n:QH3PersistenceProbe {probe_id: $token}) RETURN count(n) AS count", token=token,
            )
            if records[0]["count"] != 0:
                raise RuntimeError("Neo4j probe cleanup incomplete")
    print(f"PASS: {mode} markers in both databases")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("write", "read", "cleanup"))
    parser.add_argument("token", type=lambda value: UUID(value).hex)
    args = parser.parse_args()
    try:
        probe(args.mode, args.token)
    except Exception:
        # Driver exceptions may include connection details; keep shared logs safe.
        raise SystemExit(f"FAIL: {args.mode} persistence probe; token {args.token}") from None
