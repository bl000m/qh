"""QH-12 navigation uses the same real isolated SQL/graph/OIDC-signed fixtures."""
from copy import deepcopy
from uuid import uuid4

import pytest

from tests.test_context_query_pipeline import retrieved as retrieved
from tests.test_context_query_pipeline import (
    generic as generic, empty_database as empty_database,
    real_engine as real_engine, dedicated_server_only as dedicated_server_only,
)
from tests.test_context_query_api import query_api as query_api
from tests.test_canonical_graph_pipeline import drain
from tests.test_context_spaces_api import headers, api as api


def browse(client,scope,**params):
    auth=params.pop('auth',None)
    return client.get('/context-spaces/'+scope+'/understanding',params={'view':'history',**params},headers=headers() if auth is None else auth)


def test_browse_all_views_pages_and_exact_history(retrieved):
    p,c=retrieved
    early=deepcopy(p['choice']);early.update(id='00000000-0000-0000-0000-000000000000',item_id=str(uuid4()))
    p['repo'].save(revisions=[early]);drain(p['worker'])
    for view in ('current','proposed','history'):
        cursor=None;rows=[]
        while True:
            r=browse(c,p['scope'],view=view,limit=2,**({'after_revision_id':cursor} if cursor else {}))
            assert r.status_code==200,r.text
            page=r.json();rows+=page['items'];cursor=page['next_after_revision_id']
            if not cursor:break
        expected=p['repo'].read_snapshot((p['scope'],))['understanding_item_revisions']
        if view=='current':expected=[x for x in expected if x['id']==x['current_revision_id'] and x['validation_state']=='confirmed']
        if view=='proposed':expected=[x for x in expected if x['validation_state']=='proposed']
        assert [x['revision_id'] for x in rows]==sorted(x['id'] for x in expected)
        assert len(rows)==len({x['revision_id'] for x in rows})
    history=browse(c,p['scope'],item_id=p['choice']['item_id']).json()['items']
    assert len(history)==4 and {x['validation_state'] for x in history}=={'confirmed','proposed','rejected'}
    assert browse(c,p['scope'],revision_id=p['choice']['id']).json()['items'][0]['revision_id']==p['choice']['id']
    assert browse(c,p['scope'],revision_id=str(uuid4())).json()['items']==[]


def test_navigation_filters_open_descriptors_entities_relations_and_no_write(retrieved):
    p,c=retrieved
    assert not browse(c,p['scope'],descriptor='expected_effect').json()['items']
    assert len(browse(c,p['scope'],descriptor='expected_effect',include_tentative=True).json()['items'])==1
    assert not browse(c,p['scope'],descriptor='Decision').json()['items']
    for kind in ('entity','relation'):
        rows=browse(c,p['scope'],kind=kind,limit=1).json()['items'];assert rows and all(r['structural_kind']==kind for r in rows)
    unclassified=browse(c,p['scope'],unclassified=True).json()['items']
    assert unclassified and all(not x['content'].get('descriptors') for x in unclassified)
    relation=browse(c,p['scope'],kind='relation').json()['items'][0]
    linked=browse(c,p['scope'],related_item_id=relation['relation']['source_item_id']).json()['items']
    assert relation['revision_id'] in {x['revision_id'] for x in linked}
    endpoint=browse(c,p['scope'],revision_id=relation['relation']['target_revision_id']).json()['items'][0]
    assert endpoint['structural_kind']=='entity'
    assert relation['provenance'][0]['source_revision_id']==p['source']['id']
    assert relation['content']['citations'] and p['provider'].calls==1


@pytest.mark.parametrize('params',[{'view':'latest'},{'limit':0},{'limit':101},{'after_revision_id':'bad'},
    {'descriptor':''},{'descriptor':'x','unclassified':True},{'include_tentative':True},
    {'owner_id':'spoof'},{'text':''},{'kind':'decision'},{'item_id':'bad'}])
def test_invalid_navigation(query_api,params):
    c,_,scope,_,calls=query_api;assert browse(c,scope,**params).status_code==422
    assert not calls


