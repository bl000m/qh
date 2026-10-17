import asyncio
from dataclasses import replace
import json

import pytest

from app.chat.context import ChatContextUnavailable, ChatInputInvalid, ChatProviderUnavailable
from app.chat.implementation import ContextualChatService
from app.chat.models import ChatRequest
from app.core.models import ContextResult, ContextSpaceNotFound, Message, MessageRole
from app.policy.owner import OwnerPolicyService
from adapters.llm.chat_mock import MockChatProvider
from tests.test_chat_context import revision


def case(rows=None, provider=None):
    class Context:
        calls=[]
        values=[revision()] if rows is None else rows
        async def browse(self,request):
            self.calls.append(request)
            q=request.query
            matches=[r for r in self.values if (r.validation_state=='proposed' if q.view=='proposed' else r.is_current_confirmed)]
            matches=sorted(matches,key=lambda r:r.revision_id)
            if q.after_revision_id:matches=[r for r in matches if r.revision_id>q.after_revision_id]
            return ContextResult(hits=(),revisions=tuple(matches[:q.limit]),
                next_after_revision_id=matches[q.limit-1].revision_id if len(matches)>q.limit else None)
    owner=['alice']
    async def lookup(scope):return owner[0] if scope=='space' else None
    context=Context()
    class Provider(MockChatProvider):
        calls=[]
        async def generate(self,request):
            self.calls.append(request)
            return await super().generate(request)
    model=provider or Provider()
    service=ContextualChatService(context=context,policy=OwnerPolicyService(owner_for=lookup),
                                 provider=model,model='test-mock')
    return service,context,model,owner


def request(**kwargs):
    return ChatRequest(**(dict(subject_id='alice',context_id='space',
        messages=(Message(role=MessageRole.USER,content='Décisions ?'),)) | kwargs))


def test_default_current_and_explicit_proposed_only():
    current=revision();proposal=replace(current,revision_id='proposal',validation_state='proposed',is_current_confirmed=False)
    service,context,model,_=case([current,proposal])
    result=asyncio.run(service.respond(request()))
    assert result.references==(current,) and result.provided_revisions==(current,)
    assert len(model.calls)==1 and {r.query.view for r in context.calls}=={'current'}
    context.calls.clear()
    result=asyncio.run(service.respond(request(include_proposed=True)))
    assert set(r.revision_id for r in result.provided_revisions)=={'revision','proposal'}
    assert {r.query.view for r in context.calls}=={'current','proposed'}


def test_empty_or_proposed_only_requires_opt_in_and_never_generates():
    proposal=revision(validation_state='proposed',is_current_confirmed=False)
    for rows in ([],[proposal]):
        service,_,model,_=case(rows)
        result=asyncio.run(service.respond(request()))
        assert result.insufficient_context and not result.provided_revisions and not model.calls
        assert result.generation_seconds is None


@pytest.mark.parametrize('change',[{'subject_id':'bob'},{'context_id':'foreign'}])
def test_policy_precedes_private_read_and_generation(change):
    service,context,model,_=case()
    with pytest.raises(ContextSpaceNotFound):asyncio.run(service.respond(request(**change)))
    assert not context.calls and not model.calls


def test_concurrent_ownership_revocation_discards_answer():
    service,_,model,owner=case()
    generate=model.generate
    async def revoke(request):
        owner[0]='bob'
        return await generate(request)
    model.generate=revoke
    with pytest.raises(ContextSpaceNotFound):asyncio.run(service.respond(request()))
    assert len(model.calls)==1


def test_context_change_during_provider_work_discards_answer():
    service,context,model,_=case()
    generate=model.generate
    async def changed(request):
        context.values=[replace(context.values[0],content={'text':'Changed'})]
        return await generate(request)
    model.generate=changed
    with pytest.raises(ChatContextUnavailable):asyncio.run(service.respond(request()))


def test_bounded_pages_partial_coverage_and_no_semantic_search():
    rows=[revision(revision_id=f'{i:03}',content={'text':'x'}) for i in range(25)]
    service,context,model,_=case(rows)
    result=asyncio.run(service.respond(request()))
    assert result.partial_coverage and len(result.provided_revisions)<=20 and len(model.calls)==1
    assert len(context.calls)==6 and all(r.query.limit==10 and r.query.view=='current' for r in context.calls)
    assert all(not hasattr(r.query,'text') for r in context.calls)


@pytest.mark.parametrize('error',[RuntimeError('synthetic-private-key'),ValueError('private-payload')])
def test_provider_errors_sanitized_and_not_retried(error):
    service,_,model,_=case()
    calls=[]
    async def failed(request):calls.append(request);raise error
    model.generate=failed
    with pytest.raises(ChatProviderUnavailable) as exc:asyncio.run(service.respond(request()))
    assert len(calls)==1 and 'private' not in str(exc.value)


def test_foreign_declared_references_fail_without_retry():
    service,_,model,_=case()
    async def bad(request):
        from app.core.models import GenerationResult
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps({
            'answer':'Invented','revision_ids':['foreign'],'insufficient_context':False})))
    model.generate=bad
    with pytest.raises(ChatProviderUnavailable):asyncio.run(service.respond(request()))


def test_invalid_history_fails_before_reading_context():
    service,context,model,_=case()
    with pytest.raises(ChatInputInvalid):asyncio.run(service.respond(request(messages=())))
    assert not context.calls and not model.calls
