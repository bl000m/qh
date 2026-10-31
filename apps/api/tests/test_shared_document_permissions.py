"""Focused HTTP/repository permission replay; SQL transport is an offline double."""
from dataclasses import replace
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.postgres.guest import PostgresGuestRepository
from app.api.guest import COOKIE
from tests.test_sharing_simplified import setup


def test_originals_empty_two_of_three_expiry_and_revocation_without_provider():
    app,_,_,_,now,provider,_,_=setup()
    service=app.state.services.guest
    grant=replace(service.repository.authenticate.return_value,rights=('READ','ASK_AI'))
    service.repository.authenticate.return_value=grant
    app.state.services.policy._guest_for.return_value=grant
    docs=[dict(source_revision_id=str(uuid4()),filename=f'synthetic-{i}.pdf') for i in range(3)]
    allowed=[]
    connection=Mock()

    def execute(query,values):
        if 'SELECT policy' in query:
            assert values==(grant.snapshot_id,grant.context_id)
            return Mock(fetchone=lambda:dict(policy=dict(original_documents=list(allowed))))
        assert values[0]==grant.context_id and set(values[1])<=set(allowed)
        rows=[doc for doc in docs if doc['source_revision_id'] in values[1]]
        if 'original' in query and 'SELECT filename' in query:
            rows=[dict(filename=doc['filename'],media_type='application/pdf',original=b'%PDF-synthetic') for doc in rows]
        return Mock(fetchall=lambda:rows)

    connection.execute.side_effect=execute
    repository=PostgresGuestRepository(url='offline-only')
    repository._run=lambda subject,operation:operation(None,connection,now[0])
    repository._active=Mock(return_value=grant)
    service.repository.documents=repository.documents
    with TestClient(app,base_url='https://qh.example.test',headers={'Origin':'https://qh.example.test'}) as client:
        assert client.get('/guest/documents').status_code==401
        client.cookies.set(COOKIE,'synthetic-verified-cookie')
        assert client.get('/guest/documents').json()==[]
        assert client.get('/guest/documents/'+docs[0]['source_revision_id']).status_code==401
        allowed[:]=[docs[0]['source_revision_id'],docs[2]['source_revision_id']]
        assert client.get('/guest/documents').json()==[docs[0],docs[2]]
        for doc in (docs[0],docs[2]):
            response=client.get('/guest/documents/'+doc['source_revision_id'])
            assert response.status_code==200 and response.content==b'%PDF-synthetic'
            assert response.headers['cache-control']=='private, no-store'
        assert client.get('/guest/documents/'+docs[1]['source_revision_id']).status_code==401
        now[0]+=timedelta(hours=2)
        assert client.get('/guest/documents').status_code==401
        assert client.get('/guest/documents/'+allowed[0]).status_code==401
        now[0]-=timedelta(hours=2)
        service.repository.authenticate.return_value=None
        assert client.get('/guest/documents').status_code==401
        assert client.get('/guest/documents/'+allowed[0]).status_code==401
    provider.generate.assert_not_awaited()


@pytest.mark.parametrize('scope_mode',[None,'context'])
def test_guest_frozen_knowledge_scope_never_expands_legacy_approvals(monkeypatch,scope_mode):
    import asyncio
    import json
    from app.projections.document_scope import restrict_snapshot
    from tests.test_guest_references import PAYLOAD
    app,_,_,_,now,_,_,_=setup()
    grant=replace(app.state.services.guest.repository.authenticate.return_value,rights=('READ','ASK_AI'))
    docs=[str(uuid4()),str(uuid4())]
    policy=dict(original_documents=[],semantic_documents=[])
    if scope_mode:policy['knowledge_scope']=scope_mode
    payload=dict(PAYLOAD)
    connection=Mock()
    report=dict(document_scope_version=3 if scope_mode else 2)
    def execute(query,params):
        if 'SELECT id,context_space_id,payload,policy' in query:
            return Mock(fetchone=lambda:dict(id=grant.snapshot_id,context_space_id=grant.context_id,payload=payload,policy=policy))
        if 'SELECT a.reference' in query:
            return Mock(fetchall=lambda:[dict(reference=f'R{i+1}',sources=[d]) for i,d in enumerate(docs)])
        if 'SELECT p.report' in query:return Mock(fetchone=lambda:dict(report=report))
        raise AssertionError('Unexpected query')
    connection.execute.side_effect=execute
    metadata=Mock(return_value=docs)
    monkeypatch.setattr('adapters.postgres.guest.document_source_ids',metadata)
    repository=PostgresGuestRepository(url='offline-only')
    repository._run=lambda subject,operation:operation(None,connection,now[0])
    repository._active=Mock(return_value=grant)
    result=asyncio.run(repository.payload(grant,'READ'))
    visible=json.loads(result.payload_json)
    if scope_mode:
        assert visible==restrict_snapshot(payload,{'R1','R2'},verified_recap=True)
        metadata.assert_not_called()  # No live document/source hydration for unified snapshots.
        report['document_scope_version']=2
        from app.projections.guest import GuestDenied
        with pytest.raises(GuestDenied):asyncio.run(repository.payload(grant,'READ'))
    else:
        assert visible.get('notice') and not visible.get('recap')
        assert payload['items']==PAYLOAD['items']  # The old frozen payload is not rewritten.
