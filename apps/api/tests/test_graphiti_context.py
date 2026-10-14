"""Offline adapter and per-request billing checks; never use provider credentials."""

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from adapters.context.billing import ApprovedTransport, ExternalCallDenied
from adapters.context.graphiti import ContextEngineError, GraphitiContextEngine, episode_id, group_id
from app.core.models import ContextId, ContextQuery, SourceId, SourceRevisionId, SourceRevisionRef
from app.core.ports import ContextEngine

SPACE = ContextId("space-a")
SOURCE = SourceRevisionRef(source_id=SourceId("source-a"), revision_id=SourceRevisionId("rev-a"))


def run(coro):
    return asyncio.run(coro)


def episode():
    return SimpleNamespace(uuid=episode_id(SPACE, SOURCE), group_id=group_id(SPACE),
        source_description=json.dumps({"qh_source_revision_v1": {
            "context_id": SPACE, "source_id": SOURCE.source_id, "revision_id": SOURCE.revision_id}}))


def engine():
    ep = episode()
    edge = SimpleNamespace(uuid="edge-a", group_id=group_id(SPACE), fact="Ada founded Cedar.",
                           episodes=[ep.uuid])
    client = SimpleNamespace(search_=AsyncMock(return_value=SimpleNamespace(edges=[edge])),
        add_episode=AsyncMock(), build_indices_and_constraints=AsyncMock(), close=AsyncMock())
    loader = AsyncMock(return_value=[ep])
    return GraphitiContextEngine(client, episode_loader=loader), edge, ep


def test_ingest_and_normalize_with_fresh_adapter():
    adapter, edge, ep = engine()
    assert isinstance(adapter, ContextEngine)
    assert run(adapter.ingest_source(context_id=SPACE, source=SOURCE, text="Ada founded Cedar.",
        reference_time=datetime.now(timezone.utc))) == ep.uuid
    args = adapter.client.add_episode.call_args.kwargs
    assert args["group_id"] == group_id(SPACE)
    assert args["previous_episode_uuids"] == []
    fresh = GraphitiContextEngine(adapter.client, episode_loader=adapter.episode_loader)
    result = run(fresh.search(ContextQuery(text="Who founded Cedar?", context_ids=(SPACE,), limit=3)))
    assert result.hits[0].provenance == (SOURCE,)
    assert result.hits[0].context_id == SPACE
    assert result.hits[0].item_revision is None
    assert result.hits[0].excerpt == edge.fact
    assert adapter.client.search_.call_args.kwargs["group_ids"] == [group_id(SPACE)]
    assert adapter.client.search_.call_args.kwargs["config"].limit == 3


def test_scopes_and_initialization():
    adapter, _, _ = engine()
    other = ContextId("space-b")
    assert group_id(SPACE) == group_id(SPACE) != group_id(other)
    run(adapter.initialize())
    adapter.client.build_indices_and_constraints.assert_awaited_once_with(delete_existing=False)
    with pytest.raises(ValueError):
        group_id(ContextId(""))


@pytest.mark.parametrize("corruption", ["edge_scope", "episode_scope", "missing", "bad_ref", "no_sources"])
def test_rejects_unverifiable_or_cross_space_hits(corruption):
    adapter, edge, ep = engine()
    if corruption == "edge_scope":
        edge.group_id = group_id(ContextId("space-b"))
    elif corruption == "episode_scope":
        ep.group_id = group_id(ContextId("space-b"))
    elif corruption == "missing":
        adapter.episode_loader.return_value = []
    elif corruption == "bad_ref":
        ep.source_description = "{}"
    else:
        edge.episodes = []
    with pytest.raises(ContextEngineError):
        run(adapter.search(ContextQuery(text="Cedar", context_ids=(SPACE,))))


def test_two_requested_spaces_use_explicit_scopes():
    adapter, _, _ = engine()
    run(adapter.search(ContextQuery(text="Cedar", context_ids=(SPACE, ContextId("space-b")))))
    assert adapter.client.search_.call_args.kwargs["group_ids"] == [group_id(SPACE), group_id(ContextId("space-b"))]


def test_billing_denies_by_default_and_approves_only_one_attempt():
    async def scenario():
        sent = []
        decisions = iter([True, False])
        seen = []
        async def approve(description):
            seen.append(description)
            return next(decisions)
        def handler(request):
            sent.append(request)
            return httpx.Response(200, json={"ok": True})
        for approval in (None, approve):
            kwargs = {"approval": approval} if approval else {}
            transport = ApprovedTransport(model="test-model", embedding_model="mistral-embed",
                inner=httpx.MockTransport(handler), **kwargs)
            async with httpx.AsyncClient(transport=transport) as client:
                if approval:
                    await client.post("https://api.mistral.ai/v1/chat/completions",
                                      json={"model": "test-model", "messages": []})
                with pytest.raises(ExternalCallDenied):
                    await client.post("https://api.mistral.ai/v1/chat/completions",
                                      json={"model": "test-model", "messages": []})
        assert len(sent) == 1 and len(seen) == 2
        assert seen[0].provider == "Mistral Cloud"
        assert seen[0].endpoint.endswith("/chat/completions")
        assert seen[0].payload_sha256 == seen[1].payload_sha256
    run(scenario())


