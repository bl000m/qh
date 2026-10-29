"""Offline schema gate: PDF storage is additive; unknown versions still fail closed."""
from unittest.mock import Mock

import pytest

from adapters.context.runtime import NativeRuntime


@pytest.mark.parametrize('revision',['0010_context_consolidation','0011_source_documents','unknown_future_schema'])
def test_native_runtime_pdf_schema_gate(revision):
    runtime=NativeRuntime(url=Mock(),driver=Mock(),policy=Mock(),namespace='offline-schema-gate')
    connection=Mock()
    connection.execute.return_value.fetchone.return_value={'version_num':revision}
    manager=Mock()
    manager.__enter__=Mock(return_value=connection)
    manager.__exit__=Mock(return_value=False)
    runtime.repository=Mock(return_value=Mock(connect=Mock(return_value=manager)))
    runtime.projector=Mock()
    runtime._run=Mock()
    if revision=='unknown_future_schema':
        with pytest.raises(RuntimeError,match='requires migration 0004'):
            runtime.start()
        runtime.driver.verify_connectivity.assert_not_called()
        runtime.projector.initialize.assert_not_called()
        assert runtime.thread is None
        return
    try:
        runtime.start()
        runtime.driver.verify_connectivity.assert_called_once()
        runtime.projector.initialize.assert_called_once()
        assert runtime.schema_version==revision
    finally:
        runtime.stop()


@pytest.mark.parametrize('revision',['0011_source_documents','unknown_future_schema'])
def test_sharing_bootstrap_pdf_schema_gate(monkeypatch,revision):
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.bootstrap import create_runtime_app
    from adapters.sharing import SharingSettings

    for key,value in dict(POSTGRES_HOST='offline',POSTGRES_PORT='5432',POSTGRES_USER='offline',
        POSTGRES_PASSWORD='offline',POSTGRES_DB='offline',QH_NATIVE_CONTEXT_ENABLED='true',
        QH_NATIVE_GRAPH_NAMESPACE='offline',NEO4J_URI='bolt://offline:7687',
        NEO4J_USER='offline',NEO4J_PASSWORD='offline').items():
        monkeypatch.setenv(key,value)
    runtime=Mock(schema_version=revision)
    settings=SharingSettings(origin='https://qh.example.test',verifier_key=b'x'*32)
    with patch('adapters.context.runtime.NativeRuntime',return_value=runtime), \
         patch('neo4j.GraphDatabase.driver'), \
         patch('adapters.sharing.bind_sharing',side_effect=lambda services,*args,**kwargs:services) as bind:
        app=create_runtime_app(guest_settings=settings)
        if revision=='unknown_future_schema':
            with pytest.raises(RuntimeError,match='require reviewed schema'):
                with TestClient(app):
                    pass
            bind.assert_not_called()
            runtime.stop.assert_called_once()
        else:
            with TestClient(app) as client:
                assert client.get('/health').status_code==200
            bind.assert_called_once()
