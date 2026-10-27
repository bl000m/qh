"""Global Context Space consolidation through the existing UUM Engine.

Consolidated means machine interpretation, never human confirmation. Original
intake is replayed together so corrections cannot blindly erase earlier evidence.
"""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json

from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound, Message, MessageRole, ProviderBudgetExceeded
from app.chat.context import ChatProviderUnavailable
from app.policy.models import PolicyAction, PolicyRequest
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import UumExtractionProvider
from app.understanding.enrichment import EnrichmentUnavailable
from app.understanding import recap as recap_output


class WorkspaceChatFailed(ChatProviderUnavailable):
    pass


class ContextConsolidation:
    def __init__(self, *, context, policy, ai, repository_for):
        self.context, self.policy, self.ai = context, policy, ai
        self.repository_for = repository_for

    async def _allow(self, subject, scope):
        decision = await self.policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.PROPOSE_UPDATE, context_ids=(scope,)))
        if not decision.allowed:
            raise ContextSpaceNotFound('Context space not found')
        await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', limit=1)))

    async def read(self, subject, scope):
        await self._allow(subject, scope)
        state = await self.repository_for(subject).read(scope)
        rows = []
        ids = state.get('understanding_ids', state['current']['revision_ids'] if state['current'] else [])
        if ids:
            for revision in ids:
                page = await self.context.browse(ContextRequest(subject_id=subject,
                    query=ContextBrowse(context_id=scope, view='history', limit=1, revision_id=revision)))
                if len(page.revisions)!=1 or page.revisions[0].revision_id!=revision:
                    raise EnrichmentUnavailable('Consolidated revision unavailable')
                rows.append(asdict(page.revisions[0]))
        await self._allow(subject, scope)
        return dict(**state, understanding=rows, recap=recap_output.from_version(rows, state['current']))

    async def append(self, subject, scope, document):
        await self._allow(subject, scope)
        return await self.repository_for(subject).append(scope, document)

    async def consolidate(self, identity, scope, regeneration=None):
        await self._allow(identity.subject_id, scope)
        if self.ai is None:
            raise EnrichmentUnavailable('AI unavailable')
        request = await self.ai.authorize_consolidation(identity, scope)
        repository = self.repository_for(identity.subject_id)
        batch = await repository.claim(scope, regeneration) if regeneration else await repository.claim(scope)
        if batch.get('replayed'):
            return await self.read(identity.subject_id, scope)
        operation = batch['operation_id']
        diagnostic = None
        try:
            diagnostic = self.ai.factory.diagnostic_call(identity.subject_id, scope, 'uum')
            previous = ()
            if batch['current']:
                current = await self.read(identity.subject_id, scope)
                previous = tuple(dict(text=row['content']['text'],
                    primary_dimension=row['content'].get('primary_dimension'),
                    validation_state=row['validation_state']) for row in current['understanding'])
            provider = UumExtractionProvider(self.ai._provider(identity, request, diagnostic),
                consolidate=True, previous=previous, with_recap=True, observer=diagnostic.check)
            original = await repository.original(scope, batch['current']['source_revision_id']) if batch.get('regenerating') else None
            source, revisions = await propose_selected_conversation(
                subject_id=identity.subject_id, context_id=scope,
                conversation=self._conversation(identity.subject_id, batch),
                extraction_key='qh-context-uum/3'+(':'+operation if original else ''), original_source=original,
                policy=self.policy, descriptor_version=3,
                provider=provider,
                observer=diagnostic.check)
            if not revisions:
                raise ValueError('No structured understanding produced')
            revisions = recap_output.bind(provider.recap, revisions, operation)
            await self.ai._authorize(identity, request)
            await self._allow(identity.subject_id, scope)
            result = await repository.publish(scope, operation,
                [row['id'] for row in batch['intake']], source, revisions)
            diagnostic.check('uum.atomic_context_consolidation', True)
            diagnostic.finish('accepted', 'context_consolidation')
            return result
        except BaseException:
            # On ambiguous commit, the repository only marks a still-running job;
            # an already committed idle version remains intact and replayable.
            await repository.fail(scope, operation)
            if diagnostic is not None:
                diagnostic.finish('rejected', 'context_consolidation')
            raise

    def _conversation(self, subject, batch):
        turns = []
        for row in batch['intake']:
            imported = row['kind']=='context'
            text = json.dumps(row['context'], ensure_ascii=False, sort_keys=True) if imported else row['text']
            speaker = 'imported unverified machine understanding' if imported else 'assistant (unverified dialogue)' if row.get('role')=='assistant' else 'user (owner-declared)'
            turns.append(dict(id=row['id'], speaker=speaker, text=text))
        return dict(id='qh-context:'+batch['operation_id'], revision_no=1,
            acquired_at=datetime.now(timezone.utc).isoformat(), turns=turns,
            metadata=dict(submission_kind='owner_context_consolidation',
                submitted_by=str(subject),
                operation_id=batch['operation_id'],
                previous_version=batch['current']['id'] if batch['current'] else None,
                intake_ids=[r['id'] for r in batch['intake']]))

    async def respond(self, identity, scope, request, question, operation):
        if self.ai is None:
            raise EnrichmentUnavailable('AI unavailable')
        state = await self.read(identity.subject_id, scope)
        repository = self.repository_for(identity.subject_id)
        await self.ai.authorize_consolidation(identity, scope)
        claimed = await repository.claim_chat(scope, question, operation)
        if claimed.get('completed'):
            return dict(state='completed')
        try:
            result = await self.ai.respond(identity, replace(request, messages=self._dialogue(claimed['intake'], question),
                include_proposed=True, consolidated_revision_ids=tuple(r['revision_id'] for r in state.get('understanding', [])) if 'understanding' in state else tuple(state['current']['revision_ids']) if state['current'] else ()))
            after = await repository.read(scope)
            if after['current'] != state['current'] or after.get('understanding_ids') != state.get('understanding_ids'):
                raise EnrichmentUnavailable('Understanding changed during answer')
            await self._allow(identity.subject_id, scope)
        except Exception as exc:
            await repository.finish_chat(scope, question, operation)
            if isinstance(exc, (ProviderBudgetExceeded, ContextSpaceNotFound)):
                raise
            raise WorkspaceChatFailed('Response generation failed') from None
        # If publication is uncertain, leave the running receipt. Synchronization
        # must establish the result before a new paid attempt can be claimed.
        await repository.finish_chat(scope, question, operation, dict(kind='message',role='assistant',
            text=result.message.content,name=None,context=None,reply_to=question,
            attribution=dict(model=result.model,support_basis=result.support_basis,
                insufficient_context=result.insufficient_context,partial_coverage=result.partial_coverage,
                reference_ids=[r.revision_id for r in result.references])))
        return dict(state='completed')

    @staticmethod
    def _dialogue(items, question):
        replies = {r['reply_to']:r for r in items if r.get('reply_to')}
        messages = []
        for row in items:
            if row['kind']!='message' or row.get('reply_to'):
                continue
            message = Message(role=MessageRole(row['role']),content=row['text'])
            if messages and messages[-1].role==message.role:
                messages[-1] = Message(role=message.role,content=messages[-1].content+'\n\n'+message.content)
            elif messages or message.role==MessageRole.USER:
                messages.append(message)
            if row['id']==question:
                return tuple(messages)
            if row['id'] in replies:
                messages.append(Message(role=MessageRole.ASSISTANT,content=replies[row['id']]['text']))
        raise ValueError('Persisted question required')