def test_unknown_endpoints_models_redirects_and_failure_never_retry():
    async def scenario():
        sent = []
        async def approve(description):
            return True
        def handler(request):
            sent.append(request)
            return httpx.Response(429, text="private error detail")
        async with httpx.AsyncClient(transport=ApprovedTransport(model="test-model",
            embedding_model="mistral-embed", approval=approve, inner=httpx.MockTransport(handler))) as client:
            for url, model in [("https://api.openai.com/v1/embeddings", "mistral-embed"),
                               ("https://api.mistral.ai/v1/embeddings", "other")]:
                with pytest.raises(ExternalCallDenied):
                    await client.post(url, json={"model": model})
            with pytest.raises(ExternalCallDenied, match="Embedding batches"):
                await client.post("https://api.mistral.ai/v1/embeddings",
                                  json={"model": "mistral-embed", "input": ["first", "second"]})
            with pytest.raises(RuntimeError, match="Provider rejected request"):
                await client.post("https://api.mistral.ai/v1/embeddings", json={"model": "mistral-embed", "input": "test"})
        assert len(sent) == 1
    run(scenario())


def test_factory_is_offline_with_explicit_clients(monkeypatch):
    from adapters.context.factory import create_graphiti_engine
    for key, value in {"MISTRAL_LLM_MODEL": "test-model", "MISTRAL_EMBEDDING_MODEL": "mistral-embed",
                       "MISTRAL_API_KEY": "synthetic-test-key", "NEO4J_URI": "bolt://localhost:7687",
                       "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "synthetic-password"}.items():
        monkeypatch.setenv(key, value)
    async def scenario():
        adapter, sdk = await create_graphiti_engine()
        try:
            assert adapter.client.driver._init_task is None
            assert sdk.max_retries == 0
            assert adapter.client.embedder.config.embedding_dim == 1024
            assert adapter.client.llm_client.model == "test-model"
            adapter.client.llm_client._generate_response = AsyncMock(side_effect=RuntimeError("test"))
            with pytest.raises(RuntimeError):
                await adapter.client.llm_client._generate_response_with_retry([])
            assert adapter.client.llm_client._generate_response.await_count == 1
            with pytest.raises(RuntimeError, match="Paid reranking is disabled"):
                await adapter.client.cross_encoder.rank("query", ["text"])
        finally:
            await adapter.close()
            await sdk.close()
    run(scenario())


def test_pinned_graphiti_mistral_wire_contract(monkeypatch):
    """Exercise real Graphiti + OpenAI SDK serialization against an in-memory HTTP peer."""
    from pydantic import BaseModel
    from graphiti_core.prompts.models import Message
    from adapters.context.factory import create_graphiti_engine

    class Extracted(BaseModel):
        fact: str

    for key, value in {"MISTRAL_LLM_MODEL": "mistral-small-latest",
                       "MISTRAL_EMBEDDING_MODEL": "mistral-embed",
                       "MISTRAL_API_KEY": "synthetic-test-key", "NEO4J_URI": "bolt://localhost:7687",
                       "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "synthetic-password"}.items():
        monkeypatch.setenv(key, value)

    async def scenario():
        requests = []
        descriptions = []
        async def approve(description):
            descriptions.append(description)
            return True
        def handler(request):
            data = json.loads(request.content)
            requests.append(data)
            if request.url.path.endswith("/chat/completions"):
                assert data["model"] == "mistral-small-latest"
                assert data["response_format"]["type"] == "json_schema"
                assert data["response_format"]["json_schema"]["schema"] == Extracted.model_json_schema()
                return httpx.Response(200, json={"id": "mock", "object": "chat.completion", "created": 0,
                    "model": data["model"], "choices": [{"index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": '{"fact":"Ada founded Cedar."}'}}]})
            assert data["model"] == "mistral-embed"
            assert data["input"] in (["Ada"], ["Cedar"])
            return httpx.Response(200, json={"object": "list", "model": data["model"], "data": [
                {"object": "embedding", "index": i, "embedding": [0.01] * 1024} for i in range(1)],
                "usage": {"prompt_tokens": 2, "total_tokens": 2}})
        adapter, sdk = await create_graphiti_engine(approval=approve)
        sdk._client._transport.inner = httpx.MockTransport(handler)
        try:
            result = await adapter.client.llm_client.generate_response(
                [Message(role="system", content="Extract facts."), Message(role="user", content="Ada founded Cedar.")],
                response_model=Extracted)
            assert result == {"fact": "Ada founded Cedar."}
            vectors = await adapter.client.embedder.create_batch(["Ada", "Cedar"])
            assert len(vectors) == 2 and all(len(vector) == 1024 for vector in vectors)
            assert len(descriptions) == len(requests) == 3
            assert all("synthetic-test-key" not in str(d) for d in descriptions)
        finally:
            await adapter.close()
            await sdk.close()
    run(scenario())
