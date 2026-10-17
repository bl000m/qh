"""Real REST + dedicated SQL/Neo4j, using QH-8 fixture extraction without HTTP LLMs."""

import asyncio
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from adapters.context.incremental import IncrementalContextEngine, ProjectionWorker
from adapters.context.native import AuthorizedNativeContextService
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from app.bootstrap import create_runtime_app
from tests.test_canonical_graph_pipeline import drain
from tests.test_context_query_api import PATH
from tests.test_context_spaces_api import headers
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_runtime import configure, wait_until
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_oidc_security import SETTINGS, build_auth
from tests.test_understanding import CASES
from tests.test_understanding_pipeline import import_extract


def application(p):
    app=create_runtime_app()
    reader=PostgresSecurityReader(url=database_url())
    auth,_=build_auth(resolver=reader.resolve_identity)
    app.state.security=replace(app.state.security,authenticate=auth.authenticate)
    policy=app.state.services.policy
    app.state.services.context.retrieval_for=lambda subject:AuthorizedNativeContextService(
        policy=policy,engine=IncrementalContextEngine(
            CanonicalRepository(url=database_url(),subject_id=subject),p['projector']))
    return app


def request(client,p,*,view='history',text=None,descriptors=None,scopes=None,auth=None,**kwargs):
    body=dict(context_ids=scopes or [p['scope']],view=view,**kwargs)
    body.update(text=text) if text is not None else body.update(descriptors=descriptors or ['decision'])
    return client.post(PATH,headers=auth or headers(),json=body)


@pytest.fixture
def retrieved(generic,monkeypatch):
    p=generic;repo=p['repo']
    monkeypatch.setenv('QH_NATIVE_CONTEXT_ENABLED','false')
    with repo.connect() as c:
        bob=str(c.execute('SELECT owner_id FROM context_spaces WHERE id=%s',(p['foreign'],)).fetchone()['owner_id'])
        for sub,who in [('external-alice',repo.subject_id),('external-bob',bob)]:
            c.execute('INSERT INTO user_identities(issuer,subject,user_id) VALUES (%s,%s,%s)',(SETTINGS.issuer,sub,who))
    usecase,provider,ref,checkpoint=import_extract(p,CASES[0])
    asyncio.run(usecase.publish(subject_id=repo.subject_id,checkpoint=checkpoint))
    p['source']=repo.read_sources((p['scope'],),(ref,))[0]
    original=repo.read_snapshot((p['scope'],))['understanding_item_revisions']
    p['original']=deepcopy(original);p['provider']=provider
    choice=next(r for r in original if {'value':'decision','certainty':'asserted'} in r['content'].get('descriptors',[]))
    p['choice']=choice
    clones=[]
    for number,state in [(2,'confirmed'),(3,'proposed'),(4,'rejected')]:
        row=deepcopy(choice)
        row.update(id=str(uuid4()),revision_no=number,based_on_revision_id=choice['id'],validation_state=state)
        row.pop('created_at');row.pop('current_revision_id')
        if state!='proposed':row.update(validated_by=repo.subject_id,validated_at='2026-10-17T07:00:00Z')
        clones.append(row)
    p['confirmed']=clones[0]
    legacy=revision(p,'legacy')
    legacy.update(type_id='qh.decision',content={'legacy_note':'Readable specialized history',
                  'citations':'Opaque imported bibliography'})
    sibling_source={**p['source'],'id':str(uuid4()),'source_id':str(uuid4()),'context_space_id':p['sibling']}
    sibling=deepcopy(choice)
    sibling.update(id=str(uuid4()),item_id=str(uuid4()),context_space_id=p['sibling'],provenance=[sibling_source['id']])
    sibling['content']={'text':'Sibling pilot','descriptors':[{'value':'decision','certainty':'asserted'}]}
    repo.save(sources=[sibling_source],revisions=[*clones,legacy,sibling])
    timed_source={**p['source'],'id':str(uuid4()),'source_id':str(uuid4()),
        'content':'The trial occurred at 2026-10-01T12:00:00Z and applies from 2026-10-01T12:00:00Z until 2026-10-02T12:00:00Z.'}
    timed=revision(p,'Trial time',descriptors=['reported_timestamp'])
    timed.update(provenance=[timed_source['id']],fact_from='2026-10-01T12:00:00Z',
        fact_to='2026-10-01T12:00:00Z',valid_from='2026-10-01T12:00:00Z',valid_to='2026-10-02T12:00:00Z')
    repo.save(sources=[timed_source],revisions=[timed])
    with repo.connect() as c:c.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s',(clones[0]['id'],choice['item_id']))
    drain(p['worker'])
    drain(ProjectionWorker(repo,p['projector'],(p['sibling'],)))
    try:
        with TestClient(application(p)) as client:yield p,client
    finally:
        # Only this fixture's UUID-database namespace; never the persistent graph.
        with p['projector'].driver.session() as s:
            s.run('MATCH (n) WHERE n.key STARTS WITH $prefix OR n.id STARTS WITH $prefix OR n.slice_id STARTS WITH $prefix DETACH DELETE n',
                  prefix=p['projector'].namespace+':').consume()


