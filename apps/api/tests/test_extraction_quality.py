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
    # No lexical year matching or generic 'metadata equals event time' heuristic.
    session.validate("extract_edges.edge",deepcopy(PAYLOADS["5"]))
    session.validate("extract_nodes.extract_summaries_batch",deepcopy(PAYLOADS["6"]))


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
