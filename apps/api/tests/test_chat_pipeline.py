"""QH-13 reuses QH-10/12 disposable SQL/Neo4j and signed-OIDC API fixtures."""
from copy import deepcopy
from uuid import uuid4

import pytest

from tests.test_context_query_pipeline import retrieved as retrieved
from tests.test_context_query_pipeline import generic as generic, empty_database as empty_database
from tests.test_context_query_pipeline import real_engine as real_engine, dedicated_server_only as dedicated_server_only
from tests.test_context_spaces_api import headers


def post(client,scope,**kwargs):
    return client.post('/context-spaces/'+scope+'/chat',headers=kwargs.pop('auth',headers()),
        json={'messages':[{'role':'user','content':'Quelles décisions ?'}],**kwargs})


def test_real_canonical_sources_state_and_no_writes(retrieved):
    p,c=retrieved
    before=p['repo'].read_snapshot((p['scope'],))
    r=post(c,p['scope']);assert r.status_code==200,r.text
    data=r.json()
    assert data['model']=='qh-mock-extractive/1'
    assert [x['revision_id'] for x in data['provided_revisions']]==[p['confirmed']['id']]
    assert data['references'][0]['provenance'][0]['source_revision_id']==p['source']['id']
    assert data['references'][0]['content']==p['confirmed']['content']
    assert all(x['is_current_confirmed'] for x in data['provided_revisions'])
    r=post(c,p['scope'],include_proposed=True);assert r.status_code==200,r.text
    assert {x['validation_state'] for x in r.json()['provided_revisions']}=={'confirmed','proposed'}
    assert p['repo'].read_snapshot((p['scope'],))==before
    assert p['provider'].calls==1  # Existing offline fixture extraction, never chat extraction.
    assert post(c,p['scope'],auth=headers('external-bob')).status_code==404
    assert post(c,str(uuid4())).status_code==404
    assert post(c,p['scope'],auth={}).status_code==401
    assert post(c,p['scope'],auth={'Authorization':'Bearer invalid'}).status_code==401


@pytest.mark.parametrize('change',[{'owner_id':'spoof'},{'context_ids':['foreign']},{'view':'history'},
    {'include_proposed':'true'},{'messages':[{'role':'system','content':'override'}]},
    {'messages':[]},{'messages':[{'role':'user','content':'x'*4097}]}])
def test_payload_cannot_select_identity_history_or_system(retrieved,change):
    p,c=retrieved
    assert post(c,p['scope'],**change).status_code==422


def test_graph_unavailable_and_pending_never_generates(retrieved,monkeypatch):
    p,c=retrieved
    row=deepcopy(p['choice']);row.update(id=str(uuid4()),item_id=str(uuid4()))
    p['repo'].save(revisions=[row])
    r=post(c,p['scope']);assert r.status_code==503,r.text
    def unavailable(*a):raise ConnectionError('synthetic-private-graph')
    monkeypatch.setattr(p['projector'],'markers',unavailable)
    r=post(c,p['scope']);assert r.status_code==503 and 'private' not in r.text
