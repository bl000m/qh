"""Ordinary explicit sends for one verified development account, all owned Spaces.

No consent/grant/activation registry. The same canonical chat and Understanding
Engine retain policy, graph freshness, provenance and proposed-only publication.
"""
from decimal import Decimal
from dataclasses import replace

from app.chat.context import ChatProviderUnavailable
from app.core.models import ProviderBudgetExceeded
from app.chat.models import ChatRequest
from app.core.models import ContextSpaceNotFound


class DevelopmentAI:
    def __init__(self, *, chat, enrichment, factory, clock):
        self.chat, self.enrichment, self.factory, self.clock = chat, enrichment, factory, clock

    async def _authorize(self, identity, request, *, reserve=False):
        # Policy precedes any private configuration, ledger or context exposure.
        await self.chat._authorize(request)
        if (identity.subject_id != request.subject_id or not self.factory.eligible_identity(identity)
            or not identity.verified_session_id or not identity.work_expires_at
            or self.clock() >= min(identity.expires_at, identity.work_expires_at)
            or not self.factory.allowed(identity.subject_id, request.context_id)):
            raise ContextSpaceNotFound('Context space not found')
        if reserve:
            remaining = self.factory.remaining()
            if remaining['blocked']:
                raise ChatProviderUnavailable('Provider accounting requires review')
            if remaining['remaining_calls'] == 0 or Decimal(remaining['remaining_usd']) < self.factory.reservation_usd:
                raise ProviderBudgetExceeded()
        if not await self.factory.verified(identity.subject_id, request.context_id):
            raise ChatProviderUnavailable('Verified provider unavailable')

    async def capabilities(self, identity, request):
        await self.chat._authorize(request)
        enabled, exhausted = False, False
        remaining = dict(remaining_calls=0, remaining_usd='0')
        eligible = (identity.subject_id == request.subject_id and self.factory.eligible_identity(identity)
            and identity.verified_session_id and identity.work_expires_at
            and self.clock() < min(identity.expires_at, identity.work_expires_at)
            and self.factory.allowed(identity.subject_id, request.context_id))
        if eligible:
            accounting = self.factory.remaining()
            remaining = {k:v for k,v in accounting.items() if k!='blocked'}
            exhausted = not accounting['blocked'] and (remaining['remaining_calls'] == 0 or Decimal(remaining['remaining_usd']) < self.factory.reservation_usd)
            enabled = await self.factory.available(identity.subject_id, request.context_id)
        return dict(automatic=bool(eligible), plafond_reached=bool(eligible and exhausted), enabled=enabled,
            model=self.factory.model if enabled else None, max_seconds=None if self.factory.poc else 1800,
            max_calls=self.factory.aggregate_calls, max_usd=self.factory.aggregate_usd, provider_expires_at=self.factory.expires_at if enabled else None,
            **remaining)

    def _provider(self, identity, request, diagnostic):
        owner = self
        raw = self.factory.bind_global(diagnostic=diagnostic)
        class Guarded:
            async def generate(self, generated):
                await owner._authorize(identity, request, reserve=True)
                return await raw.generate(generated)
        return Guarded()

    async def diagnostics(self, identity, request, delete_id=None):
        # Diagnostics remain readable when price/quota is unavailable; never HTTP to Mistral.
        await self.chat._authorize(request)
        if (identity.subject_id != request.subject_id or not self.factory.eligible_identity(identity)
            or not identity.verified_session_id or not identity.work_expires_at
            or self.clock() >= min(identity.expires_at, identity.work_expires_at)):
            raise ContextSpaceNotFound('Context space not found')
        store = self.factory.diagnostics
        if delete_id is not None:
            store.delete(subject=identity.subject_id, scope=request.context_id, identity=delete_id)
            return dict(deleted=True)
        return dict(retention_seconds=store.retention,
            items=store.records(subject=identity.subject_id, scope=request.context_id))

    async def respond(self, identity, request):
        request = replace(request, extended_dialogue=True)
        await self._authorize(identity, request, reserve=True)
        diagnostic = self.factory.diagnostic_call(identity.subject_id, request.context_id, 'chat')
        try:
            result = await self.chat.respond(request, provider=self._provider(identity, request, diagnostic),
                model=self.factory.model, allow_empty=True, observer=diagnostic.check)
            try:
                await self._authorize(identity, request)
            except Exception:
                diagnostic.check('development.post_response_identity_policy', False, 'Verified identity, receipt or CHAT no longer valid')
                raise
            diagnostic.check('development.post_response_identity_policy', True)
            diagnostic.finish('accepted', 'chat_return')
            return result
        except Exception as exc:
            diagnostic.check('chat.application_return', False, type(exc).__name__)
            diagnostic.finish('rejected', 'chat')
            raise

    async def authorize_consolidation(self, identity, scope):
        request = ChatRequest(subject_id=identity.subject_id, context_id=scope, messages=())
        await self._authorize(identity, request)
        return request

    async def enrich(self, identity, scope, payload):
        request = ChatRequest(subject_id=identity.subject_id, context_id=scope, messages=())
        await self._authorize(identity, request)
        if payload.get('extraction_mode') != 'semantic' or not self.enrichment.uum:
            raise ValueError('Explicit UUM semantic request required')
        diagnostic = self.factory.diagnostic_call(identity.subject_id, scope, 'uum')
        async def before_publish():
            await self._authorize(identity, request)
            diagnostic.check('uum.pre_publication_identity_policy_graph', True)
        try:
            result = await self.enrichment.enrich(identity.subject_id, scope, payload,
                semantic_provider=self._provider(identity, request, diagnostic), provider_mode='uum-mistral/3',
                before_publish=before_publish, observer=diagnostic.check)
            diagnostic.check('uum.atomic_proposed_publication', True)
            diagnostic.finish('accepted', 'uum_publication')
            return result
        except Exception as exc:
            diagnostic.check('uum.application_publication', False, type(exc).__name__)
            diagnostic.finish('rejected', 'uum')
            raise
