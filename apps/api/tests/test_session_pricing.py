"""No paid API/network: pinned configured prices, fixed authorization and immutable grants."""
import asyncio
from datetime import datetime, timedelta, timezone
import json

import pytest

from adapters.llm.chat_config import ChatConfigurationError
from adapters.llm.session_config import PrivateSessionFactory
from tests.test_chat_sessions import setup, active
from tests.test_chat_service import request
from app.chat.sessions import SessionClosed


def test_fixed_thirty_day_authorization_separate_from_price_age_and_session(tmp_path,monkeypatch):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    path=tmp_path/'auth.json';r=json.loads(path.read_text());now=datetime.now(timezone.utc)
    r.update(activated_at=now.isoformat(),expires_at=(now+timedelta(days=30)).isoformat(),
        pricing_verified_at=(now-timedelta(days=10)).isoformat())
    path.write_text(json.dumps(r))
    factory=PrivateSessionFactory(authorization_path=path,ledger_path=ledger,
        transport=s.factory.transport)
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


def test_pinned_live_snapshot_denies_before_disclosure(tmp_path,monkeypatch):
    s,who,_,_,calls,_,_=setup(tmp_path,monkeypatch)
    s.factory.snapshots[('alice','space')]='0'*64
    with pytest.raises(SessionClosed):asyncio.run(s.preview(who,request()))
    assert not calls


@pytest.mark.parametrize('field,value',[('input_usd_per_million','0.16'),('output_usd_per_million','0.61')])
def test_configured_prices_must_match_pinned_rates(tmp_path,monkeypatch,field,value):
    # Availability no longer depends on scraping a public page: the private receipt
    # pins the rates and any drift from the accounting constants fails closed.
    _,_,_,_,_,ledger,_=setup(tmp_path,monkeypatch)
    path=tmp_path/'auth.json';r=json.loads(path.read_text());r[field]=value;path.write_text(json.dumps(r))
    with pytest.raises(ChatConfigurationError):PrivateSessionFactory(authorization_path=path,ledger_path=ledger)


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
