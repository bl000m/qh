"""Explicit local demo provisioning; never called during API startup."""

from uuid import UUID

import psycopg

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
