"""Saved real provider responses, replayed without external calls."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from graphiti_core.nodes import EntityNode, EpisodicNode
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.utils.maintenance.edge_operations import extract_edges
from graphiti_core.prompts.extract_edges import ExtractedEdges
from graphiti_core.prompts.models import Message

from adapters.context.factory import create_graphiti_engine
from adapters.context.graphiti import ContextEngineError, GraphitiContextEngine
from adapters.context.quality import ExtractionQualityError, ExtractionSession, SourceEvidence, active_extraction
from adapters.context.smoke_quality import SmokeFixture
from app.core.models import ContextId, SourceId, SourceRevisionId, SourceRevisionRef

PAYLOADS = json.loads((Path(__file__).parent / "fixtures/qh7_semantic_responses.json").read_text())
NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)
SOURCE = "Bea founded Cedar Observatory."
FIXTURE = SmokeFixture(SOURCE, frozenset({"Bea", "Cedar Observatory"}))


def test_missing_expected_entity_is_fixture_only():
    session = ExtractionSession(SourceEvidence(SOURCE, NOW))
    session.validate("extract_nodes.extract_text", deepcopy(PAYLOADS["4"]))
    assert session.entities == {"Cedar Observatory"}  # A one-entity source is legal in production.
    guarded = ExtractionSession(SourceEvidence(SOURCE, NOW), FIXTURE.validate)
    with pytest.raises(ExtractionQualityError):
        guarded.validate("extract_nodes.extract_text", deepcopy(PAYLOADS["4"]))
    with pytest.raises(ExtractionQualityError):
        guarded.check()


def test_real_bad_edge_is_rejected_before_graphiti_silent_filter(monkeypatch):
    async def scenario():
        for key,value in {"MISTRAL_API_KEY":"synthetic-test-key", "MISTRAL_LLM_MODEL":"test-model",
                          "MISTRAL_EMBEDDING_MODEL":"mistral-embed", "NEO4J_URI":"bolt://localhost:7687",
                          "NEO4J_USER":"neo4j", "NEO4J_PASSWORD":"synthetic-password"}.items():
            monkeypatch.setenv(key,value)
        adapter,sdk = await create_graphiti_engine()
        llm = adapter.client.llm_client
        llm._generate_response = AsyncMock(return_value=deepcopy(PAYLOADS["5"]))
        session = ExtractionSession(SourceEvidence(SOURCE,NOW))
        session.validate("extract_nodes.extract_text",deepcopy(PAYLOADS["4"]))
        token = active_extraction.set(session)
        try:
            episode = EpisodicNode(name="test",group_id="test",source="text",source_description="test",
                                   content=SOURCE,created_at=NOW,valid_at=NOW)
            node = EntityNode(name="Cedar Observatory",group_id="test",summary="",created_at=NOW)
            with pytest.raises(ExtractionQualityError,match="unavailable"):
                await extract_edges(adapter.client.clients,episode,[node],[],{('Entity','Entity'):[]},"test",None)
            assert llm._generate_response.await_count == 1
            # Even if Graphiti catches the failure, no subsequent LLM/embedder stage can send.
            with pytest.raises(ExtractionQualityError):
                await llm.generate_response([Message(role="user",content="next")], response_model=ExtractedEdges)
            with pytest.raises(ExtractionQualityError):
                await adapter.client.embedder.create(["next"])
            assert llm._generate_response.await_count == 1
        finally:
            active_extraction.reset(token)
            await adapter.close(); await sdk.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("number", ["2", "5", "6"])
def test_real_unsupported_dates_are_rejected_by_undated_fixture(number):
    answer = deepcopy(PAYLOADS[number]); original = deepcopy(answer)
    with pytest.raises(ExtractionQualityError):
        FIXTURE.validate(SourceEvidence(SOURCE,NOW),"saved",answer)
    assert answer == original  # Reject, never silently repair or strip dates.


def test_production_accepts_legitimate_relative_or_explicit_time():
    session = ExtractionSession(SourceEvidence("Bea founded Cedar Observatory last year.",NOW))
    session.entities = {"Bea", "Cedar Observatory"}
    answer = deepcopy(PAYLOADS["5"])
    answer['edges'][0]['valid_at'] = "2025-10-15T00:00:00Z"
    session.validate("extract_edges.edge",answer)
    # Technical and semantic timestamps may legitimately coincide when the source supports it.
    explicit = ExtractionSession(SourceEvidence("Bea founded Cedar Observatory at 2026-10-15T00:00:00Z.", NOW))
    explicit.entities = {"Bea", "Cedar Observatory"}
    answer['edges'][0]['valid_at'] = NOW.isoformat()
    explicit.validate("extract_edges.edge", answer)
    dated = ExtractionSession(SourceEvidence("Cedar Observatory was founded by Bea in 2023.", NOW))
    dated.validate("extract_nodes.extract_summaries_batch",deepcopy(PAYLOADS["6"]))


@pytest.mark.parametrize("value", ["not-a-date", "2026-02-30T00:00:00Z", "2026-10-15T00:00:00"])
def test_adapter_rejects_structurally_invalid_semantic_time(value):
    session = ExtractionSession(SourceEvidence(SOURCE,NOW)); session.entities={"Bea","Cedar Observatory"}
    answer = deepcopy(PAYLOADS["5"]);answer['edges'][0]['valid_at']=value
    with pytest.raises(ExtractionQualityError):
        session.validate("extract_edges.edge",answer)


def test_valid_fixture_and_technical_time_stay_separate():
    entities = {"extracted_entities":[{"name":"Bea"},{"name":"Cedar Observatory"}]}
    answer = deepcopy(PAYLOADS["5"]);answer['edges'][0]['valid_at']=None
    session = ExtractionSession(SourceEvidence(SOURCE,NOW),FIXTURE.validate)
    session.validate("extract_nodes.extract_text",entities)
    session.validate("extract_edges.edge",answer)
    assert session.evidence.reference_time == NOW
    assert answer['edges'][0]['valid_at'] is None


def test_swallowed_failure_cannot_become_success(monkeypatch):
    monkeypatch.setattr(EpisodicNode,"get_by_uuid",AsyncMock(side_effect=NodeNotFoundError('test')))
    monkeypatch.setattr(EpisodicNode,"save",AsyncMock())
    async def swallowed(**kwargs):
        session=active_extraction.get()
        try:
            session.validate("extract_nodes.extract_text",deepcopy(PAYLOADS["4"]))
        except ExtractionQualityError:
            pass  # Reproduce optional upstream stages swallowing ordinary exceptions.
    client=SimpleNamespace(driver=object(),add_episode=swallowed)
    engine=GraphitiContextEngine(client,quality_observer=FIXTURE.validate)
    with pytest.raises(ContextEngineError):
        asyncio.run(engine.ingest_source(context_id=ContextId('test'),
            source=SourceRevisionRef(source_id=SourceId('source'),revision_id=SourceRevisionId('revision')),
            text=SOURCE,reference_time=NOW))
    assert active_extraction.get() is None


def test_sessions_do_not_leak_between_concurrent_local_tasks():
    async def worker(name):
        session=ExtractionSession(SourceEvidence(name,NOW))
        token=active_extraction.set(session)
        try:
            await asyncio.sleep(0)
            assert active_extraction.get().evidence.text == name
        finally:
            active_extraction.reset(token)
    async def scenario():
        await asyncio.gather(worker('first'),worker('second'))
    asyncio.run(scenario())


def test_smoke_b_refuses_without_new_experiment_authorization(monkeypatch):
    from adapters.context import smoke_b
    monkeypatch.setattr('sys.argv',['smoke_b','--ledger','/tmp/unused-qh7-ledger.json'])
    with pytest.raises(SystemExit) as error:
        smoke_b.main()
    assert error.value.code == 2


def test_smoke_b_limits_deny_before_network(tmp_path):
    import httpx
    from adapters.context.smoke_b import ExperimentTransport, ExperimentStopped, MAX_REQUESTS, BUDGET_USD
    async def scenario():
        def never_send(request):
            raise AssertionError('Network should never be reached')
        for exhausted in ('count','budget'):
            guard=ExperimentTransport(tmp_path/(exhausted+'.json'),inner=httpx.MockTransport(never_send))
            if exhausted=='count':
                guard.records=[{}]*MAX_REQUESTS
            else:
                guard.cost=BUDGET_USD
            with pytest.raises(ExperimentStopped):
                await guard.handle_async_request(httpx.Request('POST','https://api.mistral.ai/v1/embeddings',
                    json={'model':'mistral-embed','input':['Bea']}))
            await guard.aclose()
    asyncio.run(scenario())


def test_smoke_fixture_refuses_missing_or_changed_relation():
    from adapters.context.smoke_b import FIXTURE as fixture
    for answer in ({'edges':[]},{'edges':[{'fact':'Bea owns Cedar Observatory'}]}):
        with pytest.raises(ExtractionQualityError):
            fixture.validate(SourceEvidence(SOURCE,NOW),'extract_edges.edge',answer)


def test_b_runner_failure_has_nonzero_exit_and_no_followup(monkeypatch,tmp_path):
    import httpx
    from adapters.context import smoke_b
    monkeypatch.setenv('MISTRAL_LLM_MODEL','offline')
    monkeypatch.setenv('MISTRAL_EMBEDDING_MODEL','mistral-embed')
    client=SimpleNamespace(_transport=SimpleNamespace(inner=httpx.MockTransport(lambda r: None)))
    sdk=SimpleNamespace(_client=client,close=AsyncMock())
    adapter=SimpleNamespace(initialize=AsyncMock(),ingest_source=AsyncMock(side_effect=ContextEngineError('test')),
                            search=AsyncMock(),close=AsyncMock())
    monkeypatch.setattr(smoke_b,'create_graphiti_engine',AsyncMock(return_value=(adapter,sdk)))
    async def scenario():
        try:
            with pytest.raises(SystemExit) as error:
                await smoke_b.run(tmp_path/'experiment.json')
            assert error.value.code==1
            adapter.search.assert_not_awaited()
            saved = json.loads((tmp_path/'experiment.json').read_text())
            assert saved['requests']==[]
            assert saved['metadata']['ingestion_status'] == 'failed'
            assert saved['diagnostic']['category'] == 'graphiti_internal'
            assert saved['stopped'] is True
        finally:
            await client._transport.inner.aclose()
    asyncio.run(scenario())


def test_b_experiment_accounts_success_and_stops_after_http_error(tmp_path):
    import httpx
    from adapters.context.smoke_b import ExperimentTransport, ExperimentStopped
    async def scenario():
        sent=[]
        def reply(request):
            sent.append(request)
            if len(sent)==2:
                return httpx.Response(429,json={'message':'synthetic failure'})
            return httpx.Response(200,json={'data':[{'index':0,'embedding':[0.01]*1024}],
                                            'usage':{'prompt_tokens':4,'completion_tokens':0}})
        guard=ExperimentTransport(tmp_path/'usage.json',inner=httpx.MockTransport(reply))
        request=httpx.Request('POST','https://api.mistral.ai/v1/embeddings',
                             json={'model':'mistral-embed','input':['synthetic']})
        try:
            response=await guard.handle_async_request(request)
            await response.aclose()
            assert len(guard.records)==1 and guard.cost==pytest.approx(0.0000004)
            with pytest.raises(ExperimentStopped):
                await guard.handle_async_request(request)
            with pytest.raises(ExperimentStopped):
                await guard.handle_async_request(request)
            assert len(sent)==2 and len(guard.records)==2  # Failed attempt counted; never retried.
        finally:
            await guard.aclose()
    asyncio.run(scenario())
