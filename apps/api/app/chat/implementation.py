"""QH-13 orchestration through existing contracts; no storage or adapter imports."""
from dataclasses import asdict
import hashlib
import json
from typing import Callable

from app.chat.context import (build_context, decode_answer, ChatContextUnavailable,
                              ChatInputInvalid, ChatProviderUnavailable)
from app.core.models import ProviderBudgetExceeded
from app.chat.models import ChatRequest, ChatResponse
from app.core.models import (ContextBrowse, ContextRequest, ContextSpaceNotFound,
                             Message, MessageRole)
from app.core.ports import LLMProvider
from app.core.services import ContextService
from app.policy.models import PolicyAction, PolicyRequest
from app.policy.services import PolicyService


def fingerprint(selection):
    rows, partial = selection
    return hashlib.sha256(json.dumps([list(map(asdict, rows)), partial],
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ContextualChatService:
    def __init__(self, *, context: ContextService, policy: PolicyService,
                 provider: LLMProvider, model: str, clock: Callable[[], float] | None = None):
        self.context, self.policy, self.provider, self.model = context, policy, provider, model
        self.clock = clock

    async def _authorize(self, request):
        decision = await self.policy.evaluate(PolicyRequest(subject_id=request.subject_id,
            action=PolicyAction.CHAT, context_ids=(request.context_id,)))
        if not decision.allowed:
            raise ContextSpaceNotFound('Context space not found')

    async def _collect(self, request):
        rows, partial = [], False
        for view in ('current', 'proposed') if request.include_proposed else ('current',):
            cursor = None
            for _ in range(2):
                page = await self.context.browse(ContextRequest(subject_id=request.subject_id,
                    query=ContextBrowse(context_id=request.context_id, view=view,
                                        limit=10, after_revision_id=cursor)))
                if len(page.revisions) > 10:
                    raise ChatContextUnavailable('Invalid retrieval page')
                for row in page.revisions:
                    if row.context_space_id != request.context_id or (
                        view == 'current' and (row.validation_state != 'confirmed' or not row.is_current_confirmed)
                    ) or (view == 'proposed' and row.validation_state != 'proposed'):
                        raise ChatContextUnavailable('Invalid retrieval visibility')
                if cursor and any(row.revision_id <= cursor for row in page.revisions):
                    raise ChatContextUnavailable('Invalid retrieval cursor')
                rows.extend(page.revisions)
                cursor = page.next_after_revision_id
                if cursor is None:
                    break
                if not page.revisions or cursor != page.revisions[-1].revision_id:
                    raise ChatContextUnavailable('Invalid retrieval cursor')
            partial |= cursor is not None
        if len({r.revision_id for r in rows}) != len(rows):
            raise ChatContextUnavailable('Duplicate retrieval revision')
        return tuple(rows), partial

    async def prepare(self, request: ChatRequest):
        if not request.context_id or request.context_query is not None:
            raise ChatInputInvalid('One explicit Space required')
        # Validate dialogue before any private read or provider invocation.
        build_context(context_id=request.context_id, revisions=(), messages=request.messages,
                      include_proposed=request.include_proposed)
        await self._authorize(request)
        selected = await self._collect(request)
        expected = fingerprint(selected)
        built = build_context(context_id=request.context_id, revisions=selected[0],
            messages=request.messages, include_proposed=request.include_proposed, partial=selected[1])
        if fingerprint(await self._collect(request)) != expected:
            raise ChatContextUnavailable('Context changed before generation')
        await self._authorize(request)  # Separate CHAT gate immediately before disclosure.
        return built, expected

    async def respond(self, request: ChatRequest, *, provider=None, model=None, allow_empty=False, observer=None) -> ChatResponse:
        built, expected = await self.prepare(request)
        if observer:
            observer("chat.pre_disclosure_policy_graph_selection", True)
        elapsed = None
        if not built.revisions and not allow_empty:
            answer, references, insufficient = 'Le contexte disponible est insuffisant pour répondre.', (), True
        else:
            started = self.clock() if self.clock else None
            try:
                generated = await (provider or self.provider).generate(built.request)
                answer, references, insufficient = decode_answer(generated.message, built, observer=observer)
            except ProviderBudgetExceeded:
                raise
            except Exception:
                # Never disclose provider bodies, prompts, URLs or credential-bearing errors.
                raise ChatProviderUnavailable('Chat provider unavailable') from None
            elapsed = self.clock() - started if self.clock and started is not None else None
        # No transaction spans generation. Reject changed selection, lost policy or graph trust.
        try:
            if fingerprint(await self._collect(request)) != expected:
                raise ChatContextUnavailable('Context changed during generation')
            await self._authorize(request)
        except Exception:
            if observer:
                observer('chat.post_generation_policy_graph_snapshot', False, 'Context changed, graph unavailable or CHAT denied')
            raise
        if observer:
            observer('chat.post_generation_policy_graph_snapshot', True)
        return ChatResponse(message=Message(role=MessageRole.ASSISTANT, content=answer),
            context_ids=(request.context_id,), model=model or self.model, references=references,
            provided_revisions=built.revisions, insufficient_context=insufficient,
            partial_coverage=built.partial, input_bound=built.input_bound,
            context_bytes=built.context_bytes, generation_seconds=elapsed)
