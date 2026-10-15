"""Error provenance through the real pinned SDK; all HTTP is mocked."""

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.nodes import EpisodicNode
from graphiti_core.prompts.extract_edges import ExtractedEdges
from graphiti_core.prompts.models import Message
from neo4j.exceptions import ServiceUnavailable

from adapters.context.diagnostics import describe_failure
from adapters.context.factory import create_graphiti_engine
from adapters.context.graphiti import ContextEngineError, GraphitiContextEngine
from adapters.context.quality import active_extraction
from adapters.context.smoke_b import ExperimentTransport
from app.core.models import ContextId, SourceId, SourceRevisionId, SourceRevisionRef

NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)
SOURCE = SourceRevisionRef(source_id=SourceId('synthetic-source'), revision_id=SourceRevisionId('r1'))


def ingest(engine):
    return engine.ingest_source(context_id=ContextId('synthetic-B'), source=SOURCE,
                               text='Bea founded Cedar Observatory.', reference_time=NOW)


@pytest.mark.parametrize('content,category,leaf', [
    ('{broken', 'llm_parsing', 'JSONDecodeError'),
    ('{}', 'llm_schema', 'ValidationError'),
    (json.dumps({'edges': [{'relation_type': 'FOUNDED', 'source_entity_name': 'Missing',
                           'target_entity_name': 'Cedar Observatory', 'fact': 'synthetic',
                           'valid_at': None, 'invalid_at': None, 'episode_indices': [0]}]}),
     'qh_consistency', 'ExtractionQualityError'),
])
def test_http_200_preserves_failure_and_synthetic_replay(monkeypatch, tmp_path, content, category, leaf):
    for name, value in {'MISTRAL_API_KEY': 'synthetic-key-never-record',
                        'MISTRAL_LLM_MODEL': 'ministral-8b-2512',
                        'MISTRAL_EMBEDDING_MODEL': 'mistral-embed',
                        'NEO4J_URI': 'bolt://localhost:7687', 'NEO4J_USER': 'neo4j',
                        'NEO4J_PASSWORD': 'synthetic-password'}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(EpisodicNode, 'get_by_uuid', AsyncMock(side_effect=NodeNotFoundError('test')))
    monkeypatch.setattr(EpisodicNode, 'save', AsyncMock())

    async def scenario():
        async def approve(_):
            return True
        adapter, sdk = await create_graphiti_engine(approval=approve)
        guard = ExperimentTransport(tmp_path/'checkpoint.json', capture_synthetic=True,
            inner=httpx.MockTransport(lambda request: httpx.Response(200,
                headers={'x-test-secret': 'must-not-record'}, json={
                    'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 10}})))
        await sdk._client._transport.inner.aclose()
        sdk._client._transport.inner = guard
        async def add_episode(**kwargs):
            active_extraction.get().entities = {'Bea', 'Cedar Observatory'}
            # Swallow the stage exception exactly like optional upstream operations.
            try:
                await adapter.client.llm_client.generate_response(
                    [Message(role='user', content='Bea founded Cedar Observatory.')],
                    response_model=ExtractedEdges, prompt_name='extract_edges.edge')
            except Exception:
                pass
        monkeypatch.setattr(adapter.client, 'add_episode', add_episode)
        try:
            with pytest.raises(ContextEngineError) as error:
                await ingest(adapter)
            diagnostic = error.value.diagnostic
            assert diagnostic.category == category
            assert diagnostic.phase == 'extract_edges.edge'
            assert leaf in diagnostic.exception_types
            assert error.value.__cause__ is not None
            saved = json.loads((tmp_path/'checkpoint.json').read_text())
            assert len(saved['requests']) == 1  # No retries, even with HTTP 200.
            row = saved['requests'][0]
            assert row['status'] == 200
            assert row['synthetic_response']['choices'][0]['message']['content'] == content
            assert row['phase'] == 'extract_edges.edge'
            assert row['synthetic_request']['response_format']
            assert 'synthetic-key-never-record' not in json.dumps(saved)
            assert 'must-not-record' not in json.dumps(saved)
            # Offline replay has the exact received content and request schema.
            if category == 'llm_parsing':
                with pytest.raises(json.JSONDecodeError):
                    json.loads(row['synthetic_response']['choices'][0]['message']['content'])
        finally:
            await adapter.close()
            await sdk.close()
    asyncio.run(scenario())


@pytest.mark.parametrize('failure,category,at_save', [
    (RuntimeError('private provider data'), 'graphiti_internal', False),
    (ServiceUnavailable('private database details'), 'neo4j_persistence', False),
    (ServiceUnavailable('private database details'), 'neo4j_persistence', True),
])
def test_internal_and_persistence_causes_are_distinct(monkeypatch, failure, category, at_save):
    monkeypatch.setattr(EpisodicNode, 'get_by_uuid', AsyncMock(side_effect=NodeNotFoundError('test')))
    monkeypatch.setattr(EpisodicNode, 'save', AsyncMock(side_effect=failure if at_save else None))
    client = SimpleNamespace(driver=object(), add_episode=AsyncMock(side_effect=failure))
    with pytest.raises(ContextEngineError) as error:
        asyncio.run(ingest(GraphitiContextEngine(client)))
    assert error.value.__cause__ is failure
    assert error.value.diagnostic.category == category
    assert 'private' not in json.dumps(error.value.diagnostic.as_dict())
    assert active_extraction.get() is None


def test_capture_is_off_by_default(tmp_path):
    async def scenario():
        guard = ExperimentTransport(tmp_path/'default.json', inner=httpx.MockTransport(lambda r:
            httpx.Response(200, json={'choices': [{'message': {'content': 'sensitive'}, 'finish_reason': 'stop'}],
                                    'usage': {'prompt_tokens': 1, 'completion_tokens': 1}})))
        try:
            await guard.handle_async_request(httpx.Request('POST', 'https://api.mistral.ai/v1/chat/completions',
                json={'model': 'ministral-8b-2512', 'max_tokens': 10, 'messages': [{'content': 'private'}]}))
            saved = (tmp_path/'default.json').read_text()
            assert 'sensitive' not in saved and 'private' not in saved
        finally:
            await guard.aclose()
    asyncio.run(scenario())


def test_diagnostic_does_not_serialize_exception_messages():
    result = describe_failure(RuntimeError('Authorization: Bearer private'), 'ingest')
    assert result.category == 'graphiti_internal'
    assert 'private' not in json.dumps(result.as_dict())


def test_non_llm_json_failure_is_not_mislabelled_as_provider_parsing():
    try:
        json.loads('{invalid-source-descriptor')
    except json.JSONDecodeError as error:
        assert describe_failure(error, 'search').category == 'graphiti_internal'
        assert describe_failure(error, 'extract_edges.edge', llm=True).category == 'llm_parsing'
