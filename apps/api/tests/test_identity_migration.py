import asyncio
from uuid import uuid4

from alembic import command
import psycopg
import pytest

from adapters.postgres.config import database_url
from adapters.postgres.demo_identities import DEMO_IDENTITIES, provision_demo
from adapters.postgres.security import PostgresSecurityReader
from tests.oidc_database import connect, isolated_database
from tests.test_migrations import insert_revision, TABLES


def test_additive_identity_migration_preserves_canonical_data_and_mapping():
    with isolated_database() as config:
        data = {key: uuid4() for key in ("owner", "space", "source", "source_revision", "item", "revision")}
        with connect() as c:
            c.execute("INSERT INTO users (id,display_name) VALUES (%s,'Existing owner')", (data["owner"],))
            c.execute("INSERT INTO context_spaces (id,owner_id,name) VALUES (%s,%s,'Existing space')", (data["space"], data["owner"]))
            c.execute("INSERT INTO sources (id,context_space_id,name) VALUES (%s,%s,'Evidence')", (data["source"], data["space"]))
            c.execute("INSERT INTO source_revisions (id,source_id,context_space_id,revision_no,content,origin) VALUES (%s,%s,%s,1,'Original','{}')", (data["source_revision"], data["source"], data["space"]))
            c.execute("INSERT INTO understanding_items (id,context_space_id) VALUES (%s,%s)", (data["item"], data["space"]))
            c.execute("INSERT INTO item_revision_provenance VALUES (%s,%s,%s)", (data["revision"], data["source_revision"], data["space"]))
            insert_revision(c, data, revision_id=data["revision"], state="confirmed")
            c.execute("UPDATE understanding_items SET current_revision_id=%s", (data["revision"],))
        def snapshot():
            with connect() as c:
                return {t: c.execute('SELECT row_to_json(t) FROM "' + t + '" t ORDER BY row_to_json(t)::text').fetchall() for t in TABLES}
        before = snapshot()
        command.upgrade(config, "0002_oidc_identities")
        command.upgrade(config, "0002_oidc_identities")
        assert snapshot() == before
        with connect() as c:
            assert c.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002_oidc_identities",)
        command.downgrade(config, "0001_qh_schema")
        assert snapshot() == before
        command.upgrade(config, "0002_oidc_identities")
        issuer = "http://localhost:8080/realms/qh"
        with connect() as c:
            provision_demo(c, issuer=issuer)
            provision_demo(c, issuer=issuer)
            assert c.execute("SELECT count(*) FROM user_identities").fetchone() == (2,)
            assert c.execute("SELECT count(*) FROM users").fetchone() == (3,)
            for query, args, error in [
                ("INSERT INTO user_identities VALUES (%s,%s,%s,now())", (issuer, DEMO_IDENTITIES[0][2], data["owner"]), psycopg.errors.UniqueViolation),
                ("INSERT INTO user_identities VALUES (%s,%s,%s,now())", ("", "x", data["owner"]), psycopg.errors.CheckViolation),
                ("INSERT INTO user_identities VALUES (%s,%s,%s,now())", ("other", "x", uuid4()), psycopg.errors.ForeignKeyViolation),
            ]:
                with pytest.raises(error), c.transaction():
                    c.execute(query, args)
            c.execute("UPDATE user_identities SET user_id=%s WHERE subject=%s", (data["owner"], DEMO_IDENTITIES[0][2]))
            with pytest.raises(ValueError), c.transaction():
                provision_demo(c, issuer=issuer)
            c.execute("UPDATE user_identities SET user_id=%s WHERE subject=%s", (DEMO_IDENTITIES[0][1], DEMO_IDENTITIES[0][2]))
        reader = PostgresSecurityReader(url=database_url())
        assert asyncio.run(reader.resolve_identity(issuer, DEMO_IDENTITIES[0][2])) == str(DEMO_IDENTITIES[0][1])
        assert asyncio.run(reader.resolve_identity("other-issuer", DEMO_IDENTITIES[0][2])) is None
        assert asyncio.run(reader.owner_for(str(data["space"]))) == str(data["owner"])
        assert asyncio.run(reader.owner_for("invalid")) is None
        with connect() as c:
            c.execute("UPDATE users SET status='disabled' WHERE id=%s", (DEMO_IDENTITIES[0][1],))
        assert asyncio.run(reader.resolve_identity(issuer, DEMO_IDENTITIES[0][2])) is None
