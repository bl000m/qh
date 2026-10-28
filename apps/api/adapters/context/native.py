"""Native projection/retrieval composed by the backend runtime.

Input rows are registered canonical repository exports, not a public ingest DTO.
Neo4j stores only retrieval properties and references; hydration remains canonical.
"""

import asyncio
import hashlib
import json

from app.core.models import (
    ContextId,
    ContextQuery,
    ContextRequest,
    ContextResult,
    ContextSearchHit,
    ItemRevisionRef,
    RetrievalHitId,
    SourceId,
    SourceRevisionId,
    SourceRevisionRef,
    UnderstandingItemId,
    UnderstandingRevisionId,
)
from app.policy.models import PolicyAction, PolicyRequest


class NativeContextError(RuntimeError):
    pass


def checked_rows(snapshot):
    sources = {s["id"]: s for s in snapshot["source_revisions"]}
    if len(sources) != len(snapshot["source_revisions"]):
        raise NativeContextError("Duplicate canonical source revision")
    rows, seen = [], set()
    for raw in snapshot["understanding_item_revisions"]:
        if raw["id"] in seen:
            raise NativeContextError("Duplicate canonical item revision")
        seen.add(raw["id"])
        if (
            raw["validation_state"] not in {"proposed", "confirmed", "rejected"}
            or not raw["provenance"]
        ):
            raise NativeContextError("Invalid revision/state/evidence")
        # SQL publication enforces pinned schemas/rules. This is a repository
        # export boundary, never an alternate validator for LLM/API input.
        kind = raw.get("structural_kind")
        if (
            kind not in {"item", "entity", "relation"}
            or not raw.get("type_id")
            or not isinstance(raw.get("type_version"), int)
            or raw["type_version"] < 1
        ):
            raise NativeContextError("Invalid registered semantic binding")
        type_id, version = raw["type_id"], raw["type_version"]
        content = raw["content"]
        text = content.get("text", json.dumps(content, sort_keys=True))
        temporal = {
            k: raw[k] for k in ("fact_from", "fact_to", "valid_from", "valid_to")
        }
        relation = raw["relation"]
        if not isinstance(text, str) or not text:
            raise NativeContextError("Invalid retrieval text")
        evidence = []
        for identifier in raw["provenance"]:
            source = sources.get(identifier)
            if source is None or source["context_space_id"] != raw["context_space_id"]:
                raise NativeContextError("Missing or foreign canonical evidence")
            evidence.append(
                {"source_id": source["source_id"], "revision_id": source["id"]}
            )
        row = dict(
            revision_id=raw["id"],
            item_id=raw["item_id"],
            context_id=raw["context_space_id"],
            category=kind,  # Retained graph property name; value is structural shape.
            structural_kind=kind,
            validation_state=raw["validation_state"],
            text=text,
            content=content,
            semantic_type=type_id,
            schema_version=version,
            relation=relation,
            current_revision_id=raw.get("current_revision_id"),
            temporal=temporal,
            properties_json=json.dumps(content.get("properties", {}), sort_keys=True),
            evidence=sorted(evidence, key=lambda x: (x["source_id"], x["revision_id"])),
        )
        row["temporal_json"] = json.dumps(temporal, sort_keys=True)
        row["fingerprint"] = hashlib.sha256(
            json.dumps(row, sort_keys=True).encode()
        ).hexdigest()
        rows.append(row)
    if not rows and "context_ids" not in snapshot:
        raise NativeContextError("Empty unscoped generation")
    return rows