def test_qh8_proposals_canonical_content_sources_and_alice_bob_isolation(retrieved):
    p,client=retrieved
    for meaning in ('decision','hypothesis','open_question','reversible_pause'):
        r=request(client,p,view='proposed',descriptors=[meaning])
        assert r.status_code==200,r.text
        rows=r.json()['items'];assert rows and all(row['type_id']=='qh.generic.item' for row in rows)
        assert all(row['validation_state']=='proposed' and not row['is_current_confirmed'] for row in rows)
        assert all(row['provenance'][0]['source_revision_id']==p['source']['id'] for row in rows)
        for row in rows:
            assert row['content']['citations'] and row['content']['extraction']
            expected=p['repo'].read_snapshot((p['scope'],),(row['revision_id'],))['understanding_item_revisions'][0]
            assert row['content']==expected['content'] and row['revision_no']==expected['revision_no']
    assert request(client,p,descriptors=['expected_effect']).json()['items']==[]
    assert len(request(client,p,descriptors=['expected_effect'],include_tentative=True).json()['items'])==1
    assert not request(client,p,descriptors=['Decision']).json()['items']
    assert not request(client,p,descriptors=['absent-descriptor']).json()['items']
    for scopes,auth in [([p['scope']],headers('external-bob')),([p['scope'],p['foreign']],headers())]:
        r=request(client,p,scopes=scopes,auth=auth)
        assert r.status_code==404 and r.json()=={'detail':'Context space not found'}
    multi=request(client,p,scopes=[p['scope'],p['sibling']],text='pilot')
    assert multi.status_code==200,multi.text
    assert {r['context_space_id'] for r in multi.json()['items']}=={p['scope'],p['sibling']}
    assert p['provider'].calls==1  # Offline fixture extraction only; query never generates.


def test_views_pagination_specialized_history_and_immutable_revisions(retrieved):
    p,client=retrieved
    for selector in ({'text':'pilot'},{'descriptors':['decision']}):
        current=request(client,p,view='current',**selector)
        assert current.status_code==200,current.text
        assert [r['revision_id'] for r in current.json()['items']]==[p['confirmed']['id']]
        assert current.json()['items'][0]['is_current_confirmed']
        after=None;rows=[]
        while True:
            page=request(client,p,view='history',limit=1,**selector,**({'after_revision_id':after} if after else {}))
            assert page.status_code==200,page.text
            rows+=page.json()['items'];after=page.json()['next_after_revision_id']
            if after is None:break
        # Text also matches the distinct hypothesis about the pilot; descriptor
        # selection contains only the four decision revisions.
        expected=5 if 'text' in selector else 4
        assert len(rows)==expected and len({r['revision_id'] for r in rows})==expected
        assert {r['validation_state'] for r in rows}=={'confirmed','proposed','rejected'}
        assert [r['revision_id'] for r in rows]==sorted(r['revision_id'] for r in rows)
    legacy=request(client,p,text='specialized')
    assert legacy.status_code==200 and legacy.json()['items'][0]['type_id']=='qh.decision'
    assert legacy.json()['items'][0]['content']=={'legacy_note':'Readable specialized history',
                                                'citations':'Opaque imported bibliography'}
    for old in p['original']:
        row=p['repo'].read_snapshot((p['scope'],),(old['id'],))['understanding_item_revisions'][0]
        assert {k:v for k,v in row.items() if k!='current_revision_id'}=={k:v for k,v in old.items() if k!='current_revision_id'}
    assert request(client,p,view='current',descriptors=['hypothesis']).json()['items']==[]


