"""Explicit owner-selected chat segment -> existing Understanding Engine.

Persistence and provider disclosure are separate from ordinary CHAT. This first
increment binds only an offline provider; existing Mistral chat grants never cover
extraction. The browser declares dialogue roles; QH attests submission identity,
not that an assistant text really came from a particular provider.
"""
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid5

from app.core.models import ProviderBudgetExceeded
from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound
from app.policy.models import PolicyAction, PolicyRequest
from app.understanding.extractor import digest, canonical_json, timestamp
from app.understanding.selected import propose_selected_conversation

EXTRACTION_KEY = 'qh39-selected-segment/1-resolved'
SEMANTIC_KEY = 'qh51-selected-semantic/2-resolved'


class EnrichmentConflict(ValueError):
    pass


class EnrichmentUnavailable(RuntimeError):
    pass


class EnrichmentRepository(Protocol):
    subject_id: str
    async def find(self, scope: str, source: str, fingerprint: str) -> dict | None: ...
    async def publish(self, scope: str, source: dict, revisions: tuple, fingerprint: str) -> dict: ...


class ConversationEnrichment:
    def __init__(self, *, context, policy, repository_for, provider, clock=None, semantic_provider=None, uum=False):
        self.context, self.policy = context, policy
        self.repository_for, self.provider = repository_for, provider
        self.semantic_provider = semantic_provider
        self.uum = uum
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._busy = set()

    async def _allow(self, subject, scope):
        decision = await self.policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.PROPOSE_UPDATE, context_ids=(scope,)))
        if not decision.allowed:
            raise ContextSpaceNotFound('Context space not found')

    async def capabilities(self, subject, scope):
        await self._allow(subject, scope)
        await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', limit=1)))
        await self._allow(subject, scope)
        return dict(literal=True, semantic=self.semantic_provider is not None,
            provider_mode=('uum-simulated/3' if self.uum else 'semantic-simulated/2') if self.semantic_provider is not None else None,
            external_disclosure=False)

    async def _vocabulary(self, subject, scope):
        from app.core.assignments import theme_name
        names, partial = set(), False
        for view in ('current', 'proposed'):
            result = await self.context.browse(ContextRequest(subject_id=subject,
                query=ContextBrowse(context_id=scope, view=view, limit=20,
                    descriptor_dimension='thematic', include_tentative=True, latest_pending=view=='proposed')))
            partial |= result.next_after_revision_id is not None
            for row in result.revisions:
                if row.type_version != 2 or not row.type_id.startswith('qh.generic.'):
                    continue
                for d in row.content.get('descriptors', []):
                    if d.get('dimension') == 'thematic' and d.get('review_state') in ('proposed','accepted') and 'name_candidate' not in d:
                        names.add(theme_name(d['value']))
        return tuple(sorted(names)[:40]), partial or len(names)>40

    async def enrich(self, subject, scope, payload, *, semantic_provider=None,
                     provider_mode=None, before_publish=None, observer=None):
        # Authorization before private reads, idempotency lookup or provider work.
        await self._allow(subject, scope)
        mode = payload.get('extraction_mode', 'literal')
        if mode not in ('literal', 'semantic'):
            raise ValueError('Explicit supported extraction mode required')
        delegate = semantic_provider or self.semantic_provider
        if mode == 'semantic' and delegate is None:
            raise EnrichmentUnavailable('Semantic extraction is not activated; no fallback')
        UUID(scope)
        UUID(payload['conversation_id'])
        UUID(payload['operation_id'])
        if payload['persist_consent'] is not True:
            raise ValueError('Explicit source and proposal persistence consent required')
        turns = payload['turns']
        if not isinstance(turns, list) or not 1 <= len(turns) <= 8:
            raise ValueError('Select one to eight turns')
        seen = set()
        for turn in turns:
            UUID(turn['id'])
            if turn['id'] in seen or turn['role'] not in ('user', 'assistant'):
                raise ValueError('Distinct identified user/assistant turns required')
            seen.add(turn['id'])
            if not isinstance(turn['content'], str) or not turn['content'].strip() or len(turn['content']) > 4096 or '\0' in turn['content']:
                raise ValueError('Bounded original turn text required')
            timestamp(turn['captured_at'])
        if len(canonical_json(payload).encode()) > 20000:
            raise ValueError('Selected segment exceeds byte limit')
        fingerprint = digest(payload)
        conversation_id = 'qh39:' + payload['conversation_id'] + ':' + payload['operation_id']
        source_id = str(uuid5(UUID(scope), 'conversation:' + conversation_id))
        source_revision_id = str(uuid5(UUID(source_id), 'revision:1'))
        repository = self.repository_for(subject)
        await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', limit=1)))
        existing = await repository.find(scope, source_revision_id, fingerprint)
        if existing is not None:
            await self._allow(subject, scope)
            return existing
        key = (str(subject), scope, source_revision_id)
        if key in self._busy or len(self._busy) >= 100:
            raise EnrichmentUnavailable('An enrichment is already in progress; no automatic retry')
        self._busy.add(key)
        try:
            from app.understanding.semantic import SemanticExtractionProvider
            vocabulary, partial = await self._vocabulary(subject, scope) if mode=='semantic' and not self.uum else ((), False)
            extraction_key = ('qh51-uum-semantic/3' if mode=='semantic' else 'qh51-uum-literal/3') if self.uum else (SEMANTIC_KEY if mode=='semantic' else EXTRACTION_KEY)
            provider = SemanticExtractionProvider(delegate, known_themes=vocabulary,
                vocabulary_partial=partial) if mode=='semantic' else self.provider
            if self.uum:
                from app.understanding.uum import UumExtractionProvider
                provider = UumExtractionProvider(delegate if mode=='semantic' else self.provider, literal=mode=='literal')
            conversation = dict(id=conversation_id, revision_no=1, acquired_at=self.clock(),
                turns=[dict(id=t['id'], speaker='user (owner-declared)' if t['role']=='user' else 'assistant (unverified dialogue)', text=t['content']) for t in turns],
                metadata=dict(submission_kind='owner_selected_browser_segment', submitted_by=str(subject),
                    conversation_id=payload['conversation_id'], operation_id=payload['operation_id'],
                    request_sha256=fingerprint, extraction_key=extraction_key,
                    provider_mode=provider_mode or ('uum-simulated/3' if self.uum else 'semantic-simulated/2') if mode=='semantic' else ('uum-offline-literal/3' if self.uum else 'offline-literal/1'),
                    turn_declarations=[dict(turn_id=t['id'], role=t['role'], captured_at=t['captured_at'],
                        timestamp_authority='browser-declared') for t in turns]))
            if mode=='semantic' and not self.uum:
                conversation['metadata'].update(known_themes=list(vocabulary), vocabulary_coverage='partial' if partial else 'complete')
            try:
                source, revisions = await propose_selected_conversation(subject_id=subject, context_id=scope,
                    conversation=conversation, extraction_key=extraction_key, policy=self.policy, provider=provider,
                    descriptor_version=3 if self.uum else (2 if mode=='semantic' else 1), observer=observer)
            except ProviderBudgetExceeded:
                raise
            except PermissionError:
                raise ContextSpaceNotFound('Context space not found') from None
            except ValueError:
                raise
            except Exception:
                raise EnrichmentUnavailable('Extraction unavailable; nothing published, no automatic retry') from None
            await self._allow(subject, scope)
            await self.context.browse(ContextRequest(subject_id=subject,
                query=ContextBrowse(context_id=scope, view='history', limit=1)))
            await self._allow(subject, scope)
            if before_publish is not None:
                await before_publish()
            return await repository.publish(scope, source, revisions, fingerprint)
        finally:
            self._busy.remove(key)
