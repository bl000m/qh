"""Explicit local demo provisioning; never called during API startup."""

from uuid import UUID

import psycopg
import os

from adapters.postgres.config import database_url

# QH IDs are independent from the fixed IdP subjects in the imported demo realm.
DEMO_IDENTITIES = (
    ("Alice", UUID("b9c1acb0-8e4a-4abd-a284-12112acfa101"), "2e381a22-b8e0-44d7-928b-52d6549da101"),
    ("Bob", UUID("b9c1acb0-8e4a-4abd-a284-12112acfa102"), "2e381a22-b8e0-44d7-928b-52d6549da102"),
)


def provision_demo(connection: psycopg.Connection, *, issuer: str) -> None:
    with connection.transaction():
        for display_name, user_id, subject in DEMO_IDENTITIES:
            connection.execute(
                "INSERT INTO users (id,display_name) VALUES (%s,%s) ON CONFLICT (id) DO NOTHING",
                (user_id, display_name),
            )
            row = connection.execute(
                "INSERT INTO user_identities (issuer,subject,user_id) VALUES (%s,%s,%s) "
                "ON CONFLICT (issuer,subject) DO UPDATE SET user_id=user_identities.user_id "
                "RETURNING user_id", (issuer, subject, user_id),
            ).fetchone()
            if row[0] != user_id:
                raise ValueError("Existing external identity cannot be rebound")


def require_identity_schema(connection) -> None:
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    if revision not in (("0002_oidc_identities",), ("0003_native_semantics",), ("0004_projection_outbox",), ("0005_retire_legacy_category",)):
        raise ValueError("A supported QH identity schema must be applied before provisioning")


def main() -> None:
    url = database_url()
    if url.host != "postgres" or url.database != "qh":
        raise SystemExit("Only the local QH development database may be provisioned.")
    with psycopg.connect(host=url.host, port=url.port, dbname=url.database,
                        user=url.username, password=url.password, connect_timeout=5) as connection:
        try:
            require_identity_schema(connection)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        provision_demo(connection, issuer=os.environ["OIDC_ISSUER"])
    print("Two local QH demo identities provisioned idempotently; no Context Spaces created.")


if __name__ == "__main__":
    main()
