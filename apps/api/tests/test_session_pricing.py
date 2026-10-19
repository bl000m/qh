"""No paid API/network: fixed official source, bounded cache and immutable grants."""
import asyncio
from datetime import datetime, timedelta, timezone
import json

import httpx
import pytest

from adapters.llm.chat_config import ChatConfigurationError
from adapters.llm.pricing import OfficialPricing, parse_prices, PRICE_URL
from adapters.llm.session_config import PrivateSessionFactory
from tests.test_chat_sessions import setup, price_html, active
from tests.test_chat_service import request
from app.chat.sessions import SessionClosed


@pytest.mark.parametrize('html', [price_html('0.16'), price_html(outgoing='0.61'),
    price_html().replace('mistral-small-2603','other-model'), 'missing prices',
    price_html().replace('false}', 'true}'), price_html().replace('/M Tokens','/K Tokens'),
    price_html().replace('0.15','null')])
def test_unrecognized_or_increased_price_fails_closed(html):
    with pytest.raises((ValueError,TypeError,KeyError)):parse_prices(html)


def test_public_price_fetch_has_no_credentials_and_refresh_never_renews_budget():
    now=[100000.0];calls=[];response=[price_html()]
    def handler(r):
        assert str(r.url)==PRICE_URL and r.method=='GET'
        assert 'authorization' not in r.headers and not r.content
        calls.append(r)
        return httpx.Response(200,text=response[0],headers={'content-type':'text/html'})
    price=OfficialPricing(transport=httpx.MockTransport(handler),clock=lambda:now[0])
    async def run():
        assert await price.verify();assert await price.verify();assert len(calls)==1
        now[0]+=86401;response[0]=price_html('0.20')
        assert not await price.verify() and price.receipt is None
        assert not await price.verify();assert len(calls)==2  # No automatic retries.
        now[0]+=61;response[0]=price_html('0.10','0.50')
        assert await price.verify();assert price.receipt['input_usd_per_million']=='0.1'
    asyncio.run(run())


@pytest.mark.parametrize('mode',['redirect','http','timeout','oversize','wrong-content'])
def test_price_endpoint_failures_never_use_stale_prices(mode):
    def handler(r):
        if mode=='timeout':raise httpx.ReadTimeout('unavailable',request=r)
        return httpx.Response(302 if mode=='redirect' else 503 if mode=='http' else 200,
            text='x'*2_000_001 if mode=='oversize' else price_html(),
            headers={'content-type':'text/plain' if mode=='wrong-content' else 'text/html','location':'https://untrusted.example'})
    p=OfficialPricing(transport=httpx.MockTransport(handler))
    assert asyncio.run(p.verify()) is False and p.receipt is None


def test_fixed_thirty_day_authorization_separate_from_price_age_and_session(tmp_path,monkeypatch):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    path=tmp_path/'auth.json';r=json.loads(path.read_text());now=datetime.now(timezone.utc)
    r.update(activated_at=now.isoformat(),expires_at=(now+timedelta(days=30)).isoformat(),
        pricing_verified_at=(now-timedelta(days=10)).isoformat())
    path.write_text(json.dumps(r))
    factory=PrivateSessionFactory(authorization_path=path,ledger_path=ledger,
        transport=s.factory.transport,pricing=s.factory.pricing)
    s.factory=factory
    original=ledger.read_bytes()
    async def run():
        assert (await s.capabilities(request()))['enabled']
        grant=await active(s,who)
        assert grant['expires_at']==who.expires_at
        await s.revoke(who,request(),grant['session_id'])
        assert len(json.loads(ledger.read_text())['calls'])==0
        r['owner_authorized']=False;path.write_text(json.dumps(r))
        assert not (await s.capabilities(request()))['enabled']
    asyncio.run(run());assert not calls
    assert json.loads(original)==json.loads(ledger.read_text())
    r['owner_authorized']=True;r['expires_at']=(now+timedelta(days=30,seconds=1)).isoformat();path.write_text(json.dumps(r))
    with pytest.raises(ChatConfigurationError):PrivateSessionFactory(authorization_path=path,ledger_path=ledger)


def test_pinned_live_snapshot_and_price_failure_deny_before_disclosure(tmp_path,monkeypatch):
    s,who,_,_,calls,_,_=setup(tmp_path,monkeypatch)
    s.factory.snapshots[('alice','space')]='0'*64
    async def run():
        with pytest.raises(SessionClosed):await s.preview(who,request())
        s.factory.snapshots[('alice','space')]=None
        p=await active(s,who)
        s.factory.pricing=OfficialPricing(transport=httpx.MockTransport(lambda r:httpx.Response(503)))
        with pytest.raises(SessionClosed):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls


@pytest.mark.parametrize('limits',[{'max_session_calls':4},{'max_session_usd':'0.02'}])
def test_new_authorization_cannot_raise_approved_session_limits(tmp_path,monkeypatch,limits):
    with pytest.raises(ChatConfigurationError):setup(tmp_path,monkeypatch,**limits)


def test_expired_availability_at_restart_keeps_mock_and_never_resets_ledger(tmp_path,monkeypatch):
    from adapters.llm.session_config import configured_session_factory
    _,_,_,_,_,ledger,_=setup(tmp_path,monkeypatch)
    path=tmp_path/'auth.json';r=json.loads(path.read_text())
    r['expires_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat();path.write_text(json.dumps(r))
    before=ledger.read_bytes()
    monkeypatch.setenv('QH_CHAT_SESSIONS_ENABLED','true')
    monkeypatch.setenv('QH_CHAT_SESSION_AUTHORIZATION_FILE',str(path))
    monkeypatch.setenv('QH_CHAT_SESSION_LEDGER_FILE',str(ledger))
    assert configured_session_factory() is None and ledger.read_bytes()==before
