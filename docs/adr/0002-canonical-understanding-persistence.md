# ADR 0002 — Canonical understanding and persistence

Update 2026-10-15: [ADR 0003](0003-native-context-engine.md) / QH-30 refines the derived engine
as native Neo4j and explicitly includes semantic entities/relations in PostgreSQL
authority. QH-4 schema/history remains valid; its no-native-engine limit was
ticket-scoped. Graphiti episode mapping is superseded by canonical revision IDs.
The concrete additive schema is still proposed, not applied.

Status: Accepted by the product owner for QH V0.1.
Scope: QH-4; refines ADR 0001's domain semantics without changing dependency direction.
Reference: [Product Contract](../product/QH_PRODUCT_CONTRACT.md).

## Approved decisions D1–D7

PostgreSQL is canonical for original sources, persisted understanding, immutable
revisions, approved projections and governance. Graphiti/Neo4j is a replaceable
derived semantic engine for extraction, semantic relationships and retrieval.
Its state must be rebuildable from QH data without requiring its internal formats
or changing approved human decisions. QH does not reproduce its complete graph,
embeddings or inferred entities/edges in PostgreSQL.

Understanding Items have stable identity, Context Space, category, structured
content, origin, validation and provenance. Categories: objective, current_state,
decision, hypothesis, open_question, constraint, preference, concept, entity,
relationship, uncertainty. Category/epistemic classification and human validation
are separate; a confirmed hypothesis is not automatically a verified fact.

Substantial edits and confirmation create new immutable revisions; AI proposals
never automatically replace the current confirmed revision. Rejected/proposed
revisions remain distinguishable. No full event sourcing or global Context Space
revision is introduced: persisted elements carry their own revisions.

Sources, items and projections each belong to one Context Space in V0.1. Ownership
derives from that space. Projection, Approved Snapshot and Share are distinct;
one projection can yield multiple immutable approved snapshots, each fixing exact
authorized contents/revisions. Each Share targets a specific snapshot. Cross-space
source reuse is future work; no implicit transverse sharing is introduced.

PostgreSQL protects referential integrity, uniqueness, relationship coherence and
immutable data. QH Core decides authorization; the backend enforces it before
adapter access/disclosure. SQL constraints do not implement access authorization.

ContextId denotes a Context Space. Understanding Item, revision, source and
retrieval-result identities are distinct. Replace the ambiguous ContextRecord
with ContextSearchHit using typed revision/provenance references. ContextQuery
requires an explicit set of space IDs; it is a scope constraint, not proof of
authorization. ContextProjection identifies the selected item revisions instead
of using space IDs as source identifiers and preserves source revision provenance.
Hits backed only by sources can be returned before Understanding Items are
persisted; they are retrieval results, not confirmed canonical understanding.
Ports and application contracts remain
framework-free and explicitly injected; no production authorization is added here.

## Minimal QH-4 implementation scope

Create users, context_spaces, sources, source_revisions, understanding_items,
understanding_item_revisions and item_revision_provenance. Identity/metadata are
separate from immutable payloads. Content uses JSONB objects for understanding
and plain original text for source revisions. Revision numbers are positive and
unique per identity. Current item revision is nullable and must be confirmed,
belonging to the same item. Provenance links precise source revisions in the same
space and is frozen with the item revision.

Immutable validation/origin metadata is recorded on revisions; changing validation
creates a new revision with an optional link to its predecessor. This is storage
shape, not a validation workflow. Database migration tests may exercise it directly.
Implementation details of constraints/indexes/triggers remain autonomous within
these invariants, without inventing new domain behavior.

Defer projections and their scope/recipient/purpose fields to QH-14; approved
snapshot storage/approval audit to QH-19; shares, token hashes, expiration/revocation
to QH-20. Their creation can add complete FK/immutability constraints without
breaking the seven foundation tables. This follows the user's D6 instruction to
avoid premature structures and supersedes the original five-table Jira action
list for this implementation; the ticket's reproducibility/rollback Done remains.
QH-8 adds ingestion, source locators and engine episode mapping against revision
IDs; QH-4 already preserves source content and provenance without Graphiti IDs.

No Graphiti integration, validation loop, Projection Engine, links, chat, React
features, full ontology or proprietary Comprehension Graph is implemented.
No automatic API-startup migrations. Tests run against UUID-named isolated empty
databases; the QH application database must not be migrated without separate
explicit authorization. Preserve existing containers and data volumes.

## Consequences and verification

Canonical human understanding survives semantic engine replacement. Persisting
items/revisions/provenance is not duplicating the derived semantic graph. Actual
engine rebuild requires future integration tests; this ADR does not claim that
Graphiti reconstruction has been implemented or verified.

Migration tests cover empty upgrade, downgrade/reapply, immutable revisions and
provenance, cross-space references, unique revisions and confirmed-current pointers.
Fake adapters and import guards verify minimal QH-2 contract corrections and
framework independence. User-approved structural choices are not reopened for
ordinary reversible implementation details.
