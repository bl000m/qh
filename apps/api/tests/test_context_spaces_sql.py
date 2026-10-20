"""Dedicated PostgreSQL HTTP acceptance; no persistent QH target or Neo4j dependency."""

from dataclasses import replace
from uuid import UUID, uuid4

from alembic import command
from fastapi.testclient import TestClient
import pytest

from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.spaces import PostgresContextSpaceRepository
from app.bootstrap import create_runtime_app
from tests.test_context_spaces_api import ALICE, BOB, headers
from tests.test_migrations import connect, empty_database as empty_database
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_oidc_security import SETTINGS, build_auth


@pytest.fixture(params=['0002_oidc_identities', '0005_retire_legacy_category'])
def spaces_db(empty_database, monkeypatch, request):
    command.upgrade(empty_database, request.param)
    monkeypatch.setenv('QH_NATIVE_CONTEXT_ENABLED', 'false')
    with connect() as c:
        for id, sub in [(ALICE, 'external-alice'), (BOB, 'external-bob')]:
            c.execute('INSERT INTO users (id,display_name) VALUES (%s,%s)', (UUID(id), sub))
            c.execute('INSERT INTO user_identities (issuer,subject,user_id) VALUES (%s,%s,%s)',
                      (SETTINGS.issuer, sub, UUID(id)))
    return request.param


def application():
    app = create_runtime_app()
    reader = PostgresSecurityReader(url=database_url())
    auth, _ = build_auth(resolver=reader.resolve_identity)
    # Only the JWKS transport is a fixture: signature/claims, identity mapping,
    # bootstrap, service, owner lookup and all metadata SQL are real.
    app.state.security = replace(app.state.security, authenticate=auth.authenticate, authenticate_with_expiry=auth.authenticate_with_expiry, authenticate_session=auth.authenticate_session)
    assert app.state.security.policy is app.state.services.policy
    assert isinstance(app.state.services.context.repository, PostgresContextSpaceRepository)
    return app


def test_alice_bob_roundtrip_persistence_and_application_reopen(spaces_db):
    app = application()
    with TestClient(app) as client:
        r = client.post('/context-spaces', headers=headers(), json={"name": "Alice A 🧭"})
        assert r.status_code == 201
        space = r.json(); path = '/context-spaces/' + space['id']
        assert space['owner_id'] == ALICE
        assert client.get('/context-spaces', headers=headers()).json()['items'] == [space]
        assert client.get(path, headers=headers()).json() == space
        for method in ('get', 'patch'):
            args = {'json': {'name': 'Bob attempt'}} if method == 'patch' else {}
            r = getattr(client, method)(path, headers=headers('external-bob'), **args)
            assert r.status_code == 404
        assert client.get('/context-spaces', headers=headers('external-bob')).json()['items'] == []
        r = client.patch(path, headers=headers(), json={'name': "Renamed '; DROP TABLE users; --"})
        assert r.status_code == 200
        updated = r.json()
        assert updated['id'] == space['id'] and updated['created_at'] == space['created_at']
        assert updated['updated_at'] >= space['updated_at']
        for payload in ({'name': 'x', 'owner_id': BOB}, {'name': ''}, {'status': 'deleted'}):
            assert client.patch(path, headers=headers(), json=payload).status_code == 422
    # New application/service/repository and new DB connections, same persisted ID.
    with TestClient(application()) as reopened:
        assert reopened.get(path, headers=headers()).json() == updated
        assert reopened.get('/context-spaces', headers=headers()).json()['items'] == [updated]
    with connect() as c:
        assert c.execute('SELECT owner_id,name,status FROM context_spaces WHERE id=%s',
                         (UUID(space['id']),)).fetchone() == (UUID(ALICE), updated['name'], 'active')
        assert c.execute('SELECT count(*) FROM users').fetchone() == (2,)
        assert c.execute('SELECT version_num FROM alembic_version').fetchone() == (spaces_db,)


def test_inactive_spaces_and_users_are_not_accessible(spaces_db):
    with TestClient(application()) as client:
        a = client.post('/context-spaces', headers=headers(), json={'name': 'A'}).json()
        client.post('/context-spaces', headers=headers('external-bob'), json={'name': 'Private B'})
        with connect() as c:
            c.execute("UPDATE context_spaces SET status='archived' WHERE id=%s", (UUID(a['id']),))
        assert client.get('/context-spaces', headers=headers()).json()['items'] == []
        assert client.get('/context-spaces/' + a['id'], headers=headers()).status_code == 404
        with connect() as c:c.execute("UPDATE users SET status='inactive' WHERE id=%s", (UUID(ALICE),))
        assert client.post('/context-spaces', headers=headers(), json={'name': 'denied'}).status_code == 401


def test_owner_predicates_fence_stale_policy_permission(spaces_db):
    app = application()
    with TestClient(app) as client:
        a = client.post('/context-spaces', headers=headers(), json={'name': 'private A'}).json()
        async def stale_owner(_): return BOB
        app.state.services.policy._owner_for = stale_owner
        path = '/context-spaces/' + a['id']
        assert client.get(path, headers=headers('external-bob')).status_code == 404
        assert client.patch(path, headers=headers('external-bob'), json={'name': 'stolen'}).status_code == 404
    with connect() as c:
        assert c.execute('SELECT name FROM context_spaces WHERE id=%s', (UUID(a['id']),)).fetchone() == ('private A',)


def test_sql_storage_error_is_generic(spaces_db, caplog):
    app = application()
    app.state.services.context.repository = PostgresContextSpaceRepository(
        url=database_url().set(database='qh9_missing_' + uuid4().hex))
    with TestClient(app) as client:
        r = client.get('/context-spaces', headers=headers())
        assert r.status_code == 503 and r.json() == {'detail': 'Context service unavailable'}
        assert 'qh9_missing_' not in r.text + caplog.text