def test_relations_temporal_bounds_and_direct_id_bypass(retrieved):
    p,client=retrieved
    r=request(client,p,descriptors=['stated_by'])
    assert r.status_code==200,r.text
    relation=r.json()['items'][0]
    assert relation['structural_kind']=='relation' and relation['relation']['predicate']=='stated_by'
    assert relation['relation']['source_item_id']==p['choice']['item_id']
    assert relation['relation']['source_revision_id']==p['choice']['id']
    target=p['repo'].read_snapshot((p['scope'],),(relation['relation']['target_revision_id'],))['understanding_item_revisions'][0]
    assert target['structural_kind']=='entity' and not target['content'].get('descriptors')
    assert relation['temporal']==dict.fromkeys(('fact_from','fact_to','valid_from','valid_to'))
    timed=request(client,p,descriptors=['reported_timestamp'])
    assert timed.status_code==200,timed.text
    assert timed.json()['items'][0]['temporal']==dict(fact_from='2026-10-01T12:00:00+00:00',
        fact_to='2026-10-01T12:00:00+00:00',valid_from='2026-10-01T12:00:00+00:00',valid_to='2026-10-02T12:00:00+00:00')
    assert request(client,p,scopes=[p['foreign']],auth=headers('external-bob'),
                   after_revision_id=p['choice']['id']).json()['items']==[]
    for field in ('source_revision_id','revision_id'):
        body=dict(context_ids=[p['scope']],view='history',text='pilot',**{field:p['source']['id']})
        assert client.post(PATH,headers=headers('external-bob'),json=body).status_code==422


def test_visibility_is_applied_before_page_limit(retrieved):
    p,client=retrieved
    # This matching proposal sorts before every other UUID. A filter applied
    # after LIMIT 1 would hide the real confirmed current revision.
    proposal=deepcopy(p['choice'])
    proposal.update(id='00000000-0000-0000-0000-000000000000',item_id=str(uuid4()))
    p['repo'].save(revisions=[proposal])
    drain(p['worker'])
    for selector in ({'text':'pilot'},{'descriptors':['decision']}):
        current=request(client,p,view='current',limit=1,**selector)
        assert current.status_code==200,current.text
        assert [r['revision_id'] for r in current.json()['items']]==[p['confirmed']['id']]
        assert current.json()['next_after_revision_id'] is None
        history=request(client,p,view='history',limit=1,**selector)
        assert history.json()['items'][0]['revision_id']==proposal['id']


@pytest.mark.parametrize('corruption',['marker','text','evidence','endpoint','missing'])
def test_graph_corruption_fails_closed(retrieved,corruption):
    p,client=retrieved
    key=p['projector'].key(p['scope'])
    with p['projector'].driver.session() as s:
        if corruption=='marker':s.run('MATCH (m:QH30Sync {key:$key}) SET m.version=m.version+1',key=key).consume()
        else:
            relation=next(r for r in p['original'] if r['structural_kind']=='relation')
            if corruption=='text':q='MATCH (r:QH30Revision {slice_id:$key,revision_id:$id}) SET r.text="corrupted"'
            elif corruption=='evidence':q='MATCH (r:QH30Revision {slice_id:$key,revision_id:$id})-[e:EVIDENCED_BY]->() DELETE e'
            elif corruption=='endpoint':q='MATCH (r:QH30Revision {slice_id:$key,revision_id:$id})-[e:OBJECT]->() DELETE e'
            else:q='MATCH (r:QH30Revision {slice_id:$key,revision_id:$id}) DETACH DELETE r'
            s.run(q,key=key,id=relation['id']).consume()
    r=request(client,p,descriptors=['stated_by'])
    assert r.status_code==503 and r.json()=={'detail':'Context service unavailable'}
    assert not request(client,p,descriptors=['not-present']).json().get('items')


def test_pending_failed_recovery_rebuild_and_reopen(retrieved,monkeypatch):
    p,client=retrieved
    row=revision(p,'Recovery',descriptors=['new_recovery_meaning'])
    p['repo'].save(revisions=[row])
    for descriptor in ('new_recovery_meaning','no-match'):
        assert request(client,p,descriptors=[descriptor]).status_code==503
    apply=p['projector'].apply
    def fail(*args):raise ConnectionError('synthetic-private-projection-error')
    monkeypatch.setattr(p['projector'],'apply',fail)
    p['worker'].run_once()
    assert p['repo'].sync_status((p['scope'],))[0]['sync_state']=='failed'
    assert request(client,p,descriptors=['no-match']).status_code==503
    monkeypatch.setattr(p['projector'],'apply',apply)
    p['worker'].rebuild(p['scope'])
    assert request(client,p,descriptors=['new_recovery_meaning']).status_code==200
    before=request(client,p,text='Recovery').json()['items']
    # New app and real native worker lifecycle, same canonical/source IDs, no extraction.
    configure(monkeypatch,p['projector'].namespace)
    for _ in range(2):
        app=create_runtime_app()
        auth,_=build_auth(resolver=PostgresSecurityReader(url=database_url()).resolve_identity)
        app.state.security=replace(app.state.security,authenticate=auth.authenticate)
        with TestClient(app) as reopened:
            runtime=app.state.native_context
            wait_until(lambda:p['repo'].sync_status((p['scope'],))[0]['sync_state']=='ready')
            assert request(reopened,p,text='Recovery').json()['items']==before
            assert runtime.thread.is_alive()
