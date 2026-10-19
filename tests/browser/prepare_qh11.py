"""Test-only provisioning inside a newly created, labelled disposable container."""
import os

from alembic import command
from alembic.config import Config
from adapters.postgres.demo_identities import provision_demo
from tests.oidc_database import connect

assert os.environ.get('QH11_BROWSER_TEST') == '1'
assert os.environ['POSTGRES_HOST'] == 'postgres' and os.environ['POSTGRES_DB'] == 'qh'
assert os.environ['QH_NATIVE_CONTEXT_ENABLED'] == 'false'
with connect() as connection:
    assert connection.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone() == (0,)
command.upgrade(Config('adapters/postgres/alembic.ini'), '0006_owner_organization')
with connect() as connection:
    provision_demo(connection, issuer=os.environ['OIDC_ISSUER'])
print('PASS: empty disposable database provisioned; two internal identities, no Spaces')
