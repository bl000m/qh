"""Confirmed erasure, with durable revocation before any cross-store cleanup."""
from app.core.models import ContextSpaceNotFound
from app.policy.models import PolicyAction, PolicyRequest
from app.core.spaces import SpaceDeletionRepository


class SpaceDeletion:
    def __init__(self, *, repository: SpaceDeletionRepository, policy, purge_graph, purge_private=None):
        self.repository, self.policy, self.purge_graph = repository, policy, purge_graph
        self.purge_private = purge_private or (lambda owner, scope: None)

    async def delete(self, subject, scope, name):
        decision = await self.policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.DELETE_CONTEXT, context_ids=(scope,)))
        if not decision.allowed:
            raise ContextSpaceNotFound('Context space not found')
        complete = await self.repository.prepare(subject, scope, name)
        if not complete:
            await self.repository.complete(subject, scope, self.purge_graph, self.purge_private)