class NativeContextEngine:
    """Existing ContextEngine search shape; caller authorizes before adapter access.

    read_snapshot returns registered repository-shaped rows. Fixture tests use
    the same representation. Readiness is enforced by the incremental engine.
    Generation replacement is intentionally one transaction for small datasets.
    """

    def __init__(
        self,
        driver,
        *,
        slice_id,
        read_snapshot,
    ):
        self.driver = driver
        self.slice_id = slice_id
        self.read_snapshot = read_snapshot

    def initialize(self):
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT qh30_generation_key IF NOT EXISTS "
                "FOR (g:QH30Generation) REQUIRE g.key IS UNIQUE"
            ).consume()
            session.run(
                "CREATE CONSTRAINT qh30_revision_key IF NOT EXISTS "
                "FOR (r:QH30Revision) REQUIRE r.key IS UNIQUE"
            ).consume()
            session.run(
                "CREATE CONSTRAINT qh30_source_key IF NOT EXISTS "
                "FOR (r:QH30Source) REQUIRE r.key IS UNIQUE"
            ).consume()
            session.run(
                "CREATE CONSTRAINT qh30_slice_key IF NOT EXISTS "
                "FOR (r:QH30Slice) REQUIRE r.id IS UNIQUE"
            ).consume()

    def replace(self, snapshot, *, generation, transaction_guard=None):
        rows = checked_rows(snapshot)  # Reject before opening a graph transaction.
        indexed = {row["revision_id"]: row for row in rows}
        relations = []
        for row in rows:
            if row["structural_kind"] == "relation":
                detail = row["relation"]
                if detail is None:
                    raise NativeContextError("Missing relation detail")
                for side in ("source", "target"):
                    endpoint = indexed.get(detail[side + "_revision_id"])
                    if endpoint is None or endpoint["context_id"] != row["context_id"]:
                        raise NativeContextError("Missing or foreign relation endpoint")
                    if endpoint["item_id"] != detail[side + "_item_id"]:
                        raise NativeContextError(
                            "Mismatched stable item/revision endpoint"
                        )
                relations.append(
                    dict(
                        revision=row["revision_id"],
                        predicate=detail["predicate"],
                        subject_revision_id=detail["source_revision_id"],
                        object_revision_id=detail["target_revision_id"],
                    )
                )
        for row in rows:
            row["key"] = f"{self.slice_id}:{generation}:{row['revision_id']}"
        manifest = hashlib.sha256(
            json.dumps(sorted(row["fingerprint"] for row in rows)).encode()
        ).hexdigest()

        def write(tx):
            if transaction_guard is not None:
                transaction_guard(tx)
            old = tx.run(
                "MATCH (s:QH30Slice {id:$id}) RETURN s.active_generation AS active",
                id=self.slice_id,
            ).single()
            generation_key = self.slice_id + ":" + generation
            prior = tx.run(
                "MATCH (g:QH30Generation {key:$key}) RETURN g.fingerprint AS fingerprint",
                key=generation_key,
            ).single()
            if prior and (
                prior["fingerprint"] != manifest
                or not old
                or old["active"] != generation
            ):
                raise NativeContextError(
                    "Changed or retired generation cannot be reapplied"
                )
            tx.run(
                "MERGE (g:QH30Generation {key:$key}) ON CREATE SET g.fingerprint=$fingerprint",
                key=generation_key,
                fingerprint=manifest,
            ).consume()
            records = tx.run(
                """UNWIND $rows AS row
                MERGE (r:QH30Revision {key: row.key})
                ON CREATE SET r.slice_id=$slice_id, r.generation=$generation,
                    r.revision_id=row.revision_id, r.item_id=row.item_id,
                    r.context_id=row.context_id, r.category=row.category,
                    r.validation_state=row.validation_state, r.text=row.text,
                    r.fingerprint=row.fingerprint, r.semantic_type=row.semantic_type,
                    r.schema_version=row.schema_version, r.properties_json=row.properties_json,
                    r.temporal_json=row.temporal_json, r.fact_from=row.temporal.fact_from,
                    r.fact_to=row.temporal.fact_to, r.valid_from=row.temporal.valid_from,
                    r.valid_to=row.temporal.valid_to
                RETURN r.key AS key, r.fingerprint AS fingerprint""",
                rows=rows,
                slice_id=self.slice_id,
                generation=generation,
            ).data()
            expected = {row["key"]: row["fingerprint"] for row in rows}
            if any(
                record["fingerprint"] != expected[record["key"]] for record in records
            ):
                raise NativeContextError(
                    "Revision changed within immutable graph generation"
                )
            tx.run(
                """UNWIND $rows AS row
                MATCH (r:QH30Revision {key:row.key})
                UNWIND row.evidence AS ref
                MERGE (s:QH30Source {key:$slice_id+':'+$generation+':'+ref.revision_id})
                ON CREATE SET s.source_id=ref.source_id, s.revision_id=ref.revision_id,
                    s.context_id=row.context_id, s.slice_id=$slice_id, s.generation=$generation
                MERGE (r)-[:EVIDENCED_BY]->(s)""",
                rows=rows,
                slice_id=self.slice_id,
                generation=generation,
            ).consume()
            tx.run(
                """UNWIND $relations AS rel
                MATCH (r:QH30Revision {key:$prefix+rel.revision})
                MATCH (a:QH30Revision {key:$prefix+rel.subject_revision_id})
                MATCH (b:QH30Revision {key:$prefix+rel.object_revision_id})
                MERGE (r)-[:SUBJECT]->(a) MERGE (r)-[:OBJECT]->(b)
                SET r.predicate=rel.predicate""",
                relations=relations,
                prefix=self.slice_id + ":" + generation + ":",
            ).consume()
            # A failed transaction never switches the active generation.
            tx.run(
                "MERGE (s:QH30Slice {id:$id}) SET s.active_generation=$generation",
                id=self.slice_id,
                generation=generation,
            ).consume()

        with self.driver.session() as session:
            session.execute_write(write)

    async def search(self, query):
        return await self._search(query)

    async def select_revisions(self, *, context_ids, revision_ids, view=None):
        """Internal exact-ID graph lookup for canonically selected descriptors."""
        revision_ids = tuple(map(str, revision_ids))
        if not 1 <= len(revision_ids) <= (101 if view is not None else 100):
            raise ValueError("Bounded incremental revision selection required")
        query = ContextQuery(text="", context_ids=tuple(context_ids), limit=len(revision_ids), view=view)
        return await self._search(query, revision_ids=revision_ids)

    async def _search(self, query, revision_ids=None):
        maximum = 101 if query.view is not None else 100
        if (revision_ids is None and not query.text.strip()) or not 1 <= query.limit <= maximum:
            raise ValueError("Nonempty query and bounded limit required")

        def read():
            with self.driver.session() as session:
                active = session.run(
                    "MATCH (s:QH30Slice {id:$id}) RETURN s.active_generation AS generation",
                    id=self.slice_id,
                ).single()
                if not active:
                    raise NativeContextError("Projection not ready")
                return session.run(
                    """MATCH (r:QH30Revision {slice_id:$slice_id, generation:$generation})
                    OPTIONAL MATCH (i:QH30Item {key:$slice_id+':'+$generation+':item:'+r.item_id})
                    WITH r,i
                    WHERE r.context_id IN $scopes AND (($ids IS NOT NULL AND r.revision_id IN $ids)
                         OR ($ids IS NULL AND toLower(r.text) CONTAINS toLower($text)))
                    AND ($after IS NULL OR r.revision_id>$after)
                    AND ($view IS NULL OR $view='history'
                         OR ($view='proposed' AND r.validation_state='proposed')
                         OR ($view='current' AND r.validation_state='confirmed' AND i.current_revision_id=r.revision_id))
                    OPTIONAL MATCH (r)-[:EVIDENCED_BY]->(e:QH30Source)
                    RETURN r AS revision, collect(properties(e)) AS evidence,
                        [(r)-[:SUBJECT]->(a) | {item_id:a.item_id, revision_id:a.revision_id, context_id:a.context_id}] AS subject_anchors,
                        [(r)-[:OBJECT]->(b) | {item_id:b.item_id, revision_id:b.revision_id, context_id:b.context_id}] AS object_anchors,
                        ($ids IS NOT NULL OR toLower(r.text) CONTAINS toLower($text)) AS matches
                    ORDER BY r.revision_id LIMIT $limit""",
                    slice_id=self.slice_id,
                    scopes=[str(c) for c in query.context_ids],
                    text=query.text,
                    ids=revision_ids,
                    limit=query.limit,
                    generation=active["generation"],
                    view=query.view,
                    after=query.after_revision_id,
                ).data()

        candidates = await asyncio.to_thread(read)
        if revision_ids is not None and {
            r["revision"]["revision_id"] for r in candidates
        } != set(revision_ids):
            raise NativeContextError("Selected revisions missing from graph; rebuild required")
        # One canonical bulk load; canonical text/state/provenance wins over graph.
        if not candidates:
            return ContextResult(hits=())
        try:
            snapshot = await asyncio.to_thread(self.read_snapshot,
                query.context_ids, tuple(c["revision"]["revision_id"] for c in candidates)
            )
        except Exception as exc:
            raise NativeContextError("Canonical read failed") from exc
        canonical = {
            row["revision_id"]: row
            for row in checked_rows(snapshot)
        }
        hits = []
        for result in candidates:
            graph = result["revision"]
            row = canonical.get(graph["revision_id"])
            evidence = sorted(
                [
                    {"source_id": e["source_id"], "revision_id": e["revision_id"]}
                    for e in result["evidence"]
                ],
                key=lambda e: (e["source_id"], e["revision_id"]),
            )
            if (
                row is None
                or row["context_id"] not in query.context_ids
                or any(
                    graph[field] != row[field]
                    for field in (
                        "context_id",
                        "item_id",
                        "text",
                        "category",
                        "validation_state",
                        "semantic_type",
                        "schema_version",
                        "properties_json",
                        "temporal_json",
                    )
                )
                or graph["fingerprint"] != row["fingerprint"]
                or any(graph.get(k) != value for k, value in row["temporal"].items())
                or evidence != row["evidence"]
                or any(e["context_id"] != row["context_id"] for e in result["evidence"])
            ):
                raise NativeContextError(
                    "Stale, missing or cross-space graph/canonical evidence"
                )
            if query.view is not None:
                detail = row["relation"]
                for side, field in (("source", "subject_anchors"), ("target", "object_anchors")):
                    expected = [] if detail is None else [dict(
                        item_id=detail[side + "_item_id"],
                        revision_id=detail[side + "_revision_id"],
                        context_id=row["context_id"],
                    )]
                    if result[field] != expected:
                        raise NativeContextError("Missing or inconsistent relation anchors")
            if not result["matches"] or len(hits) >= query.limit:
                continue
            hits.append(
                ContextSearchHit(
                    id=RetrievalHitId("native:" + row["revision_id"]),
                    context_id=ContextId(row["context_id"]),
                    excerpt=row["text"],
                    item_revision=ItemRevisionRef(
                        context_id=ContextId(row["context_id"]),
                        item_id=UnderstandingItemId(row["item_id"]),
                        revision_id=UnderstandingRevisionId(row["revision_id"]),
                    ),
                    provenance=tuple(
                        SourceRevisionRef(
                            source_id=SourceId(e["source_id"]),
                            revision_id=SourceRevisionId(e["revision_id"]),
                        )
                        for e in row["evidence"]
                    ),
                )
            )
        return ContextResult(hits=tuple(hits))


