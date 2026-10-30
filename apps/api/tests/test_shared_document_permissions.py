"""Focused HTTP/repository permission replay; SQL transport is an offline double."""
from dataclasses import replace
from datetime import timedelta
from unittest.mock import Mock
from uuid import uuid4

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
