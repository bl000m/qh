"""Offline contract/invariant checks; these do not demonstrate model quality."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.consolidation import IntakeInput, PortableContext
from app.chat.implementation import ContextualChatService
from app.core.models import ContextSpaceNotFound
from app.understanding.consolidation import ContextConsolidation
from tests.test_chat_service import request


def document(text='Le responsable est Alice.'):
    return dict(id=str(uuid4()),kind='message',role='user',text=text,name=None,context=None)


def fixture():
    context=Mock(browse=AsyncMock(return_value=SimpleNamespace(revisions=())))
    policy=Mock(evaluate=AsyncMock(return_value=SimpleNamespace(allowed=True)))
    repo=Mock(read=AsyncMock(),claim=AsyncMock(),fail=AsyncMock(),publish=AsyncMock(),append=AsyncMock())
    ai=Mock(authorize_consolidation=AsyncMock(),_authorize=AsyncMock())
    ai.factory.diagnostic_call.return_value=Mock()
    service=ContextConsolidation(context=context,policy=policy,ai=ai,repository_for=lambda subject:repo)
    who=SimpleNamespace(subject_id=str(uuid4()))
    scope=str(uuid4());batch=dict(operation_id=str(uuid4()),current=None,intake=[document()],pending_count=1)
    repo.claim.return_value=batch
    return service,who,scope,repo,ai,batch


def test_unauthorized_owner_stops_before_private_reads_or_generation():
    service,who,scope,repo,ai,_=fixture()
    service.policy.evaluate.return_value=SimpleNamespace(allowed=False)
    for operation in (service.read(who.subject_id,scope),service.consolidate(who,scope),service.append(who.subject_id,scope,document())):
        with pytest.raises(ContextSpaceNotFound):asyncio.run(operation)
    repo.read.assert_not_awaited();repo.claim.assert_not_awaited();repo.append.assert_not_awaited();ai._authorize.assert_not_awaited()


def test_one_atomic_publish_after_engine_and_repeat_does_not_generate(monkeypatch):
    service,who,scope,repo,ai,batch=fixture()
    engine=AsyncMock(return_value=({'id':str(uuid4())},({'id':str(uuid4())},)))
    monkeypatch.setattr('app.understanding.consolidation.propose_selected_conversation',engine)
    asyncio.run(service.consolidate(who,scope))
    repo.publish.assert_awaited_once()
    assert repo.publish.call_args.args[2]==[r['id'] for r in batch['intake']]
    repo.claim.return_value={'replayed':True};repo.read.return_value=dict(current=None)
    asyncio.run(service.consolidate(who,scope))
    assert engine.await_count==1 and repo.publish.await_count==1


@pytest.mark.parametrize('failure',[TimeoutError(),ValueError('invalid citations'),None])
def test_failed_or_empty_engine_retains_pending_and_never_publishes(monkeypatch,failure):
    service,who,scope,repo,_,batch=fixture()
    engine=AsyncMock(side_effect=failure,return_value=({'id':str(uuid4())},()))
    monkeypatch.setattr('app.understanding.consolidation.propose_selected_conversation',engine)
    with pytest.raises((TimeoutError,ValueError)):asyncio.run(service.consolidate(who,scope))
    repo.publish.assert_not_awaited();repo.fail.assert_awaited_once_with(scope,batch['operation_id'])
    assert batch['intake'][0]['text']=='Le responsable est Alice.'


def test_all_original_intake_and_attribution_survive_correction():
    service,who,_,_,_,batch=fixture()
    batch['current']={'id':str(uuid4())}
    batch['intake']+=[document('Le responsable n’est plus Alice mais Bob.'),dict(document('Alice devrait valider.'),role='assistant')]
    frozen=deepcopy(batch)
    conversation=service._conversation(who.subject_id,batch)
    assert [t['text'] for t in conversation['turns']]==[r['text'] for r in batch['intake']]
    assert conversation['turns'][-1]['speaker']=='assistant (unverified dialogue)'
    assert batch==frozen


def test_portable_schema_rejects_secrets_and_import_does_not_confirm():
    value=dict(schema_version='qh.context-space/1',logical_id=str(uuid4()),name='Imported',version=1,
        consolidated_at='2026-10-26T12:00:00Z',understanding=[dict(id=str(uuid4()),text='Peut-être Bob.',
            primary_dimension='hypotheses_uncertainties',certainty='tentative',validation_state='proposed',
            evidence=[dict(source_revision_id=str(uuid4()),quote='Peut-être Bob.',turn_id=None)])])
    imported=IntakeInput(**dict(document(),kind='context',text=None,context=value))
    assert imported.context.understanding[0].certainty=='tentative'
    with pytest.raises(ValidationError):PortableContext(**dict(value,access_token='secret'))
    with pytest.raises(ValidationError):IntakeInput(**dict(document(),kind='document',name='unsupported.pdf'))
    with pytest.raises(ValidationError):IntakeInput(**dict(document(),kind='context',context=value))


def test_chat_uses_exact_snapshot_ids_without_browsing_all_proposals():
    row=SimpleNamespace(revision_id='snapshot-revision')
    context=Mock(browse=AsyncMock(return_value=SimpleNamespace(revisions=(row,))))
    chat=ContextualChatService(context=context,policy=Mock(),provider=Mock(),model='offline')
    rows,partial=asyncio.run(chat._collect(replace(request(),consolidated_revision_ids=('snapshot-revision',))))
    assert rows==(row,) and not partial
    assert context.browse.call_args.args[0].query.revision_id=='snapshot-revision'
    context.browse.return_value=SimpleNamespace(revisions=())
    from app.chat.context import ChatContextUnavailable
    with pytest.raises(ChatContextUnavailable):asyncio.run(chat._collect(replace(request(),consolidated_revision_ids=('snapshot-revision',))))


def test_answer_attribution_is_persisted_by_backend_after_version_recheck():
    service,who,scope,repo,ai,_=fixture()
    state=dict(current=dict(id='version',revision_ids=['exact-reference']))
    service.read=AsyncMock(return_value=state);repo.read.return_value=state
    answer=SimpleNamespace(message=SimpleNamespace(content='Une réponse attribuée.'),model='mistral-small-2603',
        support_basis='canonical',insufficient_context=True,partial_coverage=False,
        references=[SimpleNamespace(revision_id='exact-reference')])
    ai.respond=AsyncMock(return_value=answer)
    assert asyncio.run(service.respond(who,scope,request())) is answer
    saved=repo.append.call_args.args[1]
    assert saved['attribution']['reference_ids']==['exact-reference']
    assert saved['attribution']['insufficient_context'] and saved['role']=='assistant'
    assert ai.respond.call_args.args[1].consolidated_revision_ids==('exact-reference',)
    repo.append.reset_mock();repo.read.return_value=dict(current=dict(id='changed',revision_ids=[]))
    from app.understanding.enrichment import EnrichmentUnavailable
    with pytest.raises(EnrichmentUnavailable):asyncio.run(service.respond(who,scope,request()))
    repo.append.assert_not_awaited()


def test_diagnostic_initialization_failure_releases_running_job():
    service,who,scope,repo,ai,batch=fixture()
    ai.factory.diagnostic_call.side_effect=RuntimeError('offline diagnostic unavailable')
    with pytest.raises(RuntimeError):asyncio.run(service.consolidate(who,scope))
    repo.fail.assert_awaited_once_with(scope,batch['operation_id'])


def test_previous_machine_state_is_supplied_separately_from_original_citable_source():
    import json
    from app.core.models import GenerationRequest, GenerationResult, Message, MessageRole
    from app.understanding.uum import UumExtractionProvider
    original=dict(source_revision_id='source',input_sha256='digest',text='Exact original.',turns=[])
    source_message=Message(role=MessageRole.USER,content=json.dumps(original))
    delegate=Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content='{}'))))
    provider=UumExtractionProvider(delegate,consolidate=True,previous=({'text':'Prior unverified interpretation'},))
    asyncio.run(provider.generate(GenerationRequest(messages=(Message(role=MessageRole.SYSTEM,content='Engine'),source_message))))
    generated=delegate.generate.call_args.args[0]
    assert generated.messages[-1]==source_message
    assert 'Prior unverified interpretation' in generated.messages[-2].content
    assert 'not new evidence' in generated.messages[-2].content
    assert 'not new human' in generated.messages[0].content
