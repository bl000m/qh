"""Backend-local incremental projection worker and existing Core search adapter.

Explicit composition only. No broker, startup action, provider or paid API calls.
"""

import asyncio
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

from adapters.context.native import (
    NativeContextEngine,
    NativeContextError,
    checked_rows,
)
from app.core.models import ContextResult


def scope_key(scope, namespace="qh30-incremental"):
    return namespace + ":" + str(scope)


def immutable_snapshot(snapshot):
    result = deepcopy(snapshot)
    for row in result["understanding_item_revisions"]:
        # Current selection is mutable operational metadata on QH30Item, not an assertion.
        row["current_revision_id"] = None
    return result


class ProjectionOrderError(NativeContextError):
    pass


class IncrementalProjector:
    def __init__(self, driver, *, namespace="qh30-incremental"):
        self.driver = driver
        self.namespace = namespace

    def key(self, scope):
        return scope_key(scope, self.namespace)

    def initialize(self):
        with self.driver.session() as s:
            s.run(
                "CREATE CONSTRAINT qh30_sync_key IF NOT EXISTS FOR (s:QH30Sync) REQUIRE s.key IS UNIQUE"
            ).consume()
            s.run(
                "CREATE CONSTRAINT qh30_item_key IF NOT EXISTS FOR (s:QH30Item) REQUIRE s.key IS UNIQUE"
            ).consume()
        with self.driver.session() as s:
            s.run(
                "CREATE INDEX qh30_revision_scope_generation IF NOT EXISTS FOR (r:QH30Revision) ON (r.slice_id,r.generation)"
            ).consume()
        NativeContextEngine(
            self.driver, slice_id="unused", read_snapshot=None
        ).initialize()

    def apply(self, event, snapshot, head):
        rows = checked_rows(immutable_snapshot(snapshot))
        key = self.key(event["context_space_id"])
        epoch = str(event["epoch"])
        indexed = {r["revision_id"]: r for r in rows}
        prepared = []
        relations = []
        for r in rows:
            if r["context_id"] != str(event["context_space_id"]):
                raise NativeContextError("Foreign projection input")
            props = {
                name: r[name]
                for name in (
                    "revision_id",
                    "item_id",
                    "context_id",
                    "category",
                    "validation_state",
                    "text",
                    "fingerprint",
                    "semantic_type",
                    "schema_version",
                    "properties_json",
                    "temporal_json",
                )
            }
            props.update(r["temporal"], slice_id=key, generation=epoch)
            prepared.append(
                dict(
                    key=key + ":" + epoch + ":" + r["revision_id"],
                    props=props,
                    evidence=r["evidence"],
                )
            )
            if r["structural_kind"] == "relation":
                detail = r["relation"]
                for side in ("source", "target"):
                    anchor = indexed.get(detail[side + "_revision_id"])
                    if anchor is None or anchor["item_id"] != detail[side + "_item_id"]:
                        raise NativeContextError("Missing or mismatched anchor")
                relations.append(dict(revision=r["revision_id"], **detail))

        def write(tx):
            marker = tx.run(
                "MERGE (m:QH30Sync {key:$key}) ON CREATE SET m.epoch=$epoch,m.version=0 SET m.lock=coalesce(m.lock,0)+1 RETURN m.epoch AS epoch,m.version AS version",
                key=key,
                epoch=epoch,
            ).single()
            if marker["epoch"] != epoch:
                raise ProjectionOrderError(
                    "Projection epoch mismatch; rebuild required"
                )
            if marker["version"] >= event["scope_version"]:
                return 0
            if marker["version"] != event["scope_version"] - 1:
                raise ProjectionOrderError(
                    "Out-of-order projection; predecessor required"
                )
            records = tx.run(
                """UNWIND $rows AS row MERGE (r:QH30Revision {key:row.key})
                ON CREATE SET r+=row.props RETURN r.key AS key,r.fingerprint AS fingerprint""",
                rows=prepared,
            ).data()
            expected = {r["key"]: r["props"]["fingerprint"] for r in prepared}
            if any(r["fingerprint"] != expected[r["key"]] for r in records):
                raise NativeContextError("Immutable graph assertion mismatch")
            tx.run(
                """UNWIND $rows AS row MATCH (r:QH30Revision {key:row.key})
                UNWIND row.evidence AS e MERGE (s:QH30Source {key:$prefix+e.revision_id})
                ON CREATE SET s.revision_id=e.revision_id,s.source_id=e.source_id,s.context_id=$scope,s.slice_id=$key,s.generation=$epoch
                MERGE (r)-[:EVIDENCED_BY]->(s)""",
                rows=prepared,
                prefix=key + ":" + epoch + ":",
                scope=str(event["context_space_id"]),
                key=key,
                epoch=epoch,
            ).consume()
            tx.run(
                """UNWIND $relations AS d MATCH (r:QH30Revision {key:$prefix+d.revision})
                MATCH (a:QH30Revision {key:$prefix+d.source_revision_id}) MATCH (b:QH30Revision {key:$prefix+d.target_revision_id})
                MERGE (r)-[:SUBJECT]->(a) MERGE (r)-[:OBJECT]->(b) SET r.predicate=d.predicate""",
                relations=relations,
                prefix=key + ":" + epoch + ":",
            ).consume()
            if head:
                tx.run(
                    """MERGE (i:QH30Item {key:$key}) SET i.context_id=$scope,i.item_id=$item,
                    i.current_revision_id=$current
                    WITH i WHERE coalesce(i.latest_revision_no,0)<=$number
                    SET i.latest_revision_no=$number,i.latest_revision_id=$revision""",
                    key=key + ":" + epoch + ":item:" + str(event["item_id"]),
                    scope=str(event["context_space_id"]),
                    item=str(event["item_id"]),
                    current=None
                    if head["current_revision_id"] is None
                    else str(head["current_revision_id"]),
                    number=head["revision_no"],
                    revision=str(head["id"]),
                ).consume()
            tx.run(
                "MATCH (m:QH30Sync {key:$key}) SET m.version=$version MERGE (s:QH30Slice {id:$key}) SET s.active_generation=$epoch",
                key=key,
                version=event["scope_version"],
                epoch=epoch,
            ).consume()
            return len(rows)

        with self.driver.session() as s:
            return s.execute_write(write)

    def markers(self, scopes):
        with self.driver.session() as s:
            return {
                r["scope"]: r
                for r in s.run(
                    """UNWIND $scopes AS scope OPTIONAL MATCH (m:QH30Sync {key:$prefix+scope})
                OPTIONAL MATCH (g:QH30Slice {id:$prefix+scope})
                RETURN scope,m.epoch AS epoch,m.version AS version,g.active_generation AS active""",
                    scopes=list(map(str, scopes)),
                    prefix=self.namespace + ":",
                ).data()
            }


