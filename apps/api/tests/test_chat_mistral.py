import asyncio
from datetime import datetime, timedelta, timezone
import json

import httpx
import pytest

from adapters.llm.chat_config import configured_chat_provider, ScopedMistralChatProvider, ChatConfigurationError
from adapters.llm.mistral import ExperimentBudget, MODEL
from app.core.ports import LLMProvider
from tests.test_chat_context import built, revision
from app.chat.context import decode_answer


def setup(tmp_path, monkeypatch, **changes):
    monkeypatch.setenv('MISTRAL_API_KEY','synthetic-chat-private-key')
    now=datetime.now(timezone.utc)
    data=dict(purpose='QH-13 contextual chat',model=MODEL,owner_authorized=True,context_ids=['space'],
        expires_at=(now+timedelta(hours=1)).isoformat(),pricing_verified_at=now.isoformat(),
        eur_per_usd_upper_bound='2',input_usd_per_million='0.15',output_usd_per_million='0.60') | changes
    auth=tmp_path/'authorization.json';auth.write_text(json.dumps(data));auth.chmod(0o600)
    ledger=tmp_path/'chat-ledger.json';ExperimentBudget(ledger,create=True)
    state=json.loads(ledger.read_text());state['purpose']='QH-13 contextual chat';ledger.write_text(json.dumps(state))
    return auth,ledger


def test_default_mock_even_when_a_key_exists(monkeypatch):
    monkeypatch.setenv('MISTRAL_API_KEY','synthetic-chat-private-key')
    monkeypatch.delenv('QH_CHAT_PROVIDER',raising=False)
    provider,model=configured_chat_provider()
    assert isinstance(provider,LLMProvider) and model=='qh-mock-extractive/1'


def test_concrete_adapter_reuses_port_and_http_mock_only(tmp_path,monkeypatch):
    auth,ledger=setup(tmp_path,monkeypatch)
    seen=[]
    def handler(req):
        seen.append(req)
        p=json.loads(req.content)
        assert json.loads(p['messages'][1]['content'])['allowed_reference_aliases']=={'R1':'revision'}
        assert p['model']==MODEL and p['max_tokens']==1000 and p['response_format']==dict(type='json_schema',json_schema=dict(name='qh_atomic_understanding',schema=context.request.output_schema,strict=True))
        return httpx.Response(200,json=dict(model=MODEL,usage=dict(prompt_tokens=100,completion_tokens=30),
            choices=[dict(finish_reason='stop',message=dict(content='{"answer":"ok","reference_aliases":["R1"],"insufficient_context":false,"support_basis":"canonical"}'))]))
    provider=ScopedMistralChatProvider(authorization_path=auth,ledger_path=ledger,transport=httpx.MockTransport(handler))
    assert isinstance(provider,LLMProvider)
    context=built((revision(),))
    result=asyncio.run(provider.generate(context.request))
    assert decode_answer(result.message,context)[1]==(revision(),)
    assert '"ok"' in result.message.content and len(seen)==1
    state=json.loads(ledger.read_text())
    assert state['calls'][0]['usage']==dict(prompt_tokens=100,completion_tokens=30)
    assert 'synthetic-chat-private-key' not in ledger.read_text()
    assert provider.provider.last_exchange is None


def test_429_is_counted_without_retry_and_never_blocks_the_next_call(tmp_path,monkeypatch):
    auth,ledger=setup(tmp_path,monkeypatch);seen=[]
    def handler(req):seen.append(req);return httpx.Response(429,headers={'Retry-After':'42'},json={'message':'synthetic-chat-private-key'})
    provider=ScopedMistralChatProvider(authorization_path=auth,ledger_path=ledger,transport=httpx.MockTransport(handler))
    for _ in range(2):
        with pytest.raises(Exception):asyncio.run(provider.generate(built((revision(),)).request))
    # Each explicit request makes exactly one HTTP attempt; a rate limit blocks nothing.
    assert len(seen)==2
    state=json.loads(ledger.read_text());assert not state['blocked'] and [c['status'] for c in state['calls']]==['failed','failed']


@pytest.mark.parametrize('changes',[{'owner_authorized':False},{'context_ids':[]},
    {'eur_per_usd_upper_bound':'NaN'},{'eur_per_usd_upper_bound':'26'},
    {'input_usd_per_million':'0.99'},{'model':'another-model'}])
def test_invalid_authorization_never_reaches_http(tmp_path,monkeypatch,changes):
    auth,ledger=setup(tmp_path,monkeypatch,**changes)
    with pytest.raises(ChatConfigurationError):ScopedMistralChatProvider(authorization_path=auth,ledger_path=ledger)
    assert not json.loads(ledger.read_text())['calls']


def test_unapproved_scope_does_not_reserve(tmp_path,monkeypatch):
    auth,ledger=setup(tmp_path,monkeypatch,context_ids=['other'])
    provider=ScopedMistralChatProvider(authorization_path=auth,ledger_path=ledger)
    with pytest.raises(ChatConfigurationError):asyncio.run(provider.generate(built((revision(),)).request))
    assert not json.loads(ledger.read_text())['calls']


def test_unmarked_extraction_ledger_is_rejected_without_modifying_it(tmp_path,monkeypatch):
    auth,ledger=setup(tmp_path,monkeypatch)
    data=json.loads(ledger.read_text());data.pop('purpose');ledger.write_text(json.dumps(data))
    original=ledger.read_bytes()
    with pytest.raises(ChatConfigurationError):ScopedMistralChatProvider(authorization_path=auth,ledger_path=ledger)
    assert ledger.read_bytes()==original


@pytest.mark.parametrize('bad_reference', [False, True])
def test_detailed_six_day_answer_uses_strict_root_schema_and_exact_provenance(tmp_path, monkeypatch, bad_reference):
    from app.chat.context import ChatProviderUnavailable
    auth, ledger = setup(tmp_path, monkeypatch)
    context = built((revision(),), extended_dialogue=True)
    planning = '\n\n'.join(f'### Jour {i}\n- Matin : préparation.\n- Après-midi : exercice pratique.' for i in range(1, 7))
    seen = []
    def handler(request):
        wire = json.loads(request.content); seen.append(wire)
        schema = wire['response_format']['json_schema']
        assert schema['strict'] and schema['schema']['additionalProperties'] is False
        fields = schema['schema']['properties']
        assert fields['answer']['type'] == 'string' and fields['reference_aliases']['items']['enum'] == ['R1']
        return httpx.Response(200, json=dict(model=MODEL, usage=dict(prompt_tokens=100, completion_tokens=300),
            choices=[dict(finish_reason='stop', message=dict(content=json.dumps(dict(answer=planning,
                reference_aliases=['OUTSIDE' if bad_reference else 'R1'], insufficient_context=False, support_basis='canonical'))))]))
    provider = ScopedMistralChatProvider(authorization_path=auth, ledger_path=ledger, transport=httpx.MockTransport(handler))
    result = asyncio.run(provider.generate(context.request))
    if bad_reference:
        with pytest.raises(ChatProviderUnavailable): decode_answer(result.message, context)
    else:
        answer, refs, insufficient, basis = decode_answer(result.message, context)
        assert answer == planning and refs == (revision(),) and not insufficient and basis == 'canonical'
    assert len(seen) == 1
