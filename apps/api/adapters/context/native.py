"""QH-30 native projection/retrieval. No production startup binding.

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


def checked_rows(snapshot, validate_content=None):
    sources = {s["id"]: s for s in snapshot["source_revisions"]}
    if len(sources) != len(snapshot["source_revisions"]):
        raise NativeContextError("Duplicate canonical source revision")
    rows, seen = [], set()
    for raw in snapshot["understanding_item_revisions"]:
        if raw["id"] in seen:
            raise NativeContextError("Duplicate canonical item revision")
        seen.add(raw["id"])
        canonical = "type_id" in raw
        if (
            raw["validation_state"] not in {"proposed", "confirmed", "rejected"}
            or not raw["provenance"]
        ):
            raise NativeContextError("Invalid revision/state/evidence")
        if canonical:
            # Canonical SQL publication already enforced its pinned schema/rules.
            # These rows are internal repository exports, never LLM/API input.
            kind = raw["structural_kind"]
            if (
                kind not in {"item", "entity", "relation"}
                or not raw["type_id"]
                or raw["type_version"] < 1
            ):
                raise NativeContextError("Invalid registered semantic binding")
            category, type_id, version = kind, raw["type_id"], raw["type_version"]
            content = raw["content"]
            text = content.get("text", json.dumps(content, sort_keys=True))
            temporal = {
                k: raw[k] for k in ("fact_from", "fact_to", "valid_from", "valid_to")
            }
            relation = raw["relation"]
        else:
            category = raw["category"]
            if (
                not isinstance(category, str)
                or not category
                or not raw["content"].get("text")
                or validate_content is None
            ):
                raise NativeContextError("Invalid fixture revision/state/evidence")
            try:
                validate_content(category, raw["content"])
            except (ValueError, KeyError, TypeError) as exc:
                raise NativeContextError(
                    "Invalid semantic type/version/properties"
                ) from exc
            kind = (
                "relation"
                if category == "relationship"
                else "entity"
                if category == "entity"
                else "item"
            )
            content, text = raw["content"], raw["content"]["text"]
            type_id, version = content["semantic_type"], content["schema_version"]
            temporal = {
                k: None for k in ("fact_from", "fact_to", "valid_from", "valid_to")
            }
            relation = None
            if kind == "relation":
                props = content["properties"]
                relation = dict(
                    source_item_id=props["subject_item_id"],
                    source_revision_id=props["subject_revision_id"],
                    target_item_id=props["object_item_id"],
                    target_revision_id=props["object_revision_id"],
                    predicate=props["predicate"],
                )
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
            category=category,
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
        raise NativeContextError("Empty fixture generation")
    return rows


def scope_manifests(snapshot, validate_content=None):
    rows = checked_rows(snapshot, validate_content)
    scopes = set(snapshot.get("context_ids", [])) | {r["context_id"] for r in rows}
    return {
        scope: hashlib.sha256(
            json.dumps(
                sorted(r["fingerprint"] for r in rows if r["context_id"] == scope)
            ).encode()
        ).hexdigest()
        for scope in scopes
    }


def reconcile(repository, engine, scopes, *, force_rebuild=False):
    """Explicit full reconciliation; no high-water mark/outbox/LLM or lost work.

    Scope/session locks serialize projectors. Failures leave canonical commits intact;
    readiness checks detect lag, and an explicit next reconciliation recovers.
    """
    from uuid import uuid4

    scopes = tuple(sorted(set(map(str, scopes))))
    with repository.projection_lock(engine.slice_id, scopes):
        snapshot = repository.read_snapshot(scopes)
        expected = scope_manifests(snapshot)
        with engine.driver.session() as session:
            active = session.run(
                "MATCH (s:QH30Slice {id:$id}) RETURN s.active_generation AS generation,s.scope_manifests_json AS manifest",
                id=engine.slice_id,
            ).single()
        generation = (
            active["generation"]
            if active
            and active["manifest"] == json.dumps(expected, sort_keys=True)
            and not force_rebuild
            else uuid4().hex
        )
        engine.replace(snapshot, generation=generation)
        if scope_manifests(repository.read_snapshot(scopes)) != expected:
            raise NativeContextError(
                "Canonical state advanced during projection; reconcile again"
            )
        return generation


class NativeContextEngine:
    """Existing ContextEngine search shape; caller authorizes before adapter access.

    read_snapshot may be the scoped PostgreSQL repository or a retained test fixture.
    SQL-backed composition enables verify_readiness; fixture-only tests opt out.
    Generation replacement is intentionally one transaction for small datasets.
    """

    def __init__(
        self,
        driver,
        *,
        slice_id,
        read_snapshot,
        validate_content=None,
        verify_readiness=False,
    ):
        self.driver = driver
        self.slice_id = slice_id
        self.read_snapshot = read_snapshot
        self.validate_content = validate_content
        self.verify_readiness = verify_readiness

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
                "MERGE (s:QH30Slice {id:$id}) SET s.active_generation=$generation, s.scope_manifests_json=$manifest",
                id=self.slice_id,
                generation=generation,
                manifest=json.dumps(
                    scope_manifests(snapshot, self.validate_content), sort_keys=True
                ),
            ).consume()

        with self.driver.session() as session:
            session.execute_write(write)

    async def search(self, query):
        if not query.text.strip() or not 1 <= query.limit <= 100:
            raise ValueError("Nonempty query and bounded limit required")

        prepared = []

        def read():
            if self.verify_readiness:
                try:
                    prepared.append(self.read_snapshot(query.context_ids))
                except Exception as exc:
                    raise NativeContextError("Canonical read failed") from exc
            with self.driver.session() as session:
                active = session.run(
                    "MATCH (s:QH30Slice {id:$id}) RETURN s.active_generation AS generation,s.scope_manifests_json AS manifest",
                    id=self.slice_id,
                ).single()
                if not active:
                    raise NativeContextError("Projection not ready")
                if self.verify_readiness:
                    stored = json.loads(active["manifest"] or "{}")
                    expected = scope_manifests(prepared[0])
                    if any(
                        stored.get(scope) != value for scope, value in expected.items()
                    ):
                        raise NativeContextError(
                            "Projection pending: canonical scope differs"
                        )
                return session.run(
                    """MATCH (r:QH30Revision {slice_id:$slice_id, generation:$generation})
                    WHERE r.context_id IN $scopes AND ($verify OR toLower(r.text) CONTAINS toLower($text))
                    OPTIONAL MATCH (r)-[:EVIDENCED_BY]->(e:QH30Source)
                    RETURN r AS revision, collect(properties(e)) AS evidence,
                        toLower(r.text) CONTAINS toLower($text) AS matches
                    ORDER BY r.revision_id LIMIT $limit""",
                    slice_id=self.slice_id,
                    scopes=[str(c) for c in query.context_ids],
                    text=query.text,
                    limit=len(prepared[0]["understanding_item_revisions"]) + 1
                    if prepared
                    else query.limit,
                    verify=self.verify_readiness,
                    generation=active["generation"],
                ).data()

        candidates = await asyncio.to_thread(read)
        # One canonical bulk load; canonical text/state/provenance wins over graph.
        if prepared:
            expected_ids = {
                r["id"] for r in prepared[0]["understanding_item_revisions"]
            }
            actual_ids = {r["revision"]["revision_id"] for r in candidates}
            if expected_ids != actual_ids or len(candidates) != len(expected_ids):
                raise NativeContextError("Projection incomplete: reconcile required")
        if not candidates:
            return ContextResult(hits=())
        snapshot = (
            prepared[0]
            if prepared
            else self.read_snapshot(
                query.context_ids,
                tuple(c["revision"]["revision_id"] for c in candidates),
            )
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
