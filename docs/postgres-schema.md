# QH-4 PostgreSQL foundation

Authority: [ADR 0002](adr/0002-canonical-understanding-persistence.md) and the
[Product Contract](product/QH_PRODUCT_CONTRACT.md). The original uncommitted
five-table draft is replaced by revision 0001_qh_schema; it was never applied
to QH. Its old test results are historical, not evidence for the new schema.

## Implemented tables

| Table | Data / cardinality |
| --- | --- |
| users | UUID, display_name, metadata status and timestamps; owner identity |
| context_spaces | UUID, owner_id, name, metadata status/timestamps; many per user |
| sources | UUID, context_space_id, name, metadata status/timestamps; one space per source |
| source_revisions | UUID, source_id, context_space_id, revision_no, original text, origin JSONB, created_at |
| understanding_items | Stable UUID, context_space_id, nullable current_revision_id, created_at |
| understanding_item_revisions | UUID, item_id, context_space_id, revision_no, category, content JSONB object, origin_kind, validation_state, validated_by/at, optional based_on_revision_id, created_at |
| item_revision_provenance | Revision-to-source-revision many-to-many, with context_space_id enforcing matching scope |

All revisions have positive numbers unique within their persistent identity.
IDs are caller-supplied UUIDs; timestamps use timestamptz. Immutable rows have
no updated_at: edits/confirmation create new revisions. Identity metadata may
change; callers update updated_at explicitly. No Context Space-wide revision.
No owner_id copies in child entities: ownership derives from the space.
Repeated space IDs on revisions/provenance support composite FK checks and
cannot disagree with their parent; they do not create independent ownership.

Categories are the eleven approved values in ADR 0002. origin_kind distinguishes
human/ai/import. Validation is proposed/confirmed/rejected, separate from category
and structured epistemic content. Confirmed/rejected rows require validation
actor and time; proposed rows have neither. A validator reference records actor
identity, not proof of authorization: QH Core will decide who may validate.

The current item pointer accepts only a confirmed revision of that same item.
Publishing another proposed, rejected or confirmed revision does not move it.
The optional predecessor references the same item. Sources/provenance cannot
cross spaces, including spaces owned by the same user.

## Immutability and atomic persistence

UPDATE, DELETE and TRUNCATE of source revisions, item revisions and provenance
are rejected by database triggers. Revision provenance must be assembled before
inserting its immutable item revision, in the same transaction. Its item FK is
deferred until commit, so incomplete assemblies fail. A transaction-scoped
advisory lock serializes assembly/publication of the same revision ID: concurrent
writers cannot append evidence after publication. This is a storage write rule,
not a validation workflow or an event log. Creating a new revision may copy or
change provenance only as part of that new revision's assembly.

Normal DML protection does not prevent a database administrator from deliberately
disabling triggers or dropping tables. Separate runtime/migration roles are not
introduced in this local POC. Restore/import tooling must obey atomic assembly;
no Graphiti format or ID is necessary to preserve the canonical data.

References: PostgreSQL [CREATE TRIGGER](https://www.postgresql.org/docs/16/sql-createtrigger.html)
and [advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS).

## Deferred features and tables

- QH-8: ingestion, original-source locators and engine episode mapping; existing
  source revisions already preserve original content/origin and provenance IDs.
- QH-14: projections, recipient/purpose/scope/allowlist/expiry contracts.
- QH-19: approved snapshot content, version and approval audit; shares will target
  this immutable snapshot, never mutable projection state.
- QH-20: shares, token hashes, expiration and revocation.

These tables can be introduced with complete constraints by additive migrations.
No empty projection/share shells, embeddings, semantic graph nodes/edges,
ontology, Graphiti implementation or validation service is added by QH-4.

## Repeating checks safely

```bash
make test-migrations
make verify-running
```

Tests run inside backend and create unique qh4_test_* databases from template0.
They require the local PostgreSQL role's CREATEDB capability. Teardown drops only
the exact test-created databases, without FORCE or volume/container cleanup.
The upgrade/downgrade/reapply test verifies unrelated data survives rollback;
normal tests never migrate or downgrade the QH application database.

`make migrate` upgrades the QH application database and requires explicit user
authorization; API startup never migrates the schema. The user authorized the
initial local upgrade after the isolated verification. See
[implementation checks](verification-qh-4.md) and
[local deployment](verification-qh-4-local-deployment.md) for actual results.
