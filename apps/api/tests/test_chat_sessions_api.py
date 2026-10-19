import asyncio
from dataclasses import replace
import json
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from tests.test_chat_sessions import setup
from tests.test_context_spaces_api import headers
from tests.test_oidc_security import build_auth, token


@pytest.fixture
def api(tmp_path,monkeypatch):
    sessions,who,context,_,calls,ledger,clock=setup(tmp_path,monkeypatch)
    scope=str(uuid4())
    context.values=[replace(context.values[0],context_space_id=scope)]
    async def lookup(id):return 'alice' if id==scope else None
    policy=OwnerPolicyService(owner_for=lookup);sessions.chat.policy=policy
    sessions.factory.scopes=frozenset([('alice',scope)])
    auth,_=build_auth(mapping={'external-alice':'alice','external-bob':'bob'})
    app=create_app(services=ApplicationServices(context=context,policy=policy,chat=sessions.chat,chat_sessions=sessions),
        security=SecurityBindings(authenticate=auth.authenticate,policy=policy,authenticate_with_expiry=auth.authenticate_with_expiry))
    with TestClient(app) as client:yield client,scope,sessions,calls,ledger,clock


def test_signed_oidc_api_preview_consent_state_generate_revoke_and_no_bob_disclosure(api):
    c,scope,s,calls,ledger,clock=api;base='/context-spaces/'+scope+'/chat-sessions'
    auth=headers();data={'messages':[{'role':'user','content':'Di che cosa parla?'}]}
    assert c.get(base,headers=auth).json()['enabled']
    p=c.post(base+'/preview',headers=auth,json=data)
    assert p.status_code==200 and p.headers['cache-control']=='private, no-store'
    v=p.json();path=base+'/'+v['session_id'];assert v['expires_at']<=clock[0]+300
    assert not calls
    for foreign,expected in [(headers('external-bob'),404),({},401),({'Authorization':'Bearer invalid'},401)]:
        for method,tail,payload in [('get','',None),('post','/consent',{'snapshot_sha256':v['snapshot_sha256'],'disclosure_consent':True}),('post','/messages',data),('delete','',None)]:
            r=c.request(method,path+tail,headers=foreign,json=payload)
            assert r.status_code==expected
            if expected==401:assert r.headers['www-authenticate']=='Bearer'
    assert not calls
    assert c.post(path+'/messages',headers=auth,json=data).status_code==409
    assert c.post(path+'/consent',headers=auth,json={'snapshot_sha256':v['snapshot_sha256'],'disclosure_consent':False}).status_code==422
    assert c.post(path+'/consent',headers=auth,json={'snapshot_sha256':v['snapshot_sha256'],'disclosure_consent':True}).status_code==200
    assert not calls
    r=c.post(path+'/messages',headers=auth,json=data);assert r.status_code==200,r.text
    assert r.json()['model']=='mistral-small-2603' and len(r.json()['references'])==1
    assert c.get(path,headers=auth).json()['accounting']['calls']==1
    assert c.delete(path,headers=auth).json()['state']=='revoked'
    assert c.post(path+'/messages',headers=auth,json=data).status_code==409
    assert len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1


@pytest.mark.parametrize('extra',[{'owner_id':'bob'},{'model':'another'},{'max_usd':'100'},{'include_proposed':'true'},{'view':'history'}])
def test_server_owns_identity_model_budgets_visibility(api,extra):
    c,scope,_,calls,_,_=api
    r=c.post('/context-spaces/'+scope+'/chat-sessions/preview',headers=headers(),json={'messages':[{'role':'user','content':'x'}],**extra})
    assert r.status_code==422 and not calls


def test_invalid_token_duplicate_headers_query_and_unknown_scopes(api):
    c,scope,s,calls,_,_=api;base='/context-spaces/'+scope+'/chat-sessions'
    assert c.get(base+'?owner=alice',headers=headers()).status_code==422
    assert c.get('/context-spaces/'+str(uuid4())+'/chat-sessions',headers=headers()).status_code==404
    assert c.post(base+'/preview',json={'messages':[{'role':'user','content':'x'}]},headers={'Authorization':'Bearer '+token(exp=1)}).status_code==401
    r=c.get(base,headers=[('Authorization',headers()['Authorization']),('Authorization',headers('external-bob')['Authorization'])]);assert r.status_code==401
    assert not calls


def test_disabled_real_sessions_never_fall_back_or_call_provider(api):
    c,scope,s,calls,_,_=api;s.factory=None;base='/context-spaces/'+scope+'/chat-sessions'
    assert c.get(base,headers=headers()).json()['enabled'] is False
    assert c.post(base+'/preview',headers=headers(),json={'messages':[{'role':'user','content':'x'}]}).status_code==409
    # Existing mock endpoint still works, not an automatic real-provider fallback.
    assert c.post('/context-spaces/'+scope+'/chat',headers=headers(),json={'messages':[{'role':'user','content':'x'}]}).status_code==200
    assert not calls


def test_verified_expiry_is_exposed_without_altering_identity_contract():
    auth,_=build_auth()
    from tests.test_oidc_security import QH_ALICE
    expiry=__import__('time').time()+50
    subject,expires=asyncio.run(auth.authenticate_with_expiry(token(exp=int(expiry))))
    assert subject==QH_ALICE and expires==int(expiry)
    assert asyncio.run(auth.authenticate(token()))==QH_ALICE