def test_browse_missing_view_auth_and_uniform_scope_denial(query_api):
    c,_,scope,_,calls=query_api;path='/context-spaces/'+scope+'/understanding'
    assert c.get(path,headers=headers()).status_code==422
    for auth in ({},{'X-User-ID':'alice'},{'Authorization':'Bearer invalid'}):
        assert browse(c,scope,auth=auth).status_code==401
    for id,auth in ((scope,headers('external-bob')),(str(uuid4()),headers())):
        r=browse(c,id,auth=auth);assert r.status_code==404 and r.json()=={'detail':'Context space not found'}
    assert c.get(path+'?view=history&view=proposed',headers=headers()).status_code==422
    assert browse(c,scope,auth=headers('external-bob'),revision_id=str(uuid4())).status_code==404
    assert not calls


@pytest.mark.parametrize('fault',['missing','marker','pending','empty_pending'])
def test_browse_fails_closed_even_for_empty_filters(retrieved,fault):
    p,c=retrieved
    if fault in ('pending','empty_pending'):
        row=deepcopy(p['choice']);row.update(id=str(uuid4()),item_id=str(uuid4()))
        p['repo'].save(revisions=[row])
    else:
        with p['projector'].driver.session() as s:
            if fault=='marker':s.run('MATCH (m:QH30Sync {key:$key}) SET m.version=m.version+1',key=p['projector'].key(p['scope'])).consume()
            else:s.run('MATCH (r:QH30Revision {slice_id:$key,revision_id:$id}) DETACH DELETE r',key=p['projector'].key(p['scope']),id=p['choice']['id']).consume()
    params={'descriptor':'nonexistent'} if fault=='empty_pending' else {}
    r=browse(c,p['scope'],**params);assert r.status_code==503 and r.json()=={'detail':'Context service unavailable'}


def test_policy_is_rechecked_before_disclosure_and_on_next_page(query_api):
    from dataclasses import replace
    from app.core.models import ContextResult
    c,repo,scope,_,calls=query_api
    class Backend:
        async def browse(self,request):
            calls.append(request)
            return ContextResult(hits=())
    service=c.app.state.services.context
    service.retrieval_for=lambda subject:Backend()
    assert browse(c,scope).status_code==200
    repo.rows[scope]=replace(repo.rows[scope],owner_id='revoked')
    assert browse(c,scope,after_revision_id=str(uuid4())).status_code==404
    assert len(calls)==1


@pytest.mark.parametrize('empty',[False,True])
def test_browse_changed_during_hydration_fails_closed(monkeypatch,empty):
    import asyncio
    from adapters.context.incremental import IncrementalContextEngine
    from adapters.context.native import NativeContextEngine
    from app.core.models import ContextBrowse,ContextResult,ContextSearchHit,ItemRevisionRef,ContextRetrievalUnavailable
    from tests.test_context_query_guards import case
    repo,row,_=case();repo.browse_candidates=lambda query: [] if empty else [{'id':row['id']}]
    engine=IncrementalContextEngine(repo,type('Projector',(),{'driver':None,'key':lambda self,scope:scope})())
    engine._ready=lambda scopes:{(scopes[0],'epoch',repo.version)}
    hit=ContextSearchHit(id='test',context_id=row['context_space_id'],excerpt='Cedar',provenance=(),item_revision=ItemRevisionRef(context_id=row['context_space_id'],item_id=row['item_id'],revision_id=row['id']))
    async def selected(*args,**kwargs):return ContextResult(hits=(hit,))
    monkeypatch.setattr(NativeContextEngine,'select_revisions',selected)
    repo.advance=True
    with pytest.raises(ContextRetrievalUnavailable):
        asyncio.run(engine.browse(ContextBrowse(context_id=row['context_space_id'],view='history')))


def test_empty_owned_space_still_uses_graph_readiness(retrieved,monkeypatch):
    p,c=retrieved
    r=browse(c,p['foreign'],auth=headers('external-bob'))
    assert r.status_code==200 and not r.json()['items']
    def outage(*args):raise ConnectionError('synthetic-private-driver-detail')
    monkeypatch.setattr(p['projector'],'markers',outage)
    r=browse(c,p['foreign'],auth=headers('external-bob'))
    assert r.status_code==503 and 'synthetic-private' not in r.text
