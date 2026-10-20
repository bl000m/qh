"""Canonical draft integrity, CAS and transaction rollback in disposable SQL only."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4

from alembic import command
import psycopg
import pytest

from adapters.postgres.projection_drafts import PostgresDraftRepository
from app.projections.drafts import ProjectionConflict, ProjectionNotFound, RevisionKey
from tests.test_projection_drafts import run, spec
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only


@pytest.fixture
def drafts(generic, empty_database):
    p=generic
    command.upgrade(empty_database,'0007_projection_drafts')
    a,b=revision(p,'Included pilot'),revision(p,'Private constraint')
    p['repo'].save(sources=[p['source']],revisions=[a,b])
    p.update(drafts=PostgresDraftRepository(url=p['repo'].url),rows=(a,b))
    return p


def refs(p):
    return tuple(RevisionKey(item_id=r['item_id'],revision_id=r['id']) for r in p['rows'])


def test_durable_draft_crud_and_canonical_rows_preserved(drafts):
    p=drafts;alice=p['repo'].subject_id;scope=p['scope'];a,b=refs(p)
    before=p['repo'].read_snapshot((scope,))
    value=run(p['drafts'].create(alice,scope,spec(included=(a,b),excluded=(b,))))
    assert value.owner_id==alice and value.version==1 and value.state=='draft'
    reopened=PostgresDraftRepository(url=p['repo'].url)
    assert run(reopened.read(alice,scope,value.id))==value
    updated=run(reopened.replace(alice,scope,value.id,1,spec(included=(b,))))
    assert updated.version==2 and updated.spec.effective==(b,)
    assert p['repo'].read_snapshot((scope,))==before
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) AS n FROM owner_organization').fetchone()['n']==0
        assert c.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_name IN ('shares','approved_snapshots')").fetchone()['n']==0


def test_invalid_pairs_foreign_scope_and_stale_edit_commit_nothing(drafts):
    p=drafts;alice=p['repo'].subject_id;scope=p['scope'];a,b=refs(p)
    value=run(p['drafts'].create(alice,scope,spec(included=(a,))))
    for subject,target,draft_id in ((str(uuid4()),scope,value.id),(alice,p['sibling'],value.id),(alice,scope,str(uuid4()))):
        with pytest.raises(ProjectionNotFound):run(p['drafts'].read(subject,target,draft_id))
    with pytest.raises(ProjectionNotFound):
        run(p['drafts'].replace(alice,scope,value.id,1,spec(included=(replace(a,item_id=b.item_id),))))
    with pytest.raises(ProjectionConflict):run(p['drafts'].replace(alice,scope,value.id,2,spec()))
    assert run(p['drafts'].read(alice,scope,value.id))==value
    with p['repo'].connect() as c:
        with pytest.raises(psycopg.errors.ForeignKeyViolation), c.transaction():
            c.execute('INSERT INTO projection_draft_entries VALUES (%s,%s,%s,%s,%s)',
                (value.id,scope,'exclude',b.item_id,a.revision_id))
        with pytest.raises(psycopg.errors.CheckViolation), c.transaction():
            c.execute('UPDATE projection_drafts SET context_space_id=%s,version=2 WHERE id=%s',(p['sibling'],value.id))


def test_simultaneous_edits_have_exactly_one_winner(drafts):
    p=drafts;alice=p['repo'].subject_id;scope=p['scope']
    draft=run(p['drafts'].create(alice,scope,spec()))
    def edit(_):
        try:return run(p['drafts'].replace(alice,scope,draft.id,1,spec(purpose='Edited'))).version
        except ProjectionConflict:return 'conflict'
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(edit,range(2)))
    assert set(results)=={2,'conflict'}