class ProjectionWorker:
    """Bounded retry with expiring, token-fenced leases; run inside backend process."""

    def __init__(self, repository, projector, scopes, *, lease_seconds=30):
        self.repository, self.projector, self.scopes = (
            repository,
            projector,
            tuple(map(str, scopes)),
        )
        self.lease_seconds = lease_seconds
        self.last_error = None
        self.last_revision_ids = ()
        self.last_applied_rows = 0

    def claim(self):
        with self.repository.connect() as c:
            scopes = self.repository._authorize(c, self.scopes)
            state = c.execute(
                """SELECT s.* FROM context_projection_state s JOIN projection_outbox o
                ON o.context_space_id=s.context_space_id AND o.scope_version=s.applied_version+1
                WHERE s.context_space_id=ANY(%s::uuid[]) AND s.desired_version>s.applied_version
                  AND ((o.state IN ('pending','failed') AND o.available_at<=clock_timestamp())
                    OR (o.state='processing' AND o.lease_until<clock_timestamp()))
                ORDER BY o.created_at FOR UPDATE OF s SKIP LOCKED LIMIT 1""",
                (scopes,),
            ).fetchone()
            if not state:
                return None
            event = c.execute(
                """UPDATE projection_outbox SET state='processing',attempts=attempts+1,
                lease_token=%s,lease_until=clock_timestamp()+(%s*interval '1 second'),error_code=NULL,error_type=NULL
                WHERE context_space_id=%s AND scope_version=%s RETURNING *""",
                (
                    uuid4(),
                    self.lease_seconds,
                    state["context_space_id"],
                    state["applied_version"] + 1,
                ),
            ).fetchone()
            return dict(event, epoch=state["epoch"])

    def _finish(self, event, *, error=None):
        with self.repository.connect() as c:
            state = c.execute(
                "SELECT * FROM context_projection_state WHERE context_space_id=%s FOR UPDATE",
                (event["context_space_id"],),
            ).fetchone()
            if state["epoch"] != event["epoch"]:
                return False
            if error:
                result = c.execute(
                    """UPDATE projection_outbox SET state='failed',error_code=%s,error_type=%s,
                    available_at=clock_timestamp()+(%s*interval '1 second'),lease_token=NULL,lease_until=NULL
                    WHERE id=%s AND state='processing' AND lease_token=%s RETURNING id""",
                    (
                        error,
                        type(self.last_error).__name__
                        if self.last_error
                        else "UnknownError",
                        min(2 ** min(event["attempts"], 6), 60),
                        event["id"],
                        event["lease_token"],
                    ),
                ).fetchone()
            else:
                if state["applied_version"] != event["scope_version"] - 1:
                    return False
                result = c.execute(
                    """UPDATE projection_outbox SET state='ready',completed_at=clock_timestamp(),
                    error_code=NULL,error_type=NULL,lease_token=NULL,lease_until=NULL WHERE id=%s AND state='processing' AND lease_token=%s RETURNING id""",
                    (event["id"], event["lease_token"]),
                ).fetchone()
                if result:
                    c.execute(
                        "UPDATE context_projection_state SET applied_version=%s,last_success_at=clock_timestamp() WHERE context_space_id=%s",
                        (event["scope_version"], event["context_space_id"]),
                    )
            return result is not None

    def process(self, event):
        repo = self.repository
        try:
            snapshot = repo.read_affected_snapshot(
                event["context_space_id"], event["revision_id"]
            )
            self.last_revision_ids = tuple(
                r["id"] for r in snapshot["understanding_item_revisions"]
            )
            with repo.connect() as c:
                repo._authorize(c, (event["context_space_id"],))
                head = c.execute(
                    """SELECT r.id,r.revision_no,i.current_revision_id FROM understanding_items i
                    JOIN understanding_item_revisions r ON r.item_id=i.id WHERE i.id=%s
                    ORDER BY r.revision_no DESC LIMIT 1""",
                    (event["item_id"],),
                ).fetchone()
            self.last_applied_rows = self.projector.apply(event, snapshot, head)
            return self._finish(event)
        except Exception as exc:
            self.last_error = exc
            # No payload, SQL, URI, SDK message or source text is persisted in diagnostics.
            self._finish(
                event,
                error="ordering_or_epoch"
                if isinstance(exc, ProjectionOrderError)
                else "projection_error",
            )
            return False

    def run_once(self):
        event = self.claim()
        if event is None:
            return False
        return self.process(event)

    def run(self, stop_event, *, poll_seconds=0.5):
        while not stop_event.is_set():
            try:
                progressed = self.run_once()
            except Exception as exc:
                self.last_error = exc
                progressed = False
            if not progressed:
                stop_event.wait(poll_seconds)

    def rebuild(self, scope):
        """Explicit recovery only: fence workers and pause scope commits, never LLM.

        A maintenance row lock spans graph I/O, unlike normal worker transactions.
        Old generations are retained. A lost SQL ack fails freshness closed.
        """
        repo = self.repository
        with repo.connect() as c:
            repo._authorize(c, (scope,))
            state = c.execute(
                "SELECT * FROM context_projection_state WHERE context_space_id=%s FOR UPDATE",
                (scope,),
            ).fetchone()
            epoch = str(uuid4())
            key = self.projector.key(scope)
            raw_snapshot = repo.read_snapshot((scope,))
            snapshot = immutable_snapshot(raw_snapshot)
            heads = {}
            for row in raw_snapshot["understanding_item_revisions"]:
                prior = heads.get(row["item_id"])
                if prior is None or row["revision_no"] > prior["revision_no"]:
                    heads[row["item_id"]] = row
            engine = NativeContextEngine(
                self.projector.driver, slice_id=key, read_snapshot=repo.read_snapshot
            )

            def fence(tx):
                tx.run(
                    "MERGE (m:QH30Sync {key:$key}) SET m.lock=coalesce(m.lock,0)+1,m.epoch=$epoch,m.version=$version",
                    key=key,
                    epoch=epoch,
                    version=state["desired_version"],
                ).consume()

            original_fence = fence

            def complete_fence(tx):
                original_fence(tx)
                tx.run(
                    """UNWIND $heads AS h MERGE (i:QH30Item {key:$prefix+h.item_id})
                    SET i.context_id=$scope,i.item_id=h.item_id,i.latest_revision_no=h.revision_no,
                    i.latest_revision_id=h.id,i.current_revision_id=h.current_revision_id""",
                    heads=list(heads.values()),
                    prefix=key + ":" + epoch + ":item:",
                    scope=str(scope),
                ).consume()

            engine.replace(snapshot, generation=epoch, transaction_guard=complete_fence)
            c.execute(
                "UPDATE context_projection_state SET epoch=%s,applied_version=desired_version,last_success_at=clock_timestamp() WHERE context_space_id=%s",
                (epoch, scope),
            )
            c.execute(
                "UPDATE projection_outbox SET state='ready',completed_at=clock_timestamp(),error_code=NULL,error_type=NULL,lease_token=NULL,lease_until=NULL WHERE context_space_id=%s AND scope_version<=%s",
                (scope, state["desired_version"]),
            )
            return epoch


