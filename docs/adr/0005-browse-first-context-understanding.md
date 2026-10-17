# ADR 0005 — Browse-first Context Space understanding

Date: 2026-10-17. Status: owner-approved product and architectural decision for
QH-12 / PR #13; implementation and verification are recorded separately in the
[QH-12 report](../qh-12-context-understanding.md). Supersedes the search-required
QH-12 experience, not QH-10's query contract. Preserves [ADR 0003](0003-native-context-engine.md),
[ADR 0004](0004-unified-understanding-engine.md), identity/owner policy and the
[Product Contract](../product/QH_PRODUCT_CONTRACT.md). No schema, inference or new
service is authorized by this decision.

> QH does not require users to know what to search for before showing them what their Context Space understands. Browsing is the primary experience; search is a complementary capability.

## Product decisions and rationale

| Decision adopted | Rationale | Alternatives considered | Architectural and UX consequences | Limits / open points |
| --- | --- | --- | --- | --- |
| Browse first; search second | A Space is evolving understanding, not a document-search corpus; opening it must disclose its accessible content without guessing terms | Search-only UI; empty strings/wildcards or hardcoded descriptor queries | Dedicated authenticated read-only browse operation; overview and exploration precede the existing search form | Bounded pages are not a complete semantic summary |
| Preserve canonical distinctions | Content, open descriptors, structural entities/relations, source references, immutable revisions and provenance express different facts | Flattening every object into a document; treating a descriptor as a registered kind | Reuse full canonical DTO/hydration and exact relation revision anchors; no new ontology | A concept is not promoted to an entity unless its canonical shape is entity |
| Deterministic structured preview | Literal excerpts and declared assignments are reproducible without inventing interpretation | Generated narrative; treating any summary-labelled item as validated synthesis | Label preview `Aperçu structuré`; show literal existing text and explicit page scope, UUID order, no importance ranking | A dedicated canonical-summary selection contract is not defined; existing content remains ordinary canonical content. Generative synthesis is future separately authorized work with provenance/governance |
| Data-derived open grouping | Decision/objective/question are examples, not mandatory categories | Fixed category sidebar; automatic classification from text | Exact case-sensitive descriptor buttons, multiple assignments and tentative certainty, unclassified content and structural-kind filters | Groups/counts are explicitly page-local; later pages can reveal more descriptors. A global facet operation is deferred |
| Epistemic states remain distinct | AI proposal, human confirmation, historical revision and descriptor-assignment certainty must not collapse | Latest-proposal-as-current; hiding all proposals when current is empty | Preview current confirmed heads and proposals separately; preserve complete history including rejected revisions; no write/confirm action | Confirmed does not certify real-world truth; descriptor asserted does not confirm content |
| Scoped canonical browse alongside search | No-selector access is a real use case, not a search loophole | Relax QH-10 validation; direct SQL-only UI; unlimited client scan | GET one Space's understanding with mandatory view, bounded UUID keyset and optional exact navigation filters; reuse policy, canonical candidate IDs, graph verification, hydration and readiness recheck even for empty pages | Read-committed pagination is not a frozen multi-request snapshot; concurrent writes may invalidate/fail a page. No as-of semantics |
| Progressive disclosure | Readable context before implementation detail | Raw JSON dashboard; decorative graph | Overview → bounded exploration → item/relation → exact source/revisions/technical details. Keyboard-operable controls and responsive lists | No advanced graph layout or inferred relation is implemented |
| Bounded QH-12 | Delivery must remain reviewable and truthful | Add editing, approval workflow, summaries or demo ingestion to fill gaps | Read-only UI/API and isolated real browser/native tests; existing empty Alice Spaces remain empty | Interactive human validation, editing, LLM synthesis and advanced graph navigation remain future work; persistent demo import needs separate consent |

## Read-only contract and dependency direction

`GET /context-spaces/{id}/understanding` requires `view=current|proposed|history`;
`limit` is 1–100 (default 20), `after_revision_id` is the last returned revision
UUID. Optional navigation filters are exact `descriptor` with explicit
`include_tentative`, `kind=item|entity|relation`, `unclassified`, `item_id`,
`revision_id` and `related_item_id`. Filters intersect, apply **before** pagination,
and never change epistemic state. `unclassified` means no recognizable nonempty
value/asserted-or-tentative assignment, not inferred semantic absence.
`related_item_id` selects explicit incident relation revisions; `item_id` selects
one stable item's revisions; `revision_id` opens an exact retained anchor, normally
in history view. Empty filtered pages have no global absence implication.

The response reuses the QH-10 canonical revision page: content JSON, registered
binding, state/current pointer, temporal bounds, provenance and relation anchors.
Authenticated QH identity → ContextService → shared PolicyService precedes every
private candidate read. CanonicalRepository selects at most limit+1 IDs in one
owned scope. The native engine verifies those exact assertions in Neo4j, validates
canonical fingerprints/evidence/anchors, hydrates the same canonical DTO and
rechecks readiness and policy before disclosure. A missing selected assertion,
pending/error state or concurrent update fails closed, including empty selections.
No SQL-only fallback. Unknown/foreign scope returns uniform 404, untrusted graph
503. No migration, realm change, provider or second persistence/policy system.

QH-10 POST still requires exactly one nonempty text or descriptor selector, and
remains useful for substring/exact-assignment search across explicitly owned
scopes. Browse is a separate Core/application operation; no fabricated query
text, closed vocabulary or implicit unlimited client fetch is introduced.

## Verifiable acceptance and historical boundary

Opening a populated owned Space shows a labelled structured preview without a
query; current and proposed remain visibly distinct, with historical-only and
truly empty states distinguished. Buttons navigate bounded canonical pages and
exact endpoints/history; full revision rendering is reused. Facets never claim
global coverage from a page. Foreign owners are denied before data access; every
page rechecks policy/freshness; unavailable clears visible stale data. Tests must
exercise real isolated SQL 0005, Neo4j, Keycloak and Chromium, plus invalid input,
missing assertions, pending state, later responses, mobile/keyboard and QH-10
regressions. Product decision approval does not establish those tests have passed:
see the report's criterion-by-criterion executed results. No merge/DONE without
owner review. Previous reports and sealed evidence retain their original scope.
