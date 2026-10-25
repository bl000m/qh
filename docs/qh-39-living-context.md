# QH-39 — selected conversation to persistent proposed understanding

## Owner-reviewed closure — 2026-10-20

[PR #18](https://github.com/bl000m/qh/pull/18) was merged by the owner without squash
at `03365668f40bb77142809fa4e0691a318514dbf5`, retaining approved `a2af973` and all
source commits; the merge tree is identical to that approved head. Its four green
CI jobs and prior executed evidence below are reused, not rerun for description edits.
QH-39 is closed in Jira with the owner's authorization. QH-46 status is unchanged.

The Product Owner explicitly confirmed that the fourth QH-45 Mistral call
(ledger 3 → 4) was their manual test from the Mac. This attribution is also recorded
in the PR description and Jira. No audit ledger modification, new inference,
private identifier disclosure or test-result rewrite follows from that confirmation.

Delivered: persistent Source → proposed Understanding, available QH-46 human review
and offline literal extraction. Real semantic extraction in the runtime remains
**NOT IMPLEMENTED**, tracked separately in [QH-51](https://contextlab.atlassian.net/browse/QH-51),
not QH-47 reconciliation. Minimal Demo B QH-40 can use already extracted/verified
synthetic sources. The historical in-review text below retains its dated evidence.

2026-10-19. Demo B block 1. Single checkout `/home/ubuntu/qh`, branch
`feat/QH-39-conversation-understanding`, from main merge
`8c10bf6eb3da3a66b46d5ac6ed8062fcb16edb92` (PR #17, owner-authorized no-squash
merge; all four required jobs green on its source HEAD). QH-49's versioned live
Keycloak image and all QH-50 work are retained. Jira QH-49/QH-50 status transitions
are not inferred from this merge approval. QH-46 remains independently open.

## Implemented behavior and boundary

Alice converses in an owned Space and chooses `Enrichir ce contexte`. A native
accessible dialog previews the exact selected messages; user turns are selected
initially, assistant turns are not. Persistence consent is separate from proposal
inclusion in chat, external disclosure and human confirmation. Saving returns real
source/proposal IDs; `Examiner la proposition` opens the existing canonical detail
and QH-46 controls, including on mobile. A refresh/new authentication loses unsaved
dialogue but not the selected canonical source/proposals.

**Runtime extraction is an explicitly labelled offline literal control.** It copies
selected user utterances as generic proposed items, preserving negation/uncertainty
verbatim, with no semantic classification, splitting or relevance claim. It does not
infer meaning, entities, decisions or dates. Assistant text remains declared
unverified dialogue; in this control it produces no Understanding proposal. This is
a real persistence/validation/review vertical slice, **not** evidence of new LLM
comprehension or a live Mistral extraction. Fixture providers separately exercise
structured entity/relation proposals through the same port/Engine.

The endpoint is `POST /context-spaces/{id}/enrichments`, authenticated and owner-only
through the existing PROPOSE_UPDATE policy. Strict input: conversation/operation
UUIDs, 1–8 identified selected user/assistant turns (exact text up to 4,096 code
points each, offset-bearing browser capture time), explicit `persist_consent=true`.
Total serialized selected payload at most 20,000 UTF-8 bytes. Unknown fields/query
parameters, owner/profile/state/IDs/revision counters, duplicate turn IDs, empty or
NUL text and naive timestamps are rejected. Output names the exact scope,
SourceRevision, proposed revision IDs, replay flag and offline provider mode.

No new schema/migration/service, second Engine or direct graph writer. Selected-source
intake retains QH-8 serialization/IDs while allowing one selected turn. Its private
request-local buffer reuses the unchanged Engine’s `extract`/`publish` methods; the
sealed extractor file and original three-turn importer remain byte-identical. QH-32
exact unique locators and the strict batch validator run before publication.
CanonicalRepository saves source and the whole batch/outbox in one transaction.
Owner policy, graph verification and SQL ownership/readiness checks fail closed.
A provider/429/timeout, invalid citation/sibling or SQL constraint publishes nothing.
An explicitly successful zero-item result records only the consented source and
returns an honest no-proposals message.

Source identity is stable for Space/conversation/operation; each explicit selected
segment is an immutable revision-1 source snapshot grouped by conversation metadata.
The authenticated submitter/server acquisition time are distinguished from declared
roles/browser timestamps and real-world factual time. Same operation/exact payload
replay returns original IDs without provider work, even after service reopen/review;
changed input conflicts. Client selection IDs and SQL locking prevent accidental
replay duplicates. A deliberately new operation is not semantic deduplication.
The prior sources, captures, human decisions and ledgers are never rewritten.

[ADR 0009](adr/0009-selected-conversation-enrichment.md) records rationale,
alternatives and consequences; [architecture](architecture.md) and
[Product Contract](product/QH_PRODUCT_CONTRACT.md#selected-chat-enrichment--owner-qh-39-increment-2026-10-19)
link the bounded increment. Backend provider errors are sanitized. No source/body,
credential or token logging is added. Existing chat snapshot grants require a new
preview/consent after enrichment; they do not authorize extraction disclosure.

## Actual Jira Definition of Done and verification

| QH-39 criterion | Classification / evidence |
| --- | --- |
| Authenticated synthetic user creates/opens Space, submits selected conversation and sees proposed revision linked to original source | Implemented/tested — PASS: real isolated Chromium creation → explicit selection/consent → proposed source-backed revision → refresh/new OIDC login → QH-46 review; no live demo mutation |
| Retrieval after projection returns exact IDs/citations; unauthorized cannot read/send | Implemented/tested — PASS: dedicated SQL/Neo4j tests, policy-before-access, exact Unicode source spans, foreign HTTP denial |
| Chat answer cannot write without Engine; no automatic confirmation | Implemented/tested — PASS: separate explicit route/consent, same Engine/strict validation and atomic repository; null current pointer, proposed state, unchanged review workflow |
| Required mock/replay E2E; live provider only separately authorized | Offline implementation/tested: durable replay, fixture structured relations, provider-error/timeout controls; live extraction NOT IMPLEMENTED/NOT TESTED and no paid call |
| CI and isolated integration green, persistent QH databases unchanged | Targeted tests PASS; final complete CI/preservation results recorded on the PR/Jira after publication |
| Reviewed merge and Jira closure | Pending owner review; no QH-39 merge or DONE |

Targeted executed evidence before publication:

- No-network Docker: **85 PASS** covering the new application/API checks, original
  QH-8/QH-32 capture replays, factory and allowlist boundaries. Ruff PASS.
- Dedicated disposable PostgreSQL/Neo4j: **12 PASS / 37.97 s** across schema 0004
  and 0005 fixtures. Atomic failed-publication rollback, simultaneous replay,
  reopened service, exact source/provenance, proposed/current separation, QH-46
  confirmation, structured entity/relation output, empty extraction, damaged/stale
  graph denial and canonical rebuild. No persistent target fallback is permitted.
- Additional revoked-owner, ambiguous-quote and concurrent-inflight controls: **15 PASS** in the focused application suite (overlaps earlier counts).
- Focused real browser: **1 PASS / 36.6 s**, with create/selected-source consent, proposed provenance, durable replay, refresh/re-authentication, owner confirmation, desktop/mobile screenshots and Bob denial. [Canonical receipt](evidence/qh39-selected-conversation-20261019/README.md). Two earlier focused failures were retained and corrected: pending projection before replay and before post-review detail. Backend freshness was preserved; the UI waits only for bounded authorized GETs after a known local publication.
- Frontend wire regression: **1 PASS**, invalid/foreign receipt, duplicate IDs and provider-mode mislabelling rejected.
- Docker TypeScript app/test typecheck and production Vite build PASS before final
  targeted browser run. Subsequent affected UI checks are recorded in the PR.

Tests are included in the existing native runner and browser campaign, not another
infrastructure. Local targeted browser runs use the existing harness's explicitly
focused mode; they are not represented as a full campaign. The complete final
campaign is the mandatory four-job GitHub workflow on the final published commit.
Its first attempt caught QH-33’s sealed extractor fingerprint: the original file
is now restored byte-for-byte, and the new selected-source intake feeds its existing
methods via a request-local buffer. No historical manifest/audit or required gate
is weakened. The source-representation equivalence and sealed v1/v2 audit pass;
only changed/failed checks are rerun locally before the required updated-HEAD CI.
Actual run/result and any necessary affected failure rechecks are recorded in PR/Jira.
Counts overlap across tests/suites and must not be summed into a larger score.

## QH-46 reuse and remaining limits

Existing pending inbox, exact detail/history and confirm/reject/correct APIs/components
are reused. The SQL/Neo4j test confirms a newly enriched proposal through QH-46,
retains the original source/proposed revision and verifies the new current pointer
and rebuild. Previous QH-50 coverage supplies refusal/correction/concurrency and
mobile behavior. This does not change QH-46 status or implement bulk/conflict matching,
advanced reconciliation/revocation semantics or independent benchmark validation.

Semantic fidelity is not proved by exact citations or successful persistence.
QH-33/QH-38 defects/independent validation remain open. The offline control cannot
show real semantic extraction from conversation; activating an LLM requires a new
purpose/payload-specific disclosure and budget design/authorization. Existing
QH-45 Mistral availability, receipt, credentials, budget and ledger are untouched;
no chat grant is repurposed. No new paid call, provider/write retry or fallback. After a known local publication,
revision detail may perform at most four authorized GETs over 1.5 seconds while the
derived graph catches up; persistent failure remains visible with manual navigation
retry, and navigation cancels further scheduled reads. No SQL-only success.

Unsaved dialogue remains in memory only. User-selected segments persist canonically;
QH-31 Source Vault, multi-author authorship attestation, QH-42 session redesign,
QH-47 semantic identity/contradictions, QH-48 ranking, sharing and MCP remain out of
scope. Existing OIDC access tokens expire after 300 seconds; no renewal is added.
No seed/review/write against the three existing demo Spaces is performed by tests.
