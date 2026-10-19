"""Reuse existing disposable SQL/Neo4j/signed-OIDC pipeline, no canonical writes."""
from dataclasses import replace
import json
import time

from tests.test_context_query_pipeline import retrieved as retrieved
from tests.test_context_query_pipeline import generic as generic, empty_database as empty_database
from tests.test_context_query_pipeline import real_engine as real_engine, dedicated_server_only as dedicated_server_only
from tests.test_chat_sessions import setup
from tests.test_context_spaces_api import headers
from tests.test_oidc_security import build_auth
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.config import database_url


def test_canonical_sessions_aliases_provenance_and_zero_writes(retrieved,tmp_path,monkeypatch):
    p,c=retrieved
    sessions,_,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    sessions.chat=c.app.state.services.chat
    sessions.clock=time.time
    sessions.factory.scopes=frozenset([(str(p['repo'].subject_id),p['scope'])])
    c.app.state.services=replace(c.app.state.services,chat_sessions=sessions)
    auth,_=build_auth(resolver=PostgresSecurityReader(url=database_url()).resolve_identity)
    c.app.state.security=replace(c.app.state.security,authenticate_with_expiry=auth.authenticate_with_expiry)
    before=p['repo'].read_snapshot((p['scope'],))
    base='/context-spaces/'+p['scope']+'/chat-sessions'
    alice=headers();bob=headers('external-bob')
    data={'messages':[{'role':'user','content':'Di che cosa parla questo Context Space?'}],'include_proposed':True}
    preview=c.post(base+'/preview',headers=alice,json=data)
    assert preview.status_code==200,preview.text
    v=preview.json();path=base+'/'+v['session_id'];assert not calls
    assert c.post(path+'/consent',headers=alice,json=dict(snapshot_sha256=v['snapshot_sha256'],disclosure_consent=True)).status_code==200
    r=c.post(path+'/messages',headers=alice,json=data)
    assert r.status_code==200,r.text
    result=r.json();assert {r['validation_state'] for r in result['provided_revisions']}=={'confirmed','proposed'}
    assert result['references'][0] in result['provided_revisions']
    assert result['references'][0]['provenance']
    for verb,tail,body in [('get','',None),('post','/messages',data),('delete','',None)]:
        assert c.request(verb,path+tail,headers=bob,json=body).status_code==404
    assert c.delete(path,headers=alice).status_code==200
    assert c.post(path+'/messages',headers=alice,json=data).status_code==409
    assert len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1
    assert p['repo'].read_snapshot((p['scope'],))==before
