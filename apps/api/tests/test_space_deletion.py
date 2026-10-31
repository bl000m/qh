"""Owner HTTP boundary and partial-failure receipts; no infrastructure or provider."""
from dataclasses import replace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.context.deletion import SpaceDeletion
from app.core.spaces import SpaceConfirmationMismatch
from app.core.models import ContextStorageUnavailable
from app.policy.owner import OwnerPolicyService
from tests.test_sharing_simplified import setup


def test_owner_confirmation_guest_denial_and_no_success_on_partial_failure():
    app,owner,scope,_,_,provider,_,_=setup()
    repository=Mock(prepare=AsyncMock(return_value=False),complete=AsyncMock())
    policy=OwnerPolicyService(owner_for=AsyncMock(return_value=owner))
    deletion=SpaceDeletion(repository=repository,policy=policy,purge_graph=Mock())
    app.state.services=replace(app.state.services,space_deletion=deletion)
    path='/context-spaces/'+scope
    with TestClient(app) as client:
        assert client.request('DELETE',path,json={'name':'Space'}).status_code==401
        repository.prepare.assert_not_awaited()
        policy._deletion_owner_for.return_value=str(uuid4())
        headers={'Authorization':'Bearer owner'}
        assert client.request('DELETE',path,json={'name':'Space'},headers=headers).status_code==404
        repository.prepare.assert_not_awaited()
        policy._deletion_owner_for.return_value=owner
        repository.prepare.side_effect=SpaceConfirmationMismatch()
        assert client.request('DELETE',path,json={'name':'wrong'},headers=headers).status_code==409
        repository.complete.assert_not_awaited()
        repository.prepare.side_effect=None
        repository.complete.side_effect=ContextStorageUnavailable()
        assert client.request('DELETE',path,json={'name':'Space'},headers=headers).status_code==503
        repository.complete.side_effect=None
        assert client.request('DELETE',path,json={'name':'Space'},headers=headers).status_code==204
        repository.complete.assert_awaited_with(owner,scope,deletion.purge_graph,deletion.purge_private)
    provider.generate.assert_not_awaited()
