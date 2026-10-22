"""Explicit cutover registration refuses existing data; real isolated SQL only."""
import importlib.util
from pathlib import Path
import sys
from uuid import uuid4

from alembic import command
import pytest

from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from tests.test_migrations import empty_database as empty_database


def test_explicit_provisioning_is_idempotent_preserves_registry_and_refuses_nonempty(empty_database, monkeypatch):
    command.upgrade(empty_database,'0006_owner_organization')
    repo=CanonicalRepository(url=database_url(),subject_id='')
    path=Path(__file__).resolve().parents[3]/'scripts/provision_qh_semantics.py'
    spec=importlib.util.spec_from_file_location('uum_provision',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(sys,'argv',[str(path),'--register-uum-profiles'])
    with repo.connect() as c:
        before=c.execute('SELECT * FROM semantic_type_versions ORDER BY type_id,version').fetchall()
    module.main();module.main()
    with repo.connect() as c:
        after=c.execute('SELECT * FROM semantic_type_versions ORDER BY type_id,version').fetchall()
        assert [r for r in after if r['version']!=3]==before
        assert len(after)==len(before)+3
        owner=str(uuid4())
        c.execute("INSERT INTO users(id,display_name) VALUES (%s,'UUM provisioning guard')",(owner,))
        c.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Existing data must not be converted')",(str(uuid4()),owner))
    with pytest.raises(RuntimeError,match='empty application'):
        module.main()
    with repo.connect() as c:
        assert c.execute('SELECT * FROM semantic_type_versions ORDER BY type_id,version').fetchall()==after
