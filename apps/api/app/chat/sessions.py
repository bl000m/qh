"""Ephemeral disclosure grants; canonical retrieval/generation remain in QH-13."""
from dataclasses import asdict, dataclass
import hashlib
import json
from uuid import uuid4

from app.chat.context import BuiltContext, ChatInputInvalid, ChatContextUnavailable, ChatProviderUnavailable
from app.chat.models import ChatRequest
from app.chat.services import ProviderSessionFactory, ProviderSessionBinding
from app.core.models import ContextSpaceNotFound


class SessionClosed(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatIdentity:
    subject_id: str
    expires_at: float
    credential_id: str
    verified_session_id: str | None = None
    work_expires_at: float | None = None


@dataclass
class Grant:
    id: str
    identity: ChatIdentity
    request: ChatRequest
    built: BuiltContext
    selection: str
    expires_at: float
    state: str = 'preview'
    binding: ProviderSessionBinding | None = None
    busy: bool = False


def packet_hash(built):
    return hashlib.sha256(json.dumps([asdict(m) for m in built.request.messages[:2]],
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ProviderSessions:
    def __init__(self, *, chat, factory: ProviderSessionFactory | None = None, clock, session_binding=False):
        self.session_binding = session_binding
        self.chat, self.factory, self.clock = chat, factory, clock
        self.grants = {}

    async def capabilities(self, request):
        await self.chat._authorize(request)
        enabled = self.factory is not None and await self.factory.available(request.subject_id, request.context_id)
        return dict(enabled=enabled, model=self.factory.model if enabled else None,
                    max_seconds=1800 if self.session_binding else 300, max_calls=self.factory.max_calls if enabled else 3,
                    max_usd=self.factory.max_usd if enabled else '0.01',
                    provider_expires_at=self.factory.expires_at if enabled else None,
                    **({k: v for k, v in self.factory.remaining().items() if k != 'blocked'} if enabled
                       else dict(remaining_calls=0, remaining_usd='0')))

    def _prune(self):
        for key, grant in list(self.grants.items()):
            if grant.expires_at <= self.clock() and not grant.busy:
                del self.grants[key]
        if len(self.grants) >= 1000:
            raise SessionClosed('Session capacity unavailable')

    async def preview(self, identity, request):
        if identity.subject_id != request.subject_id:
            raise ContextSpaceNotFound('Context space not found')
        caps = await self.capabilities(request)
        if not caps['enabled'] or identity.expires_at <= self.clock():
            raise SessionClosed('Real provider unavailable')
        if self.session_binding and (not identity.verified_session_id or identity.work_expires_at is None or identity.work_expires_at <= self.clock()):
            raise SessionClosed('Verified OIDC work session required')
        self._prune()
        built, selection = await self.chat.prepare(request)
        if not self.factory.accepts_snapshot(request.subject_id, request.context_id, packet_hash(built)):
            raise SessionClosed('Context outside the authorized snapshot')
        if not built.revisions:
            raise ChatInputInvalid('No eligible context; explicit proposal choice may be needed')
        grant = Grant(str(uuid4()), identity, request, built, selection,
                      min(self.clock() + (1800 if self.session_binding else 300),
                          identity.work_expires_at if self.session_binding else identity.expires_at, self.factory.expires_at))
        self.grants[grant.id] = grant
        return self.describe(grant)

    async def _get(self, identity, request, grant_id, *, revoke=False):
        if identity.subject_id != request.subject_id:
            raise ContextSpaceNotFound('Context space not found')
        await self.chat._authorize(request)
        grant = self.grants.get(grant_id)
        if (grant is None or identity.subject_id != grant.identity.subject_id
                or request.context_id != grant.request.context_id):
            raise ContextSpaceNotFound('Context space not found')
        same_session = (bool(identity.verified_session_id) and identity.verified_session_id == grant.identity.verified_session_id
                        and identity.work_expires_at is not None and self.clock() < identity.work_expires_at) if self.session_binding else identity.credential_id == grant.identity.credential_id
        if not revoke and (not same_session
                or self.clock() >= min(grant.expires_at, identity.expires_at)
                or self.factory is None or not await self.factory.verified(identity.subject_id, request.context_id)):
            grant.state = 'closed'
            raise SessionClosed('Session expired or unavailable')
        return grant

    def describe(self, grant):
        accounting = grant.binding.summary() if grant.binding else dict(calls=0, committed_usd='0', blocked=False)
        return dict(session_id=grant.id, context_id=grant.request.context_id,
                    model=self.factory.model, state=grant.state, expires_at=grant.expires_at,
                    include_proposed=grant.request.include_proposed,
                    snapshot_sha256=packet_hash(grant.built), max_calls=self.factory.max_calls, max_usd=self.factory.max_usd,
                    accounting=accounting,
                    provided_revisions=tuple(asdict(r) for r in grant.built.revisions),
                    provider_messages=tuple(asdict(m) for m in grant.built.request.messages),
                    partial_coverage=grant.built.partial, input_bound=grant.built.input_bound,
                    context_bytes=grant.built.context_bytes)

    async def consent(self, identity, request, grant_id, *, snapshot_sha256, consent):
        grant = await self._get(identity, request, grant_id)
        if grant.state != 'preview' or consent is not True or snapshot_sha256 != packet_hash(grant.built):
            raise ChatInputInvalid('Exact preview and explicit disclosure consent required')
        built, selection = await self.chat.prepare(grant.request)
        if selection != grant.selection or packet_hash(built) != packet_hash(grant.built):
            grant.state = 'closed'
            raise ChatContextUnavailable('Context changed; new consent required')
        # No await from final validity check through binding/state transition.
        await self._get(identity, request, grant_id)
        if grant.state != 'preview':
            raise SessionClosed('Preview no longer available')
        grant.binding = self.factory.bind(grant.identity.verified_session_id if self.session_binding else grant.id, max_calls=self.factory.max_calls, max_usd=self.factory.max_usd)
        grant.state = 'active'
        return self.describe(grant)

    async def status(self, identity, request, grant_id):
        grant = await self._get(identity, request, grant_id)
        built, selection = await self.chat.prepare(grant.request)
        if selection != grant.selection or packet_hash(built) != packet_hash(grant.built):
            grant.state = 'closed'
            raise ChatContextUnavailable('Context changed; new consent required')
        await self._get(identity, request, grant_id)
        return self.describe(grant)

    async def revoke(self, identity, request, grant_id):
        grant = await self._get(identity, request, grant_id, revoke=True)
        grant.state = 'revoked'
        return dict(session_id=grant.id, state='revoked')

    async def respond(self, identity, request, grant_id):
        grant = await self._get(identity, request, grant_id)
        if grant.state != 'active' or grant.busy or request.include_proposed != grant.request.include_proposed:
            raise SessionClosed('Active matching session required')
        grant.busy = True
        owner = self

        class GuardedProvider:
            async def generate(self, generated):
                await owner._get(identity, request, grant_id)
                if grant.state != 'active' or generated.messages[:2] != grant.built.request.messages[:2]:
                    raise SessionClosed('Context changed or session revoked')
                # The same verified selection must hold even for rows outside the sent budget.
                from app.chat.implementation import fingerprint
                if fingerprint(await owner.chat._collect(request)) != grant.selection:
                    raise ChatContextUnavailable('Context changed')
                await owner._get(identity, request, grant_id)
                if grant.state != 'active':
                    raise SessionClosed('Session revoked')
                return await grant.binding.provider.generate(generated)

        try:
            result = await self.chat.respond(request, provider=GuardedProvider(), model=self.factory.model)
            await self._get(identity, request, grant_id)
            if grant.state != 'active':
                raise SessionClosed('Session revoked')
            return result
        except Exception:
            if grant.state != 'revoked':
                grant.state = 'closed'
            raise ChatProviderUnavailable('Provider session stopped; no automatic retry') from None
        finally:
            grant.busy = False
