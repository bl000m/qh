"""Ordinary explicit sends for one verified development account, all owned Spaces.

No consent/grant/activation registry. The same canonical chat and Understanding
Engine retain policy, graph freshness, provenance and proposed-only publication.
"""
from decimal import Decimal

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
        if not await self.factory.verified(identity.subject_id, request.context_id):
            raise ChatProviderUnavailable('Verified provider unavailable')
        if reserve:
            remaining = self.factory.remaining()
            if not remaining['remaining_calls'] or Decimal(remaining['remaining_usd']) < Decimal('0.0024'):
                raise ProviderBudgetExceeded()
            if remaining['blocked']:
                raise ChatProviderUnavailable('Provider accounting requires review')

    async def capabilities(self, identity, request):
        await self.chat._authorize(request)
        enabled, exhausted = False, False
        remaining = dict(remaining_calls=0, remaining_usd='0')
        eligible = (identity.subject_id == request.subject_id and self.factory.eligible_identity(identity)
            and identity.verified_session_id and identity.work_expires_at
            and self.clock() < min(identity.expires_at, identity.work_expires_at)
            and self.factory.allowed(identity.subject_id, request.context_id))
        if eligible:
            remaining = {k:v for k,v in self.factory.remaining().items() if k!='blocked'}
            exhausted = not remaining['remaining_calls'] or Decimal(remaining['remaining_usd']) < Decimal('0.0024')
            enabled = await self.factory.available(identity.subject_id, request.context_id)
        return dict(automatic=bool(eligible), plafond_reached=bool(eligible and exhausted), enabled=enabled,
            model=self.factory.model if enabled else None, max_seconds=1800,
            max_calls=8, max_usd='0.20', provider_expires_at=self.factory.expires_at if enabled else None,
            **remaining)

    def _provider(self, identity, request):
        owner = self
        raw = self.factory.bind_global()
        class Guarded:
            async def generate(self, generated):
                await owner._authorize(identity, request, reserve=True)
                return await raw.generate(generated)
        return Guarded()

    async def respond(self, identity, request):
        await self._authorize(identity, request, reserve=True)
        result = await self.chat.respond(request, provider=self._provider(identity, request),
            model=self.factory.model, allow_empty=True)
        await self._authorize(identity, request)
        return result

    async def enrich(self, identity, scope, payload):
        request = ChatRequest(subject_id=identity.subject_id, context_id=scope, messages=())
        await self._authorize(identity, request)
        if payload.get('extraction_mode') != 'semantic' or not self.enrichment.uum:
            raise ValueError('Explicit UUM semantic request required')
        async def before_publish():
            await self._authorize(identity, request)
        return await self.enrichment.enrich(identity.subject_id, scope, payload,
            semantic_provider=self._provider(identity, request), provider_mode='uum-mistral/3',
            before_publish=before_publish)
