"""Internal canonical SQL adapter; no public ingestion API or Source Vault I/O.

Writes are for an already-authorized application/test operation. Owner/scope checks
are defense in depth, not a new policy action. Registration is explicit provisioning.
"""

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

TEMPORAL = ("fact_from", "fact_to", "valid_from", "valid_to")


def json_values(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: json_values(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_values(v) for v in value]
    if isinstance(value, (UUID, datetime)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    return value


class CanonicalRepository:
    def __init__(self, *, url, subject_id):
        self.url, self.subject_id = url, str(subject_id)

    def connect(self, **kwargs):
        return psycopg.connect(
            host=self.url.host,
            port=self.url.port,
            dbname=self.url.database,
            user=self.url.username,
            password=self.url.password,
            connect_timeout=5,
            row_factory=dict_row,
            **kwargs,
        )

    def _authorize(self, c, scopes, *, lock=False):
        scopes = sorted(set(map(str, scopes)))
        if not scopes or not self.subject_id:
            raise PermissionError("Explicit owned scopes required")
        rows = c.execute(
            "SELECT cs.id FROM context_spaces cs JOIN users u ON u.id=cs.owner_id "
            "WHERE cs.id=ANY(%s::uuid[]) AND cs.owner_id=%s::uuid "
            "AND cs.status='active' AND u.status='active'"
            + (" FOR SHARE OF cs,u" if lock else ""),
            (scopes, self.subject_id),
        ).fetchall()
        if {str(r["id"]) for r in rows} != set(scopes):
            raise PermissionError("Owned scope required")
        return scopes

    @staticmethod
    def _immutable(c, table, values):
        """Called under publication lock; compare replay, never update history."""
        key = "id" if "id" in values else "item_revision_id"
        exists = c.execute(
            sql.SQL("SELECT 1 FROM {} WHERE {}=%s").format(
                sql.Identifier(table), sql.Identifier(key)
            ),
            (values[key],),
        ).fetchone()
        converted = [
            Jsonb(v) if isinstance(v, (dict, list)) else v for v in values.values()
        ]
        if exists:
            comparisons = sql.SQL(" AND ").join(
                sql.SQL("{} IS NOT DISTINCT FROM %s").format(sql.Identifier(k))
                for k in values
            )
            matches = c.execute(
                sql.SQL("SELECT ({}) AS matches FROM {} WHERE {}=%s").format(
                    comparisons, sql.Identifier(table), sql.Identifier(key)
                ),
                (*converted, values[key]),
            ).fetchone()
            if not matches["matches"]:
                raise ValueError("Conflicting immutable replay")
            return
        c.execute(
            sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(",").join(map(sql.Identifier, values)),
                sql.SQL(",").join(sql.Placeholder() for _ in values),
            ),
            converted,
        )

    @staticmethod
    def _identity(c, table, identifier, scope, name=None):
        values = {"id": identifier, "context_space_id": scope}
        if name is not None:
            values["name"] = name
        c.execute(
            sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT(id) DO NOTHING"
            ).format(
                sql.Identifier(table),
                sql.SQL(",").join(map(sql.Identifier, values)),
                sql.SQL(",").join(sql.Placeholder() for _ in values),
            ),
            tuple(values.values()),
        )
        row = c.execute(
            sql.SQL("SELECT context_space_id FROM {} WHERE id=%s").format(
                sql.Identifier(table)
            ),
            (identifier,),
        ).fetchone()
        if str(row["context_space_id"]) != str(scope):
            raise PermissionError("Identity belongs to another scope")

    def register_types(self, definitions):
        """Explicit trusted schema provisioning, never inferred from LLM output."""
        with self.connect() as c:
            for definition in definitions:
                c.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    ("type:" + definition["type_id"],),
                )
                existing = c.execute(
                    "SELECT * FROM semantic_type_versions WHERE type_id=%s AND version=%s",
                    (definition["type_id"], definition["version"]),
                ).fetchone()
                expected = {**definition, "validator_version": "qh-schema-1"}
                expected.setdefault("relation_rules", None)
                if existing:
                    if existing != expected:
                        raise ValueError("Conflicting registered type replay")
                else:
                    c.execute(
                        "INSERT INTO semantic_type_versions(type_id,version,structural_kind,property_schema,relation_rules,validator_version) VALUES (%s,%s,%s,%s,%s,%s)",
                        (
                            expected["type_id"],
                            expected["version"],
                            expected["structural_kind"],
                            Jsonb(expected["property_schema"]),
                            None
                            if expected["relation_rules"] is None
                            else Jsonb(expected["relation_rules"]),
                            expected["validator_version"],
                        ),
                    )

    def save(self, *, sources=(), revisions=()):
        """One ACID batch; IDs/numbers explicit; no automatic confirmation/current."""
        sources, revisions = tuple(sources), tuple(revisions)
        scopes = {r["context_space_id"] for r in (*sources, *revisions)}
        with self.connect() as c:
            self._authorize(c, scopes, lock=True)
            for key in sorted({str(r["id"]) for r in (*sources, *revisions)}):
                c.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (key,)
                )
            for source in sources:
                self._identity(
                    c,
                    "sources",
                    source["source_id"],
                    source["context_space_id"],
                    source.get("source_name", "Source"),
                )
                values = {
                    k: source[k]
                    for k in (
                        "id",
                        "source_id",
                        "context_space_id",
                        "revision_no",
                        "content",
                        "origin",
                    )
                }
                if "created_at" in source:
                    values["created_at"] = source["created_at"]
                self._immutable(c, "source_revisions", values)
            for revision in revisions:
                self._identity(
                    c,
                    "understanding_items",
                    revision["item_id"],
                    revision["context_space_id"],
                )
                binding = dict(
                    item_revision_id=revision["id"],
                    context_space_id=revision["context_space_id"],
                    type_id=revision["type_id"],
                    type_version=revision["type_version"],
                    **{k: revision.get(k) for k in TEMPORAL},
                )
                self._immutable(c, "item_revision_types", binding)
                relation = revision.get("relation")
                if relation is not None:
                    self._immutable(
                        c,
                        "relation_revision_details",
                        dict(
                            item_revision_id=revision["id"],
                            context_space_id=revision["context_space_id"],
                            **relation,
                        ),
                    )
                elif c.execute(
                    "SELECT 1 FROM relation_revision_details WHERE item_revision_id=%s",
                    (revision["id"],),
                ).fetchone():
                    raise ValueError("Immutable relation cannot be removed")
                published = c.execute(
                    "SELECT 1 FROM understanding_item_revisions WHERE id=%s",
                    (revision["id"],),
                ).fetchone()
                provenance = set(map(str, revision["provenance"]))
                if published:
                    old = c.execute(
                        "SELECT source_revision_id FROM item_revision_provenance WHERE item_revision_id=%s",
                        (revision["id"],),
                    ).fetchall()
                    if provenance != {str(r["source_revision_id"]) for r in old}:
                        raise ValueError("Conflicting immutable provenance replay")
                else:
                    for ref in sorted(provenance):
                        c.execute(
                            "INSERT INTO item_revision_provenance VALUES (%s,%s,%s)",
                            (revision["id"], ref, revision["context_space_id"]),
                        )
                values = {
                    k: revision[k]
                    for k in (
                        "id",
                        "item_id",
                        "context_space_id",
                        "revision_no",
                        "content",
                        "origin_kind",
                        "validation_state",
                    )
                }
                values.update(
                    category=None,
                    validated_by=revision.get("validated_by"),
                    validated_at=revision.get("validated_at"),
                    based_on_revision_id=revision.get("based_on_revision_id"),
                )
                if "created_at" in revision:
                    values["created_at"] = revision["created_at"]
                self._immutable(c, "understanding_item_revisions", values)

    def read_snapshot(self, context_ids, revision_ids=None):
        """Authorized, consistent bulk read; all history unless IDs explicitly given.

        Source content is a representation; origin may locate an external original.
        No original bytes are fetched or required to build a graph/provenance ref.
        """
        with self.connect() as c:
            c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            scopes = self._authorize(c, context_ids)
            revision_ids = None if revision_ids is None else list(revision_ids)
            rows = c.execute(
                """SELECT r.*,i.current_revision_id,t.type_id,t.type_version,
                t.fact_from,t.fact_to,t.valid_from,t.valid_to,s.structural_kind,
                d.source_item_id,d.source_revision_id,d.target_item_id,d.target_revision_id,d.predicate,
                ARRAY(SELECT p.source_revision_id FROM item_revision_provenance p
                      WHERE p.item_revision_id=r.id ORDER BY p.source_revision_id) AS provenance
                FROM understanding_item_revisions r JOIN understanding_items i ON i.id=r.item_id
                JOIN item_revision_types t ON t.item_revision_id=r.id
                JOIN semantic_type_versions s ON (s.type_id,s.version)=(t.type_id,t.type_version)
                LEFT JOIN relation_revision_details d ON d.item_revision_id=r.id
                WHERE r.context_space_id=ANY(%s::uuid[])
                  AND (%s::uuid[] IS NULL OR r.id=ANY(%s::uuid[])) ORDER BY r.id""",
                (
                    scopes,
                    None if revision_ids is None else list(revision_ids),
                    None if revision_ids is None else list(revision_ids),
                ),
            ).fetchall()
            for row in rows:
                row["relation"] = None
                if row["structural_kind"] == "relation":
                    row["relation"] = {
                        k: row[k]
                        for k in (
                            "source_item_id",
                            "source_revision_id",
                            "target_item_id",
                            "target_revision_id",
                            "predicate",
                        )
                    }
                for k in (
                    "source_item_id",
                    "source_revision_id",
                    "target_item_id",
                    "target_revision_id",
                    "predicate",
                ):
                    row.pop(k)
            refs = sorted({str(ref) for row in rows for ref in row["provenance"]})
            sources = c.execute(
                "SELECT * FROM source_revisions WHERE context_space_id=ANY(%s::uuid[]) AND id=ANY(%s::uuid[]) ORDER BY id",
                (scopes, refs),
            ).fetchall()
            return json_values(
                {
                    "context_ids": scopes,
                    "source_revisions": sources,
                    "understanding_item_revisions": rows,
                }
            )

    @contextmanager
    def projection_lock(self, slice_id, scopes):
        # Session lock survives read transactions, but no SQL transaction spans Neo4j I/O.
        with self.connect(autocommit=True) as c:
            self._authorize(c, scopes)
            c.execute(
                "SELECT pg_advisory_lock(hashtextextended(%s,0))",
                ("projection:" + slice_id,),
            )
            try:
                yield
            finally:
                c.execute(
                    "SELECT pg_advisory_unlock(hashtextextended(%s,0))",
                    ("projection:" + slice_id,),
                )

    def read_affected_snapshot(self, context_id, revision_id):
        """Only changed revision and transitive immutable anchors, using FK indexes."""
        with self.connect() as c:
            self._authorize(c, (context_id,))
            ids = c.execute(
                """WITH RECURSIVE affected(id) AS (
                SELECT id FROM understanding_item_revisions WHERE id=%s AND context_space_id=%s
                UNION
                SELECT endpoint.id FROM affected a
                  JOIN relation_revision_details d ON d.item_revision_id=a.id
                  CROSS JOIN LATERAL (VALUES(d.source_revision_id),(d.target_revision_id)) endpoint(id)
                  WHERE d.context_space_id=%s
                ) SELECT id FROM affected""",
                (revision_id, context_id, context_id),
            ).fetchall()
        return self.read_snapshot((context_id,), [r["id"] for r in ids])

    def sync_status(self, context_ids):
        """O(number of requested scopes), no canonical revision scan."""
        with self.connect() as c:
            scopes = self._authorize(c, context_ids)
            rows = c.execute(
                """SELECT s.*,o.state AS next_state,o.attempts,o.error_code,o.error_type,
                CASE WHEN s.desired_version=s.applied_version THEN 'ready' ELSE COALESCE(o.state,'failed') END AS sync_state,
                CASE WHEN o.id IS NULL THEN 0 ELSE EXTRACT(EPOCH FROM clock_timestamp()-o.created_at) END AS lag_seconds
                FROM context_projection_state s LEFT JOIN projection_outbox o
                  ON o.context_space_id=s.context_space_id AND o.scope_version=s.applied_version+1
                WHERE s.context_space_id=ANY(%s::uuid[]) ORDER BY s.context_space_id""",
                (scopes,),
            ).fetchall()
            if len(rows) != len(scopes):
                raise RuntimeError("Projection state missing")
            return json_values(rows)
