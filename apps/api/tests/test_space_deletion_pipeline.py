"""One disposable SQL/Neo4j erasure: isolation, rollback, replay and stale worker."""
import asyncio
from copy import deepcopy
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

from alembic import command
import psycopg
from psycopg.types.json import Jsonb
import pytest

from adapters.context.incremental import ProjectionWorker
from adapters.context.runtime import NativeRuntime
from adapters.postgres.space_deletion import PostgresSpaceDeletion, TABLES
from adapters.postgres.guest import PostgresGuestRepository
from app.core.spaces import SpaceConfirmationMismatch
from app.core.models import ContextSpaceNotFound, ContextStorageUnavailable
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain


def run(value):return asyncio.run(value)


def seed(p):
    repo=p['repo'];scope=p['scope'];a,b=revision(p,'Pilot'),revision(p,'Team')
    relation=revision(p,'Selected by',shape='relation')
    relation['relation']=dict(source_item_id=a['item_id'],source_revision_id=a['id'],
        target_item_id=b['item_id'],target_revision_id=b['id'],predicate='selected_by')
    a.update(validation_state='confirmed',validated_by=repo.subject_id,validated_at='2026-10-30T10:00:00Z')
    repo.save(sources=[p['source']],revisions=[a,b,relation]);drain(p['worker'])
    successor=deepcopy(b);successor.update(id=str(uuid4()),revision_no=2,based_on_revision_id=b['id'])
    repo.save(revisions=[successor]);drain(p['worker'])
    doc,draft,preview,snapshot,invitation,challenge,session=[str(uuid4()) for _ in range(7)]
    with repo.connect() as c:
        c.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s',(a['id'],a['item_id']))
        c.execute('INSERT INTO source_documents(source_revision_id,context_space_id,filename,media_type,sha256,original) '
            "VALUES (%s,%s,'synthetic.pdf','application/pdf',%s,%s)",(p['source']['id'],scope,'a'*64,b'%PDF-synthetic'))
        c.execute('INSERT INTO context_intake(id,context_space_id,document) VALUES (%s,%s,%s)',(doc,scope,Jsonb(dict(kind='document'))))
        c.execute('INSERT INTO context_consolidations(id,context_space_id,version,intake_ids,source_revision_id,revision_ids) '
            'VALUES (%s,%s,1,%s,%s,%s)',(str(uuid4()),scope,[doc],p['source']['id'],[a['id'],b['id'],relation['id']]))
        c.execute("INSERT INTO context_consolidation_jobs VALUES (%s,%s,'idle',clock_timestamp())",(scope,str(uuid4())))
        c.execute("INSERT INTO projection_drafts(id,context_space_id,recipient_kind,recipient,purpose,version) VALUES (%s,%s,'subject','invite@example.test','Synthetic',1)",(draft,scope))
        c.execute("INSERT INTO projection_draft_entries VALUES (%s,%s,'include',%s,%s)",(draft,scope,a['item_id'],a['id']))
        policy=dict(rights=['READ'],recipient_email='invite@example.test')
        payload=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Allowed')])
        c.execute('INSERT INTO disclosure_previews(id,context_space_id,draft_id,policy,selection_stamp,payload,report,fingerprint) '
            'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(preview,scope,draft,Jsonb(policy),'a'*64,Jsonb(payload),Jsonb({}),'b'*64))
        c.execute('INSERT INTO approved_snapshots(id,context_space_id,preview_id,fingerprint,policy,payload,accepted_exceptions,approved_by) '
            'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(snapshot,scope,preview,'b'*64,Jsonb(policy),Jsonb(payload),Jsonb([]),repo.subject_id))
        c.execute('INSERT INTO approved_snapshot_revisions VALUES (%s,%s,%s,%s,%s)',(snapshot,scope,'R1',a['item_id'],a['id']))
        c.execute("INSERT INTO guest_invitations(id,context_space_id,snapshot_id,token_hash,expires_at) VALUES (%s,%s,%s,%s,clock_timestamp()+interval '1 hour')",(invitation,scope,snapshot,'d'*64))
        c.execute("INSERT INTO guest_challenges(id,invitation_id,code_hash,expires_at) VALUES (%s,%s,%s,clock_timestamp()+interval '1 hour')",(challenge,invitation,'e'*64))
        c.execute("INSERT INTO guest_sessions(id,invitation_id,challenge_id,token_hash,expires_at) VALUES (%s,%s,%s,%s,clock_timestamp()+interval '1 hour')",(session,invitation,challenge,'f'*64))
        document={k:{scope:'synthetic'} for k in ('memberships','primary_domains','space_descriptions','usage')}
        c.execute('INSERT INTO owner_organization VALUES (%s,1,%s)',(repo.subject_id,Jsonb(document)))
    # An old generation must disappear too, while a sibling scope survives.
    other=deepcopy(p['source']);other.update(id=str(uuid4()),source_id=str(uuid4()),context_space_id=p['sibling'])
    sibling=revision(p,'Retain sibling');sibling.update(id=str(uuid4()),item_id=str(uuid4()),context_space_id=p['sibling'],provenance=[other['id']])
    repo.save(sources=[other],revisions=[sibling]);drain(ProjectionWorker(repo,p['projector'],(p['sibling'],)))
    p['worker'].rebuild(scope)
    new=revision(p,'Leased before deletion');repo.save(revisions=[new])
    return p['worker'].claim(),sibling


@pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)
def test_confirmed_erasure_is_resumable_and_leaves_no_scope_data(generic,empty_database,monkeypatch):
    p=generic;repo=p['repo'];owner=repo.subject_id;scope=p['scope']
    deletion=PostgresSpaceDeletion(url=repo.url)
    with pytest.raises(ContextStorageUnavailable):run(deletion.prepare(owner,scope,'Synthetic'))
    command.upgrade(empty_database,'0012_space_deletion')
    assert run(deletion.owner_for(scope))==owner
    assert run(deletion.owner_for(str(uuid4()))) is None
    event,sibling=seed(p)
    before=repo.read_snapshot((p['sibling'],),(sibling['id'],))
    with pytest.raises(ContextSpaceNotFound):run(deletion.prepare(owner,p['foreign'],'Synthetic'))
    with pytest.raises(SpaceConfirmationMismatch):run(deletion.prepare(owner,scope,'synthetic'))
    with repo.connect() as c:assert c.execute('SELECT status FROM context_spaces WHERE id=%s',(scope,)).fetchone()['status']=='active'
    guest=PostgresGuestRepository(url=repo.url)
    assert run(guest.authenticate('f'*64))
    assert not run(deletion.prepare(owner,scope,'Synthetic'))
    assert run(deletion.owner_for(scope))==owner
    assert run(guest.authenticate('f'*64)) is None  # Revoked before graph/SQL cleanup.
    with pytest.raises(ContextStorageUnavailable):
        run(deletion.complete(owner,scope,Mock(side_effect=ConnectionError('offline graph')),Mock()))
    # Normal immutable/cross-scope deletes remain forbidden, even with a forged scope.
    with pytest.raises(psycopg.Error):
        with repo.connect() as c:c.execute('DELETE FROM source_revisions WHERE context_space_id=%s',(scope,))
    with pytest.raises(psycopg.Error):
        with repo.connect() as c:
            c.execute("SELECT set_config('qh.purge_scope',%s,true),set_config('qh.purge_owner',%s,true)",(scope,owner))
            c.execute('DELETE FROM source_revisions WHERE context_space_id=%s',(p['sibling'],))
    original=deletion._purge;reached=[]
    def fail_after_sql(c,who,target):
        original(c,who,target);reached.append(True);raise RuntimeError('lost SQL ack simulation')
    monkeypatch.setattr(deletion,'_purge',fail_after_sql)
    with pytest.raises(ContextStorageUnavailable):
        run(deletion.complete(owner,scope,p['projector'].purge,Mock()))
    assert reached
    with repo.connect() as c:
        assert c.execute('SELECT count(*) n FROM source_documents WHERE context_space_id=%s',(scope,)).fetchone()['n']==1
    monkeypatch.setattr(deletion,'_purge',original)
    runtime=NativeRuntime(url=repo.url,driver=p['projector'].driver,policy=Mock(),namespace=p['projector'].namespace)
    runtime.schema_version='0012_space_deletion';runtime._resume_deletions()
    with repo.connect() as c:
        assert c.execute('SELECT state FROM context_space_deletions WHERE context_space_id=%s',(scope,)).fetchone()['state']=='complete'
        assert c.execute('SELECT count(*) n FROM context_spaces WHERE id=%s',(scope,)).fetchone()['n']==0
        for table in TABLES:assert c.execute(f'SELECT count(*) n FROM {table} WHERE context_space_id=%s',(scope,)).fetchone()['n']==0,table
        for table in ('guest_sessions','guest_challenges'):assert c.execute(f'SELECT count(*) n FROM {table}').fetchone()['n']==0
        document=c.execute('SELECT document FROM owner_organization WHERE owner_id=%s',(owner,)).fetchone()['document']
        assert all(scope not in values for values in document.values())
        assert c.execute('SELECT count(*) n FROM users').fetchone()['n']==2
    assert repo.read_snapshot((p['sibling'],),(sibling['id'],))==before
    apply=Mock(wraps=p['projector'].apply);monkeypatch.setattr(p['projector'],'apply',apply)
    assert not p['worker'].process(event);apply.assert_not_called()
    with p['projector'].driver.session() as graph:
        assert graph.run('MATCH(n) WHERE n.context_id=$scope OR n.slice_id=$key OR n.key=$key OR n.key STARTS WITH $prefix OR n.id=$key RETURN count(n) AS n',
            scope=scope,key=p['projector'].key(scope),prefix=p['projector'].key(scope)+':').single()['n']==0
        assert graph.run('MATCH(n:QH30Revision {context_id:$scope}) RETURN count(n) AS n',scope=p['sibling']).single()['n']>0
    assert run(deletion.prepare(owner,scope,'Synthetic'))  # Durable idempotent receipt.
    assert run(deletion.owner_for(scope))==owner


@pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)
def test_revocation_does_not_wait_for_inflight_graph_and_cleanup_fences_it(generic,empty_database,monkeypatch):
    p=generic;repo=p['repo'];scope=p['scope'];owner=repo.subject_id
    command.upgrade(empty_database,'0012_space_deletion')
    repo.save(sources=[p['source']],revisions=[revision(p,'Concurrent projection')])
    event=p['worker'].claim();entered,release=Event(),Event();original=p['projector'].apply
    def slow_apply(*args):
        entered.set();assert release.wait(10);return original(*args)
    monkeypatch.setattr(p['projector'],'apply',slow_apply)
    deletion=PostgresSpaceDeletion(url=repo.url)
    with ThreadPoolExecutor(max_workers=2) as pool:
        worker=pool.submit(p['worker'].process,event)
        try:
            assert entered.wait(5)
            assert not run(deletion.prepare(owner,scope,'Synthetic'))
            with repo.connect() as c:
                assert c.execute('SELECT status FROM context_spaces WHERE id=%s',(scope,)).fetchone()['status']=='deleting'
            completion=pool.submit(deletion.complete_sync,owner,scope,p['projector'].purge)
            assert not completion.done()
        finally:release.set()
        worker.result(timeout=10);completion.result(timeout=10)
    with p['projector'].driver.session() as graph:
        assert graph.run('MATCH(n) WHERE n.context_id=$scope OR n.key=$key OR n.id=$key RETURN count(n) AS n',
            scope=scope,key=p['projector'].key(scope)).single()['n']==0
