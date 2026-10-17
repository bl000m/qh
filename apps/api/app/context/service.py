"""Authorize before metadata access; publication/retrieval remain separate work."""

from app.core.models import (ContextId, ContextRequest, ContextResult, ContextSpace,
                             ContextSpaceNotFound, ContextSpacePage, SubjectId,
                             ContextRetrievalUnavailable)
from app.core.spaces import ContextSpaceRepository
from app.policy.models import PolicyAction, PolicyRequest
from app.policy.services import PolicyService


def validate_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip() or len(name) > 256 or "\x00" in name:
        raise ValueError("Name must contain 1–256 characters and no NUL")
    return name


class ManagedContextService:
    def __init__(self, *, repository: ContextSpaceRepository, policy: PolicyService,
                 retrieval_for=None):
        self.repository, self.policy = repository, policy
        self.retrieval_for = retrieval_for

    async def _allow(self, subject_id, action, context_id=None):
        decision = await self.policy.evaluate(PolicyRequest(
            subject_id=subject_id, action=action,
            context_ids=() if context_id is None else (context_id,),
        ))
        if not decision.allowed:
            if context_id is not None:
                raise ContextSpaceNotFound("Context space not found")
            raise PermissionError("Access denied")

    async def create_space(self, *, subject_id: SubjectId, name: str) -> ContextSpace:
        await self._allow(subject_id, PolicyAction.CREATE_CONTEXT)
        name = validate_name(name)
        return await self.repository.create(subject_id=subject_id, name=name)

    async def list_spaces(self, *, subject_id: SubjectId, limit: int = 20,
                          after_id: ContextId | None = None) -> ContextSpacePage:
        await self._allow(subject_id, PolicyAction.LIST_CONTEXTS)
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        ids = await self.repository.list_ids(subject_id=subject_id, limit=limit + 1, after_id=after_id)
        items = tuple([await self.get_space(subject_id=subject_id, context_id=id) for id in ids[:limit]])
        return ContextSpacePage(items=items, next_after_id=items[-1].id if len(ids) > limit else None)

    async def get_space(self, *, subject_id: SubjectId, context_id: ContextId) -> ContextSpace:
        await self._allow(subject_id, PolicyAction.READ_CONTEXT, context_id)
        value = await self.repository.read(subject_id=subject_id, context_id=context_id)
        if value is None:
            raise ContextSpaceNotFound("Context space not found")
        return value

    async def rename_space(self, *, subject_id: SubjectId, context_id: ContextId,
                           name: str) -> ContextSpace:
        await self._allow(subject_id, PolicyAction.UPDATE_CONTEXT, context_id)
        name = validate_name(name)
        value = await self.repository.rename(subject_id=subject_id, context_id=context_id,
                                              name=name)
        if value is None:
            raise ContextSpaceNotFound("Context space not found")
        return value

    async def retrieve(self, request: ContextRequest) -> ContextResult:
        decision = await self.policy.evaluate(PolicyRequest(
            subject_id=request.subject_id, action=PolicyAction.READ_CONTEXT,
            context_ids=request.query.context_ids,
        ))
        if not decision.allowed:
            raise ContextSpaceNotFound("Context space not found")
        if self.retrieval_for is None:
            raise ContextRetrievalUnavailable("Context retrieval unavailable")
        try:
            result = await self.retrieval_for(request.subject_id).retrieve(request)
        except PermissionError:
            raise ContextSpaceNotFound("Context space not found") from None
        if (any(h.context_id not in request.query.context_ids for h in result.hits)
                or any(r.context_space_id not in request.query.context_ids for r in result.revisions)):
            raise ContextRetrievalUnavailable("Context retrieval unavailable")
        # Recheck the shared resource policy before disclosure, even on empty pages.
        decision = await self.policy.evaluate(PolicyRequest(
            subject_id=request.subject_id, action=PolicyAction.READ_CONTEXT,
            context_ids=request.query.context_ids,
        ))
        if not decision.allowed:
            raise ContextSpaceNotFound("Context space not found")
        return result
