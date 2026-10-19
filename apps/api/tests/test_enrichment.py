"""Explicit persistence control and existing Engine; offline, no DB or network."""
import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.llm.offline import LiteralSegmentProvider
from adapters.oidc import InvalidCredentials
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.core.models import ContextSpaceNotFound, GenerationResult, Message, MessageRole
from app.main import create_app
from app.policy.models import PolicyDecision
from app.understanding.enrichment import ConversationEnrichment, EnrichmentConflict, EnrichmentUnavailable


def payload(*texts):
    return dict(conversation_id=str(uuid4()), operation_id=str(uuid4()), persist_consent=True,
        turns=[dict(id=str(uuid4()), role='user', content=text, captured_at='2026-10-19T12:00:00Z') for text in texts or ('Le pilote reste une hypothèse 🌱.',)])


class Memory:
    def __init__(self):
        self.subject_id = str(uuid4())
        self.saved = {}
        self.calls = 0

    async def find(self, scope, source, fingerprint):
        old = self.saved.get(source)
        if old:
            if old[0] != fingerprint:
                raise EnrichmentConflict()
            return dict(old[1], replayed=True)

    async def publish(self, scope, source, revisions, fingerprint):
        self.calls += 1
        result = dict(context_id=scope, source_revision_id=source['id'], revision_ids=[r['id'] for r in revisions],
            replayed=False, provider_mode='offline-literal/1')
        self.saved[source['id']] = (fingerprint, result, deepcopy(source), deepcopy(revisions))
        return result


def setup(provider=None):
    repo = Memory()
    policy = Mock(evaluate=AsyncMock(return_value=PolicyDecision(allowed=True)))
    context = Mock(browse=AsyncMock(return_value=None))
    service = ConversationEnrichment(context=context, policy=policy,
        repository_for=lambda subject: repo, provider=provider or LiteralSegmentProvider())
    return repo, policy, context, service


def run(repo, service, scope, data):
    return asyncio.run(service.enrich(repo.subject_id, scope, data))


def test_source_and_proposal_exact_original_authority_and_replay():
    repo, policy, context, service = setup()
    scope, data = str(uuid4()), payload()
    result = run(repo, service, scope, data)
    old = deepcopy(data)
    second = run(repo, service, scope, data)
    assert second == dict(result, replayed=True) and repo.calls == 1 and data == old
    source, rows = next(iter(repo.saved.values()))[2:]
    assert rows[0]['content']['text'] == data['turns'][0]['content']
    quote = rows[0]['content']['citations'][0]
    assert source['content'][quote['start']:quote['end']] == quote['quote']
    assert rows[0]['validation_state'] == 'proposed' and rows[0]['origin_kind'] == 'ai'
    assert rows[0].get('validated_by') is None and rows[0]['provenance'] == [source['id']]
    metadata = source['origin']['metadata']
    assert metadata['submitted_by'] == repo.subject_id
    assert metadata['turn_declarations'][0]['timestamp_authority'] == 'browser-declared'
    assert all(c.args[0].action.value in ('propose_update', 'read_context') for c in policy.evaluate.call_args_list)
    assert context.browse.await_count >= 2
    changed = deepcopy(data); changed['turns'][0]['content'] = 'Different'
    with pytest.raises(EnrichmentConflict): run(repo, service, scope, changed)


def test_assistant_never_becomes_human_claim_or_implicit_confirmation():
    repo, _, _, service = setup()
    data = payload('Décision encore proposée.', 'Assistant invents approval')
    data['turns'][1]['role'] = 'assistant'
    run(repo, service, str(uuid4()), data)
    source, rows = next(iter(repo.saved.values()))[2:]
    assert 'assistant (unverified dialogue)' in source['content']
    assert len(rows) == 1 and 'approval' not in rows[0]['content']['text']


def test_explicit_empty_result_records_only_authorized_source():
    repo, _, _, service = setup(); data = payload('Unverified assistant text')
    data['turns'][0]['role'] = 'assistant'
    result = run(repo, service, str(uuid4()), data)
    assert result['revision_ids'] == []
    assert len(repo.saved) == 1


@pytest.mark.parametrize('failure',[RuntimeError('HTTP 429 private'), TimeoutError('private timeout')])
def test_provider_errors_do_not_write_or_retry(failure):
    provider = Mock(generate=AsyncMock(side_effect=failure))
    repo, _, _, service = setup(provider)
    with pytest.raises(EnrichmentUnavailable): run(repo, service, str(uuid4()), payload())
    assert repo.calls == 0 and provider.generate.await_count == 1 and not service._busy


def test_invalid_sibling_fails_whole_batch_and_citations_are_never_invented():
    class Bad:
        async def generate(self, request):
            result = await LiteralSegmentProvider().generate(request)
            import json
            output = json.loads(result.message.content)
            output['items'].append(dict(output['items'][0], local_id='bad', evidence=[]))
            return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(output)))
    repo, _, _, service = setup(Bad())
    with pytest.raises(ValueError): run(repo, service, str(uuid4()), payload())
    assert repo.calls == 0


