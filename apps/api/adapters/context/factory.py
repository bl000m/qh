"""Explicit opt-in Graphiti assembly; never imported by API startup."""

import asyncio
import os

import httpx
from openai import AsyncOpenAI

from adapters.context.billing import Approval, ApprovedTransport, deny_call
from adapters.context.quality import active_extraction
from adapters.context.diagnostics import StageError, describe_failure, llm_phase


async def create_graphiti_engine(*, approval: Approval = deny_call):
    # Set before constructing Graphiti; no provider or telemetry traffic on startup.
    os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
    from graphiti_core import Graphiti
    from graphiti_core.cross_encoder.client import CrossEncoderClient
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

    from adapters.context.graphiti import GraphitiContextEngine

    class NoRetryClient(OpenAIGenericClient):
        async def generate_response(self, *args, **kwargs):
            session = active_extraction.get()
            if session:
                session.check()
            phase = kwargs.get("prompt_name", "unknown")
            token = llm_phase.set(phase)
            try:
                answer = await super().generate_response(*args, **kwargs)
                response_model = kwargs.get("response_model")
                if response_model is not None:
                    response_model.model_validate(answer)
                if session:
                    session.validate(phase, answer)
                return answer
            except Exception as exc:
                diagnostic = describe_failure(exc, phase, llm=True)
                category = diagnostic.category
                if category == "graphiti_internal":
                    # Unknown SDK/upstream failures are not labelled schema errors.
                    category = "llm_internal"
                if category == "qh_consistency":
                    if session and session.cause is None:
                        session.cause = exc
                    raise
                failure = StageError(category, phase)
                if session and session.cause is None:
                    session.failure = "Extraction provider stage failed"
                    session.cause = failure
                raise failure from exc
            finally:
                llm_phase.reset(token)

        async def _generate_response_with_retry(self, *args, **kwargs):
            return await self._generate_response(*args, **kwargs)

    class SingleInputEmbedder(OpenAIEmbedder):
        async def create(self, input_data):
            session = active_extraction.get()
            if session:
                session.check()
            try:
                return await super().create(input_data)
            except Exception as exc:
                if session and session.failure is None:
                    session.failure = "Extraction embedding stage failed"
                    session.cause = exc
                raise

        async def create_batch(self, input_data_list):
            # One source string per request and separate approval, never a paid batch.
            return [await self.create([text]) for text in input_data_list]

    class DisabledReranker(CrossEncoderClient):
        async def rank(self, query, passages):
            raise RuntimeError("Paid reranking is disabled; use local RRF")

    model = os.environ["MISTRAL_LLM_MODEL"]
    embedding_model = os.environ["MISTRAL_EMBEDDING_MODEL"]
    if not model.strip() or embedding_model != "mistral-embed":
        raise ValueError("Explicit extraction model and mistral-embed are required")
    key = os.environ["MISTRAL_API_KEY"]
    if not key:
        raise ValueError("MISTRAL_API_KEY must be set in the local VPS .env")
    http = httpx.AsyncClient(transport=ApprovedTransport(
        model=model, embedding_model=embedding_model, approval=approval),
        follow_redirects=False, timeout=60)
    sdk = AsyncOpenAI(api_key=key, base_url="https://api.mistral.ai/v1",
                      max_retries=0, http_client=http)
    config = LLMConfig(api_key=key, base_url="https://api.mistral.ai/v1",
                       model=model, small_model=model, temperature=0, max_tokens=4096)
    # This pinned driver schedules index writes if constructed in a running loop.
    # Construct in a worker without a loop so initialize() is the only schema step.
    try:
        driver = await asyncio.to_thread(Neo4jDriver, os.environ["NEO4J_URI"],
                                        os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    except Exception as exc:
        await sdk.close()
        raise StageError("neo4j_persistence", "driver_setup") from exc
    graphiti = Graphiti(graph_driver=driver,
        llm_client=NoRetryClient(config=config, client=sdk, max_tokens=4096),
        embedder=SingleInputEmbedder(config=OpenAIEmbedderConfig(
            embedding_model=embedding_model, embedding_dim=1024), client=sdk),
        cross_encoder=DisabledReranker(), max_coroutines=1)
    return GraphitiContextEngine(graphiti), sdk
