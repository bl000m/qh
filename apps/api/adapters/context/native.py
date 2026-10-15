"""QH-30 fixture-backed native slice. No production binding or canonical writer.

Input rows are a bulk canonical export/join shaped from QH-4, not a new Core DTO.
Neo4j stores only retrieval properties and references; hydration remains canonical.
"""

import asyncio
import hashlib
import json

from app.core.models import (
    ContextId,
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


def checked_rows(snapshot, validate_content):
    sources = {s["id"]: s for s in snapshot["source_revisions"]}
    if len(sources) != len(snapshot["source_revisions"]):
        raise NativeContextError("Duplicate canonical source revision")
    rows = []
    seen = set()
    for raw in snapshot["understanding_item_revisions"]:
        if raw["id"] in seen:
            raise NativeContextError("Duplicate canonical item revision")
        seen.add(raw["id"])
        if (
            not isinstance(raw["category"], str)
            or not raw["category"]
            or raw["validation_state"] not in {"proposed", "confirmed", "rejected"}
            or not raw["content"].get("text")
            or not raw["provenance"]
        ):
            raise NativeContextError("Invalid fixture revision/state/evidence")
        try:
            validate_content(raw["category"], raw["content"])
        except (ValueError, KeyError, TypeError) as exc:
            raise NativeContextError(
                "Invalid semantic type/version/properties"
            ) from exc
        evidence = []
        for identifier in raw["provenance"]:
            source = sources.get(identifier)
            if source is None or source["context_space_id"] != raw["context_space_id"]:
                raise NativeContextError("Missing or foreign canonical evidence")
            evidence.append(
                {"source_id": source["source_id"], "revision_id": source["id"]}
            )
        row = {
            "revision_id": raw["id"],
            "item_id": raw["item_id"],
            "context_id": raw["context_space_id"],
            "category": raw["category"],
            "validation_state": raw["validation_state"],
            "text": raw["content"]["text"],
            "content": raw["content"],
            "evidence": sorted(
                evidence, key=lambda x: (x["source_id"], x["revision_id"])
            ),
        }
        row["semantic_type"] = raw["content"]["semantic_type"]
        row["schema_version"] = raw["content"]["schema_version"]
        row["properties_json"] = json.dumps(
            raw["content"]["properties"], sort_keys=True
        )
        row["fingerprint"] = hashlib.sha256(
            json.dumps(row, sort_keys=True).encode()
        ).hexdigest()
        rows.append(row)
    if not rows:
        raise NativeContextError("Empty fixture generation")
    return rows


class NativeContextEngine:
    """Existing ContextEngine search shape; caller authorizes before adapter access.

    read_snapshot is one bulk canonical fixture read in this milestone. It must
    become an authorized canonical repository read before production deployment.
    Generation replacement is intentionally one transaction for small fixture sets.
    """

    def __init__(self, driver, *, slice_id, read_snapshot, validate_content):
        self.driver = driver
        self.slice_id = slice_id
        self.read_snapshot = read_snapshot
        self.validate_content = validate_content

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

    def replace(self, snapshot, *, generation):
        rows = checked_rows(
            snapshot, self.validate_content
        )  # Reject before opening a graph transaction.
        indexed = {row["revision_id"]: row for row in rows}
        relations = []
        for row in rows:
            if row["category"] == "relationship":
                properties = row["content"]["properties"]
                endpoints = [
                    indexed.get(properties[field])
                    for field in ("subject_revision_id", "object_revision_id")
                ]
                if any(
                    e is None or e["context_id"] != row["context_id"] for e in endpoints
                ):
                    raise NativeContextError(
                        "Missing, mismatched or foreign relation endpoint"
                    )
                if any(
                    endpoint["item_id"] != properties[field]
                    for endpoint, field in zip(
                        endpoints, ("subject_item_id", "object_item_id")
                    )
                ):
                    raise NativeContextError("Mismatched stable item/revision endpoint")
                relations.append({"revision": row["revision_id"], **properties})
        for row in rows:
            row["key"] = f"{self.slice_id}:{generation}:{row['revision_id']}"
        manifest = hashlib.sha256(
            json.dumps(sorted(row["fingerprint"] for row in rows)).encode()
        ).hexdigest()

        def write(tx):
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
                    "Changed or retired fixture generation cannot be reapplied"
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
                    r.schema_version=row.schema_version, r.properties_json=row.properties_json
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
        if not query.text.strip() or not 1 <= query.limit <= 100:
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
                    WHERE r.context_id IN $scopes AND toLower(r.text) CONTAINS toLower($text)
                    OPTIONAL MATCH (r)-[:EVIDENCED_BY]->(e:QH30Source)
                    RETURN r AS revision, collect(properties(e)) AS evidence
                    ORDER BY r.revision_id LIMIT $limit""",
                    slice_id=self.slice_id,
                    scopes=[str(c) for c in query.context_ids],
                    text=query.text,
                    limit=query.limit,
                    generation=active["generation"],
                ).data()

        candidates = await asyncio.to_thread(read)
        # One canonical bulk load; canonical text/state/provenance wins over graph.
        if not candidates:
            return ContextResult(hits=())
        snapshot = self.read_snapshot(
            query.context_ids, tuple(c["revision"]["revision_id"] for c in candidates)
        )
        canonical = {
            row["revision_id"]: row
            for row in checked_rows(snapshot, self.validate_content)
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
                    )
                )
                or graph["fingerprint"] != row["fingerprint"]
                or evidence != row["evidence"]
                or any(e["context_id"] != row["context_id"] for e in result["evidence"])
            ):
                raise NativeContextError(
                    "Stale, missing or cross-space graph/canonical evidence"
                )
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