def test_policy_denial_precedes_source_lookup_or_generation():
    repo, policy, context, service = setup()
    policy.evaluate.return_value = PolicyDecision(allowed=False)
    service.repository_for = Mock(side_effect=AssertionError('must not bind repository'))
    with pytest.raises(ContextSpaceNotFound): run(repo, service, str(uuid4()), payload())
    context.browse.assert_not_awaited()


@pytest.mark.parametrize('change', [
    lambda d: d.update(persist_consent=False),
    lambda d: d['turns'][0].update(content='\0'),
    lambda d: d['turns'][0].update(captured_at='2026-10-19'),
    lambda d: d['turns'].append(deepcopy(d['turns'][0])),
])
def test_invalid_selected_segment_never_publishes(change):
    repo, _, _, service = setup();data = payload();change(data)
    with pytest.raises(ValueError): run(repo, service, str(uuid4()), data)
    assert not repo.saved


def test_actual_http_auth_input_and_cache_guards():
    repo, policy, context, service = setup();scope=str(uuid4())
    async def auth(token):
        if token != 'alice': raise InvalidCredentials('invalid')
        return repo.subject_id
    app=create_app(services=ApplicationServices(context=context,policy=policy,enrichment=service),
        security=SecurityBindings(authenticate=auth,policy=policy))
    path='/context-spaces/'+scope+'/enrichments';data=payload()
    with TestClient(app) as client:
        assert client.post(path,json=data).status_code==401
        assert client.post(path,headers={'Authorization':'Bearer invalid'},json=data).status_code==401
        headers={'Authorization':'Bearer alice'}
        assert client.post(path+'?owner=alice',headers=headers,json=data).status_code==422
        assert client.post(path,headers=headers,json=dict(data,owner_id=repo.subject_id)).status_code==422
        result=client.post(path,headers=headers,json=data)
        assert result.status_code==200 and result.headers['Cache-Control']=='private, no-store'
        assert len(result.json()['revision_ids'])==1
        policy.evaluate.return_value=PolicyDecision(allowed=False)
        assert client.post(path,headers=headers,json=data).status_code==404


def test_owner_revoked_after_generation_never_publishes():
    repo, policy, _, service = setup()
    class Revoked:
        async def generate(self, request):
            result = await LiteralSegmentProvider().generate(request)
            policy.evaluate.return_value = PolicyDecision(allowed=False)
            return result
    service.provider = Revoked()
    with pytest.raises(ContextSpaceNotFound): run(repo, service, str(uuid4()), payload())
    assert repo.calls == 0 and not service._busy


def test_repeated_identical_quote_is_ambiguous_not_offset_disambiguated():
    repo, _, _, service = setup()
    with pytest.raises(ValueError): run(repo, service, str(uuid4()), payload('Same exact assertion.', 'Same exact assertion.'))
    assert repo.calls == 0


def test_inflight_same_operation_has_one_provider_call_without_automatic_retry():
    repo, _, _, service = setup()
    scope, data = str(uuid4()), payload()
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        class Delayed:
            calls = 0
            async def generate(self, request):
                self.calls += 1;started.set();await release.wait()
                return await LiteralSegmentProvider().generate(request)
        provider = Delayed();service.provider = provider
        first = asyncio.create_task(service.enrich(repo.subject_id, scope, data))
        await started.wait()
        with pytest.raises(EnrichmentUnavailable): await service.enrich(repo.subject_id, scope, data)
        release.set();await first
        assert provider.calls == 1 and repo.calls == 1
    asyncio.run(scenario())


def test_selected_intake_preserves_original_three_turn_serialization_and_ids():
    from app.understanding.selected import selected_source
    from app.understanding.extractor import UnderstandingExtractor
    from tests.test_understanding import MemoryRepository
    repository=MemoryRepository();scope=str(uuid4())
    conversation=dict(id='serializer-equivalence',revision_no=1,acquired_at='2026-10-19T00:00:00Z',
        turns=[dict(id=str(uuid4()),speaker='user (owner-declared)',text=text) for text in ('Une hypothèse 🌱.', 'Pas de commande.', 'Une question ouverte ?')],
        metadata=dict(submission_kind='owner_selected_browser_segment'))
    policy=Mock(evaluate=AsyncMock(return_value=PolicyDecision(allowed=True)))
    old=UnderstandingExtractor(repository=repository,policy=policy,provider=LiteralSegmentProvider())
    ref=asyncio.run(old.import_conversation(subject_id=repository.subject_id,context_id=scope,conversation=conversation))
    assert selected_source(scope,conversation)==repository.sources[ref]
    single=deepcopy(conversation);single['turns']=single['turns'][:1]
    with pytest.raises(ValueError):asyncio.run(old.import_conversation(subject_id=repository.subject_id,context_id=scope,conversation=single))
    assert len(selected_source(scope,single)['origin']['turns'])==1
