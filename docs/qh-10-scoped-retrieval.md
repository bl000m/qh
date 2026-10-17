# QH-10 — authorized canonical Understanding retrieval

2026-10-17. [Jira QH-10](https://contextlab.atlassian.net/browse/QH-10), branch
`feat/QH-10-scoped-retrieval`, single checkout `/home/ubuntu/qh`, baseline
`2a4eb9bb59cc9d89989169f9f7a89ea194e8a4cc` (QH-9 merged/DONE).
Candidate implementation, **not deployed**. This task stops before merge and Jira
DONE for owner review. No Jira write is implied by implementation or green tests.

## Approved visibility decision

The owner explicitly approved this contract on 2026-10-17 after the STOP AND ASK
required by [ADR 0003](adr/0003-native-context-engine.md) and QH-10:

| Required `view` | Exact selection | Interpretation |
| --- | --- | --- |
| `current` | Revision ID equals that stable item's `current_revision_id` and state is `confirmed` | Current approved understanding, if any; never implicit latest revision |
| `proposed` | All matching revisions whose state is `proposed` | Proposals, including earlier proposed revisions; no automatic supersession inferred from revision number |
| `history` | All retained matching revisions, including current, proposed, superseded confirmed and rejected revisions | Explicit complete-history view; each result retains validation state and `is_current_confirmed` |

There is **no default view** and no automatic fallback from current to proposals.
QH-8 proposals with null confirmed-current pointers are accessible through
`proposed` or `history`; they do not become approved because a query returns them.
History intentionally overlaps the other views. This changes selection, not
owner authorization, publication or canonical validation.

Pagination applies **after** the visibility and query predicates. Temporal bounds
are returned, but temporal/as-of filtering is excluded from this increment by the
same explicit approval. Null bounds remain unknown/unspecified, not infinite
validity or a date inferred from ingestion. No earlier ADR is rewritten.

## One REST endpoint, two selectors

`POST /context-spaces/query` requires the existing OIDC bearer token, internal QH
subject mapping and shared owner PolicyService. It is a read-only query despite
using POST for the explicit multi-Space body. No `ask` or generative route exists.

```json
{
  "context_ids": ["10000000-0000-4000-8000-000000000001"],
  "view": "proposed",
  "descriptors": ["hypothesis", "reversible_pause"],
  "include_tentative": false,
  "limit": 20,
  "after_revision_id": null
}
```

Use exactly one of nonblank `text` (up to 4096 characters) or `descriptors`
(1–100 nonempty strings). Text reuses native case-insensitive substring matching,
without semantic/vector ranking. Descriptors reuse `select_descriptors` and
`CanonicalRepository.descriptor_candidates`: exact case-sensitive **any-of**,
`asserted` assignments by default, explicit `include_tentative=true` to include
tentative assignments. Absence means no descriptor match; no vocabulary, trimming,
normalization, aliases or inferred classifications are introduced. Multiple matching
assignments yield one result. `include_tentative=true` with text is invalid.

Scope is 1–20 UUID Space IDs (duplicates deduplicated); `limit` is an integer
1–100, default 20. `after_revision_id` is an optional UUID keyset cursor. Results
from all requested Spaces are ordered globally by revision UUID, not relevance,
revision number or recency. A bounded one-row lookahead determines whether a
continuation cursor is present. The cursor names the last returned revision and
is only an ordering boundary, not a resource-access capability.

Every page is authorized and freshness-checked independently. Pagination is not
a frozen cross-request snapshot: concurrent writes between pages may change the
matching set, including insertions before the cursor. Callers must repeat the
same scope, selector and view to continue that query. No hidden filtering after
page truncation discards valid matching revisions or creates empty intermediate
pages because of the selected validation view.

Extra payload fields, unsupported query parameters, invalid IDs, missing view,
both/no selectors and invalid limits yield 422. Owner IDs, source/revision IDs,
confirmation fields and temporal predicates cannot be supplied as alternate scope
or authority. Existing metadata CRUD and DELETE 405 are unchanged.

## Canonical response

The illustrative IDs below are synthetic UUIDs. The example is abbreviated to
one proposal; timestamps and field values are not observations of a live model.
`content` is preserved unchanged, including optional descriptors/properties and
QH-8 citation/extraction fields when present. Historical specialized profiles
remain readable without coercion to a generic schema or synthesized descriptors.

```json
{
  "view": "proposed",
  "items": [{
    "context_space_id": "10000000-0000-4000-8000-000000000001",
    "item_id": "20000000-0000-4000-8000-000000000001",
    "revision_id": "30000000-0000-4000-8000-000000000001",
    "revision_no": 1,
    "structural_kind": "item",
    "type_id": "qh.generic.item",
    "type_version": 1,
    "content": {
      "text": "The pilot may reduce waiting.",
      "descriptors": [{"value": "hypothesis", "certainty": "asserted"}],
      "properties": {"basis": "Tentative interpretation"}
    },
    "origin_kind": "ai",
    "validation_state": "proposed",
    "validated_by": null,
    "validated_at": null,
    "current_revision_id": null,
    "is_current_confirmed": false,
    "based_on_revision_id": null,
    "created_at": "2026-10-17T08:00:00+00:00",
    "temporal": {"fact_from": null, "fact_to": null, "valid_from": null, "valid_to": null},
    "relation": null,
    "provenance": [{
      "source_id": "40000000-0000-4000-8000-000000000001",
      "source_revision_id": "50000000-0000-4000-8000-000000000001",
      "revision_no": 1,
      "origin": {"locator": "synthetic://example"}
    }]
  }],
  "next_after_revision_id": null
}
```

`relation`, when present, contains `predicate`, `source_item_id`,
`source_revision_id`, `target_item_id`, `target_revision_id`: these endpoint
revision IDs reference Understanding Items, unlike the Source revision IDs in
provenance. The response exposes exact source revision identity/number and origin,
not an original-byte download endpoint. Literal citations, including turn IDs and
Unicode code-point spans, remain in canonical `content.citations` when available.
Their quote equality is checked against authorized source revisions; equality is
not semantic entailment or human approval. No missing quote is manufactured.

The `certainty` of a descriptor assignment is independent of epistemic state.
No generic classification replaces a historical registered type. See
[flexible persistence](flexible-semantic-persistence.md) for shape/profile/meaning,
source provenance, immutable revisions and the approved model.

## Existing engine, canonical hydration and fail-closed behavior

FastAPI authenticates using QH-5; ContextService authorizes the **whole** explicit
scope through QH-29 before invoking its bound native service/engine. A mixed
owned/foreign scope rejects as a whole; there is no partial response. The same
owner policy and repository ownership defenses are reused, without grants or ACLs.

The existing native text path applies view/cursor predicates before its bounded
graph lookup; the descriptor path applies those predicates in canonical SQL
before the bounded exact-ID Neo4j lookup. Both preserve the native graph/canonical
fingerprint and evidence verification. Structured results additionally check the
selected relations' physical SUBJECT/OBJECT anchors against canonical details.

Canonical bulk hydration supplies the full revision payload, type binding,
provenance, temporal fields, current pointer and exact endpoint identities.
Referenced relation endpoints/current pointers are checked within authorized
Spaces. A freshness fence spans selection **and the final canonical hydration**;
the shared owner policy is rechecked before returning, including empty pages.

| Condition | HTTP behavior |
| --- | --- |
| Missing/invalid bearer or expired token | 401, no retrieval |
| Failed existing general OAuth gate | 403, no retrieval |
| Unknown/foreign Space, mixed denied scope or lost owner access | Uniform 404, no payload/IDs/sources disclosed |
| Query has no authorized matches and projection is ready | 200 with empty items, null cursor and explicit requested view |
| Pending/failed projection, stale graph marker, selected revision/provenance/anchor mismatch, concurrent change during retrieval | Generic 503; no partially verified results |
| Native runtime unavailable/disabled | 503 after the scope gate; no fallback to an unverified SQL-only result |

This reuses the existing text search, descriptor selector, CanonicalRepository and
native runtime/worker. Graph-backed query checks are bounded to synchronization
state and selected candidates/anchors; no ordinary query adds a full-scope graph
audit. Explicit maintenance rebuild remains the recovery mechanism. No provider,
embedding, new index, service, table, migration or canonical write is introduced.

## Acceptance and execution evidence

The Jira Done criteria are tracked separately from publication, review and closure:

| Jira criterion | Verification |
| --- | --- |
| Real protected FastAPI routes retrieve QH-8 proposals by text/descriptor | New REST + real dedicated PostgreSQL/Neo4j suite imports/extracts/publishes the existing QH-8 synthetic fixture with the offline provider, then queries through real routes |
| Four meanings share generic item/1, open/multiple/tentative/absent descriptors | Existing decision/hypothesis/open_question/reversible_pause fixture, tentative expected_effect, entity without descriptors, unknown/case-mismatched descriptors |
| Canonical identity, shape/type, validation, sources and revision distinctions | Exact SQL payload comparison, confirmed-current vs proposed/rejected history, immutable old rows, relation endpoints, known and null temporal bounds, specialized historical binding |
| Scope/authentication/ID isolation and explicit empty/not-ready results | Alice/Bob, two owned Spaces, mixed denial, signed-token OIDC fixtures, spoof/extra fields, foreign cursor, empty pages, real graph corruption and pending/failed state |
| Canonical hydration, freshness, reproducible integration and framework-free DTOs | Actual SQL/Neo4j checks, final-hydration concurrency injection, failure recovery/rebuild, two native application lifecycles with retained IDs, Core import/boundary tests |
| Owner review, merge and Jira closure | PENDING by instruction; target READY FOR REVIEW, never DONE automatically |

Execution results and final head CI are recorded after their actual completion on
the associated PR. Test counts overlap where the strict suite includes targeted
checks and must not be summed. The JWKS transport in dedicated SQL/graph tests is
a fixture; token signatures/claims, SQL identity mapping, owner lookup, HTTP routes,
repository, Neo4j and worker are real. Existing hosted Keycloak tests remain a
separate mandatory CI check. Test-created UUID databases and graph namespaces
are isolated from the VPS; no live container is restarted.

Executed targeted checks: **180 passed**, 5.76 s (HTTP/Core/OIDC/policy/boundaries,
offline container); **18 passed**, 115.11 s (new REST + real SQL/Neo4j on both
schema 0004 and 0005); eight hydration/concurrency guards passed again after the
last relation-shape guard. Ruff, 56 local links/anchors, JSON examples, whitespace
and frozen QH-33/citation audits pass. An initial pagination test wrongly expected
text `pilot` to select only decision revisions; its expectation now preserves the
separate matching hypothesis. No fixture or original extraction was rewritten.

Exact final test/OCI commit `48cbb60627d1947092ec74607222af0e689ea0ca`, test image
`qh10-retrieval:48cbb60627d1947092ec74607222af0e689ea0ca`, immutable image ID
`sha256:6fb804a03725037703797f0c1318e82713b0d3a90cf6b7f020f8965e99f2ea48`.
Built from Git archive with the existing hash-locked Docker recipe, excluding
ignored configuration/secrets. Packaged API/hydration and visibility-pagination
checks on this image: **39 passed**, 18 deselected, 20.07 s, no source mount.
The two new deterministic pagination cases also passed separately (2 passed,
18 deselected, 18.80 s). Deselection is intentional targeted selection, not a
claim that the full suite ran. Application code/configuration is identical to
implementation commit `60b7ddd`; the later test commit adds only these two cases.
The full strict run uses no source mount or provider key; results are recorded
once observed. Later documentation does not alter executable/configuration files.

Reproduction on the explicitly configured dedicated test network, using the
reviewed candidate image (exact identity recorded after the build):

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -w /workspace/apps/api --entrypoint python \
  qh10-retrieval:48cbb60627d1947092ec74607222af0e689ea0ca \
  -u /workspace/scripts/run_qh30_integration.py
```

## Boundaries and remaining limits

QH-10 adds retrieval, not ingestion, chat, confirmation UI, semantic reconciliation,
sharing, collaboration, snapshots, guest links, MCP or frontend. Temporal/as-of
filters need a later approved contract; no unknown-time interpretation is invented.
Exact descriptors do not reconcile synonyms or prove semantic correctness. QH-38
independent human validation remains open; no semantic benchmark/reference/ledger
is changed and no semantic quality improvement is inferred from retrieval tests.

The VPS remains on c723d32 application images/schema 0005. Candidate commits and
CI are not a deployment. No paid inference, persistent migration, new grant or
automatic promotion to confirmed occurs. QH-11 does not start on completion.