class AuthorizedNativeContextService:
    """Internal manual slice: reuse QH PolicyService, never a second owner policy."""

    def __init__(self, *, policy, engine):
        self.policy = policy
        self.engine = engine

    async def retrieve(self, request: ContextRequest):
        decision = await self.policy.evaluate(
            PolicyRequest(
                subject_id=request.subject_id,
                action=PolicyAction.READ_CONTEXT,
                context_ids=request.query.context_ids,
            )
        )
        if not decision.allowed:
            raise PermissionError("Context access denied")
        return await self.engine.search(request.query)

    async def browse(self, request: ContextRequest):
        decision = await self.policy.evaluate(PolicyRequest(
            subject_id=request.subject_id, action=PolicyAction.READ_CONTEXT,
            context_ids=request.query.context_ids,
        ))
        if not decision.allowed:
            raise PermissionError('Context access denied')
        return await self.engine.browse(request.query)

    async def select_descriptors(self, *, subject_id, context_ids, values,
                                 include_tentative=False, limit=20, after_revision_id=None):
        """Internal authorized exact selection; no public port/HTTP DTO change."""
        context_ids = tuple(context_ids)
        decision = await self.policy.evaluate(PolicyRequest(
            subject_id=subject_id, action=PolicyAction.READ_CONTEXT,
            context_ids=tuple(context_ids),
        ))
        if not decision.allowed:
            raise PermissionError("Context access denied")
        return await self.engine.select_descriptors(
            context_ids=tuple(context_ids), values=values,
            include_tentative=include_tentative, limit=limit,
            after_revision_id=after_revision_id,
        )
