# PostgreSQL schema: deployed 0004 and prepared cleanup

Authority: [ADR 0002](adr/0002-canonical-understanding-persistence.md) and the
[Product Contract](product/QH_PRODUCT_CONTRACT.md). The original uncommitted
five-table draft is replaced by revision 0001_qh_schema; it was never applied
to QH. Its old test results are historical, not evidence for the new schema.

## Current state and authority

- **Persistent QH:** schema `0004_projection_outbox`, native backend/worker at
  `fd50b1ba67061ea95285a2ffce122939524ab93f`. The authorized cutover retained two
  synthetic proposed item revisions with `qh.decision/1` bindings and exact source
  evidence; the database is no longer empty. See dated QH-30 execution evidence.
- **This separate cleanup branch:** generic-profile regressions work on 0004;
  prepared `0005_retire_legacy_category` is tested only on disposable databases.
- **Not authorized:** further persistent writes/migrations/deployment. Do not use
  `make migrate` (moving head) against QH or edit its mounted QH-30 source.

The executable migration files define the SQL. [ADR 0003](adr/0003-native-context-engine.md)
defines current architecture; [QH-30 plan](qh-30-plan.md) retains test evidence and
cutover gates. The following QH-4 sections describe their historical baseline.

## Historical QH-4 foundation (migration 0001)

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

QH-5 prepares the additive `0002_oidc_identities` revision: `user_identities`
maps unique `(issuer, subject)` pairs to `users.id` without changing these seven
tables. It has been tested with upgrade/downgrade on isolated data and
applied to database `qh` with explicit approval on 2026-10-14. See
[identity setup](qh-5-authentication.md).

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

`make migrate` executes Alembic `upgrade head` against the configured QH database and requires explicit user
authorization; API startup never migrates the schema. The user authorized the
initial local upgrade after the isolated verification. See
[implementation checks](verification-qh-4.md) and
[local deployment](verification-qh-4-local-deployment.md) for actual results.

## Superseded proposals and approved QH-30 model

The earlier category-plus-subtype and entity-only endpoint proposals were superseded
before implementation. ADR 0003 records the succession; no historical migration or
immutable payload was rewritten. Graphiti episode mappings in the historical QH-8
list above are superseded by canonical item/source revision IDs.

QH-30 implementation (isolated verification followed by authorized cutover): migration `0003_native_semantics` adds
three tables: semantic_type_versions, item_revision_types, relation_revision_details.
The entity marker proposal was removed as redundant. Universal endpoints reference
QH-4 item/revision/space triples; temporal metadata belongs to every revision
binding. Pinned schemas/rules and publication guards enforce immutable assembly.
Migrations 0001/0002 are unchanged. Migration 0003 was verified on
qh30-sql-test before its authorized application; persistent QH is now at 0004.
See qh-30-plan.md for compatibility, validator profile, execution evidence and gates.

QH-30 migration 0004 (deployed): projection_outbox + context_projection_state
are operational, not new canonical semantic entities. SQL publication/current-pointer
triggers queue work atomically; per-scope counters, token leases and recovery epochs
support incremental processing. Readiness uses these counters instead of full SQL
snapshot scans. Rebuild still comes from canonical data. Persistent QH is now at 0004, retaining the synthetic smoke records; no database
or volume recreation was performed.


## Prepared 0005 — not deployed

The [post-cutover proposal](qh-semantic-consolidation.md) distinguishes structural
shape, open-ended content and optional specialization. New generic profiles do
not require a schema migration: trusted provisioning can register them on 0004.
They are tested candidates, not automatically registered runtime defaults.

`0005_retire_legacy_category` removes the obsolete column and only its BEFORE INSERT
publication check. It takes a table lock, refuses any non-null historical category,
uses no CASCADE or immutability bypass, and preserves all other locks/constraints/
triggers, registry records, immutable bindings and data. The repository omits the
column on writes/exports on both 0004 and 0005; runtime accepts only explicitly known
schema revisions. The deployed fd50 image requires 0004 and must not be started
against 0005. This needs a separately reviewed image/migration transition.

The eleven immutable v1 seeds stay reproducible in applied 0003 and remain readable
for existing references; they do not prescribe new semantic categories. Do not
rewrite `qh.decision/1` smoke bindings or delete unused registry records to make the
registry count equal three. A future database with non-null legacy categories
requires an explicit preservation decision before removal. Downgrade refuses;
recovery is a reviewed forward repair, preserving actual content.
