"""Global Context Space consolidation through the existing UUM Engine.

Consolidated means machine interpretation, never human confirmation. Original
intake is replayed together so corrections cannot blindly erase earlier evidence.
"""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import time

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
    def __init__(self, *, context, policy, ai, repository_for, pdf_parser=None):
        self.context, self.policy, self.ai = context, policy, ai
        self.repository_for = repository_for
        self.pdf_parser = pdf_parser

    async def _allow(self, subject, scope, *, verify_graph=True):
        decision = await self.policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.PROPOSE_UPDATE, context_ids=(scope,)))
        if not decision.allowed:
            raise ContextSpaceNotFound('Context space not found')
        if verify_graph:
            await self.context.browse(ContextRequest(subject_id=subject,
                query=ContextBrowse(context_id=scope, view='history', limit=1)))

    async def read(self, subject, scope):
        await self._allow(subject, scope, verify_graph=False)
        state = await self.repository_for(subject).read(scope)
        ids = state.get('understanding_ids', state['current']['revision_ids'] if state['current'] else [])
        # One exact batch shares readiness, graph verification and canonical
        # hydration. Empty Spaces still pass through the graph availability gate.
        page = await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', limit=max(1, len(ids)), revision_ids=tuple(ids))))
        indexed = {row.revision_id: row for row in page.revisions} if ids else {}
        if set(indexed) != set(ids) or ids and len(page.revisions) != len(ids):
            raise EnrichmentUnavailable('Consolidated revision unavailable')
        rows = [asdict(indexed[id]) for id in ids]
        await self._allow(subject, scope, verify_graph=False)
        return dict(**state, understanding=rows, recap=recap_output.from_version(rows, state['current']))

    async def append(self, subject, scope, document):
        await self._allow(subject, scope)
        return await self.repository_for(subject).append(scope, document)

    async def import_pdf(self, subject, scope, operation, name, data, display_name=None):
        from app.understanding.documents import prepare_document
        await self._allow(subject, scope)
        if self.pdf_parser is None:
            raise EnrichmentUnavailable('PDF parser unavailable')
        pages=await self.pdf_parser(data)
        document,source=prepare_document(scope,operation,name,data,pages,display_name)
        await self._allow(subject, scope, verify_graph=False)
        return await self.repository_for(subject).import_document(scope,document,source,data)

    async def documents(self, subject, scope):
        await self._allow(subject, scope, verify_graph=False)
        return await self.repository_for(subject).documents(scope)

    async def document(self, subject, scope, revision):
        await self._allow(subject, scope, verify_graph=False)
        return await self.repository_for(subject).document(scope,revision)

    async def consolidate(self, identity, scope, regeneration=None):
        started_at = time.perf_counter()
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
                consolidate=True, previous=previous, with_recap=True, chunked=any(row.get('source_revision_id') for row in batch['intake']), observer=diagnostic.check, measure=diagnostic.measure)
            original = await repository.original(scope, batch['current']['source_revision_id']) if batch.get('regenerating') else None
            source, revisions = await propose_selected_conversation(
                subject_id=identity.subject_id, context_id=scope,
                conversation=self._conversation(identity.subject_id, batch),
                extraction_key='qh-context-uum/3'+(':'+operation if original else ''), original_source=original,
                policy=self.policy, descriptor_version=3,
                provider=provider,
                observer=diagnostic.check)
            if not revisions:
                if any(row.get('source_revision_id') for row in batch['intake']):
                    from app.understanding.documents import DocumentInvalid
                    raise DocumentInvalid('Aucune proposition produite. Les originaux restent conservés ; la compréhension n’a pas été mise à jour.')
                raise ValueError('No structured understanding produced')
            documents=[await repository.original(scope,row['source_revision_id']) for row in batch['intake'] if row.get('source_revision_id')]
            if documents:
                from app.understanding.documents import original_citations
                revisions=original_citations(revisions,documents)
            if provider.parts:
                for revision in revisions:
                    revision['content']['extraction']['parts']=provider.parts
            revisions = recap_output.bind(provider.recap, revisions, operation)
            await self.ai._authorize(identity, request)
            await self._allow(identity.subject_id, scope)
            result = await repository.publish(scope, operation,
                [row['id'] for row in batch['intake']], source, revisions)
            await self._allow(identity.subject_id, scope, verify_graph=False)
            # This is the committed write receipt, not a graph retrieval. Reuse
            # its validated recap; detailed reads retain the graph readiness gate.
            result = dict(result, recap=recap_output.from_version(revisions, result['current']))
            diagnostic.check('uum.atomic_context_consolidation', True)
            diagnostic.finish('accepted', 'context_consolidation', started_at=started_at)
            return result
        except BaseException:
            # On ambiguous commit, the repository only marks a still-running job;
            # an already committed idle version remains intact and replayable.
            await repository.fail(scope, operation)
            if diagnostic is not None:
                diagnostic.finish('rejected', 'context_consolidation', started_at=started_at)
            raise

    def _conversation(self, subject, batch):
        turns = []
        for row in batch['intake']:
            if row.get('document_turns'):
                turns.extend(t for t in row['document_turns'] if t['text'].strip())
                continue
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

    async def _document_answer(self, subject, scope, repository, question, operation):
        from app.chat.documents import document_reply
        claimed=await repository.claim_chat(scope,question,operation)
        if claimed.get('completed'):
            return dict(state='completed')
        try:
            row=next(r for r in claimed['intake'] if r['id']==question)
            reply=document_reply(row['text'],await self.documents(subject,scope))
            await self._allow(subject,scope,verify_graph=False)
        except Exception:
            await repository.finish_chat(scope,question,operation)
            raise
        await repository.finish_chat(scope,question,operation,dict(kind='message',role='assistant',
            text=reply['text'],documents=reply['documents'],name=None,context=None,reply_to=question))
        return dict(state='completed')

    async def respond(self, identity, scope, request, question, operation):
        from app.chat.documents import is_original_request, document_selection, scoped_revision_ids
        await self._allow(identity.subject_id,scope,verify_graph=False)
        repository=self.repository_for(identity.subject_id)
        intake=await repository.read(scope)
        asked=next((r for r in intake['intake'] if r['id']==question and r['kind']=='message' and r['role']=='user'),None)
        if asked is None:
            raise ValueError('Persisted question required')
        if is_original_request(asked['text']):
            return await self._document_answer(identity.subject_id,scope,repository,question,operation)
        if self.ai is None:
            raise EnrichmentUnavailable('AI unavailable')
        state = await self.read(identity.subject_id, scope)
        repository = self.repository_for(identity.subject_id)
        await self.ai.authorize_consolidation(identity, scope)
        claimed = await repository.claim_chat(scope, question, operation)
        if claimed.get('completed'):
            return dict(state='completed')
        try:
            documents=[dict(source_revision_id=r['source_revision_id'],filename=r['name'],display_name=r.get('display_name',r['name'])) for r in claimed['intake'] if r.get('source_revision_id')]
            selected,ambiguous=document_selection(asked['text'],documents)
            if selected is not None and ambiguous:
                await repository.finish_chat(scope,question,operation,dict(kind='message',role='assistant',
                    text='De quel document parles-tu ? Précise son nom pour conserver le bon périmètre.',name=None,context=None,reply_to=question))
                return dict(state='completed')
            ids=tuple(r['revision_id'] for r in state.get('understanding', [])) if 'understanding' in state else tuple(state['current']['revision_ids']) if state['current'] else ()
            messages=self._dialogue(claimed['intake'],question)
            if selected is not None:
                ids=scoped_revision_ids(state.get('understanding',[]),selected,documents)
                if not ids:
                    await repository.finish_chat(scope,question,operation,dict(kind='message',role='assistant',
                        text='Aucune information mémorisée attribuée à ce document ne permet de répondre. Tu peux consulter l’original.',
                        documents=selected,name=None,context=None,reply_to=question))
                    return dict(state='completed')
                # Prior assistant responses can contain facts from other PDFs.
                messages=(Message(role=MessageRole.USER,content=asked['text']),)
            result = await self.ai.respond(identity, replace(request, messages=messages,
                include_proposed=True, consolidated_revision_ids=ids))
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