class IncrementalContextEngine:
    """Constant-size sync gates + bounded candidate hydration, no scope-wide read."""

    def __init__(self, repository, projector):
        self.repository, self.projector = repository, projector

    def _ready(self, scopes):
        states = self.repository.sync_status(scopes)
        markers = self.projector.markers(scopes)
        for state in states:
            scope = state["context_space_id"]
            m = markers[scope]
            if state["desired_version"] != state["applied_version"]:
                raise NativeContextError("Projection pending or failed")
            if (
                state["desired_version"] == 0
                and m["epoch"] is None
                and m["active"] is None
            ):
                continue
            if (
                m["epoch"] != state["epoch"]
                or m["active"] != state["epoch"]
                or m["version"] != state["applied_version"]
            ):
                raise NativeContextError(
                    "Projection not ready; explicit rebuild required"
                )
        return {
            (s["context_space_id"], s["epoch"], s["desired_version"]) for s in states
        }

    async def search(self, query):
        before = await asyncio.to_thread(self._ready, query.context_ids)
        hits = []

        def read(scopes, ids):
            return immutable_snapshot(self.repository.read_snapshot(scopes, ids))

        for scope in query.context_ids:
            if any(s == str(scope) and version == 0 for s, _, version in before):
                continue
            engine = NativeContextEngine(
                self.projector.driver,
                slice_id=self.projector.key(scope),
                read_snapshot=read,
            )
            result = await engine.search(
                replace(query, context_ids=(scope,), limit=query.limit)
            )
            hits.extend(result.hits)
        after = await asyncio.to_thread(self._ready, query.context_ids)
        if before != after:
            raise NativeContextError("Projection advanced during retrieval; retry read")
        return ContextResult(hits=tuple(hits[: query.limit]))

    async def select_descriptors(self, *, context_ids, values, include_tentative=False,
                                 limit=20, after_revision_id=None):
        context_ids = tuple(dict.fromkeys(context_ids))
        before = await asyncio.to_thread(self._ready, context_ids)
        candidates = await asyncio.to_thread(
            self.repository.descriptor_candidates, context_ids, values,
            include_tentative=include_tentative, limit=limit,
            after_revision_id=after_revision_id,
        )
        hits = []
        for scope in context_ids:
            ids = [r["id"] for r in candidates if r["context_space_id"] == str(scope)]
            if not ids:
                continue
            engine = NativeContextEngine(
                self.projector.driver, slice_id=self.projector.key(scope),
                read_snapshot=lambda scopes, refs: immutable_snapshot(
                    self.repository.read_snapshot(scopes, refs)),
            )
            result = await engine.select_revisions(context_ids=(scope,), revision_ids=ids)
            hits.extend(result.hits)
        after = await asyncio.to_thread(self._ready, context_ids)
        if before != after:
            raise NativeContextError("Projection advanced during retrieval; retry read")
        return ContextResult(hits=tuple(sorted(hits, key=lambda h: str(h.item_revision.revision_id))))
