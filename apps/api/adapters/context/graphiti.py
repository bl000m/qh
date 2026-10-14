"""Replaceable derived semantic adapter. Callers authorize scope before invocation."""

import json
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from graphiti_core.errors import NodeNotFoundError
from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF

from app.core.models import (
    ContextId, ContextQuery, ContextResult, ContextSearchHit, RetrievalHitId,
    SourceId, SourceRevisionId, SourceRevisionRef,
)


class ContextEngineError(RuntimeError):
    pass


def group_id(context_id: ContextId) -> str:
    if not str(context_id).strip():
        raise ValueError("Context Space ID must not be empty")
    return "qh_" + uuid5(NAMESPACE_URL, "qh:space:" + str(context_id)).hex


def episode_id(context_id: ContextId, source: SourceRevisionRef) -> str:
    return str(uuid5(NAMESPACE_URL, json.dumps(
        [str(context_id), str(source.source_id), str(source.revision_id)], separators=(",", ":"))))


class GraphitiContextEngine:
    def __init__(self, client, *, episode_loader=None):
        self.client = client
        self.episode_loader = episode_loader or self._load_episodes

    async def _load_episodes(self, ids):
        return await EpisodicNode.get_by_uuids(self.client.driver, ids)

    async def initialize(self) -> None:
        """Explicit local schema initialization, never invoked at API startup."""
        await self.client.build_indices_and_constraints(delete_existing=False)

    async def ingest_source(self, *, context_id: ContextId, source: SourceRevisionRef,
                            text: str, reference_time: datetime) -> str:
        """Adapter-only operation; no canonical writes or human validation.

        QH-8 owns the canonical ingestion use case. This derived source descriptor
        makes synthetic QH-7 episodes resolvable across adapter restarts.
        """
        if not text.strip() or not source.source_id or not source.revision_id:
            raise ValueError("Source text and revision identifiers are required")
        if reference_time.tzinfo is None or reference_time.utcoffset() is None:
            raise ValueError("reference_time must be timezone-aware")
        scope = group_id(context_id)
        identifier = episode_id(context_id, source)
        descriptor = json.dumps({"qh_source_revision_v1": {
            "context_id": str(context_id), "source_id": str(source.source_id),
            "revision_id": str(source.revision_id)}}, separators=(",", ":"))
        try:
            # Graphiti 0.30.2 treats uuid as an existing episode lookup, not a
            # creation ID. Persist only the derived episode before extraction.
            try:
                episode = await EpisodicNode.get_by_uuid(self.client.driver, identifier)
            except NodeNotFoundError:
                episode = EpisodicNode(uuid=identifier, name=identifier, group_id=scope,
                    source=EpisodeType.text, source_description=descriptor, content=text,
                    created_at=datetime.now(timezone.utc), valid_at=reference_time)
                await episode.save(self.client.driver)
            else:
                if (episode.group_id != scope or episode.source != EpisodeType.text
                        or episode.source_description != descriptor or episode.content != text
                        or episode.valid_at != reference_time):
                    raise ValueError("Existing derived episode conflicts with the source revision")
            await self.client.add_episode(name=identifier, episode_body=text,
                source_description=descriptor, reference_time=reference_time,
                source=EpisodeType.text, group_id=scope, uuid=identifier,
                previous_episode_uuids=[], update_communities=False)
        except Exception:
            raise ContextEngineError("Semantic ingestion failed") from None
        return identifier

    async def search(self, query: ContextQuery) -> ContextResult:
        if not query.text.strip() or query.limit < 1 or query.limit > 100:
            raise ValueError("Search requires text and a limit between 1 and 100")
        scopes = {group_id(ctx): ctx for ctx in query.context_ids}
        try:
            # Copy the recipe: Graphiti.search mutates the global recipe limit.
            config = EDGE_HYBRID_SEARCH_RRF.model_copy(deep=True)
            config.limit = query.limit
            result = await self.client.search_(query=query.text, config=config,
                                                group_ids=list(scopes))
            edges = list(result.edges)
            if any(edge.group_id not in scopes for edge in edges):
                raise ValueError("Out-of-scope result")
            ids = list(dict.fromkeys(eid for edge in edges for eid in edge.episodes))
            episodes = {ep.uuid: ep for ep in await self.episode_loader(ids)} if ids else {}
            hits = []
            for edge in edges[:query.limit]:
                provenance = []
                for eid in edge.episodes:
                    ep = episodes.get(eid)
                    if ep is None or ep.group_id != edge.group_id:
                        raise ValueError("Missing or cross-space source provenance")
                    data = json.loads(ep.source_description)["qh_source_revision_v1"]
                    context_id = scopes[edge.group_id]
                    ref = SourceRevisionRef(source_id=SourceId(data["source_id"]),
                                            revision_id=SourceRevisionId(data["revision_id"]))
                    if (data["context_id"] != str(context_id) or not ref.source_id
                            or not ref.revision_id or episode_id(context_id, ref) != eid):
                        raise ValueError("Invalid source descriptor")
                    if ref not in provenance:
                        provenance.append(ref)
                if not provenance:
                    raise ValueError("Semantic hit lacks source revision provenance")
                hits.append(ContextSearchHit(id=RetrievalHitId(edge.uuid),
                    context_id=scopes[edge.group_id], excerpt=edge.fact,
                    provenance=tuple(provenance)))
            return ContextResult(hits=tuple(hits))
        except Exception:
            raise ContextEngineError("Semantic retrieval failed") from None

    async def close(self) -> None:
        await self.client.close()
