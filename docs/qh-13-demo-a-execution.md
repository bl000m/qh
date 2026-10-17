# Demo A — authorized persistent synthetic seed and verification

2026-10-18, Europe/Rome. Executed on the existing VPS stack after the owner's
explicit authorization of the [plan at d90647a](qh-13-demo-a-plan.md).
This supersedes that plan's **NOT EXECUTED** status for this precise import only.
QH-13 / [PR #14](https://github.com/bl000m/qh/pull/14) stays open for the owner's
Mac review; Jira QH-13 stays `En cours`. No merge, confirmation, paid inference,
QH-39 work, migration, deployment or UX implementation.

## Retained demo Spaces

All three are newly created through Alice's real OIDC-authenticated ContextService;
existing Spaces and historical owners were neither reused nor reassigned.

| Space | Fixture | Browser URL |
| --- | --- | --- |
| Projet pilote | project | [Open Projet pilote](http://localhost:5173/context-spaces/eb122625-1830-4557-b805-473d3b66132a) |
| Bien-être | health | [Open Bien-être](http://localhost:5173/context-spaces/780888ef-6ca6-4eba-b6f9-f1d192795b7f) |
| Organisation personnelle | personal | [Open Organisation personnelle](http://localhost:5173/context-spaces/a0e43025-aad1-457e-86f1-6a813fcd14c4) |

Each Space contains the exact original three-turn conversation, one source revision,
four generic items, one entity and one anchored `stated_by` relation. All **18**
Understanding revisions remain **proposed**; confirmed-current pointers and validation
actors/times are null. There is initially one revision per item/source, not fabricated
successive history. Scripted fixture expectations are not real LLM extraction or
independent semantic validation. Original fixture/capture/reference/ledger files are
unchanged. Other owners' historical data remain unchanged.

## Executed import and recovery evidence

The protected archive is `/home/ubuntu/qh/.local-archive/qh13-demo-a-20261018/`
(directory mode 700; private files 600, sealed manifest/hash 400; ignored and excluded
from builds). It retains the fresh `qh.dump`, archive listing, before/after row hashes,
container/config inventory, creation intents/receipts, sealed exact manifest,
original/derived checkpoints, resolver audits, canonical exports, operator scripts,
browser captures and screenshots. No credentials/tokens or private backups are
published in Git. Tokens remained in memory in the browser probe.

1. Read-only preflight passed: schema 0005, 14 registered profiles including the
   three exact generic definitions, Alice/Bob's two existing OIDC links, all scope
   versions aligned and zero non-ready outbox rows. Fixture bytes match approved
   d90647a. No new identity, registry row or policy was created.
2. Fresh `pg_dump -Fc` archive was listed and restored with exit-on-error into a
   **new database on the already-existing dedicated test PostgreSQL**, using no-owner/
   no-privileges restore. No new QH stack/container/port/volume, and no restore into
   the live database. All **14 tables**, 71 constraints, 104 triggers including internal
   FK triggers, and 12 function definitions were verified. Generated internal FK
   trigger OIDs were normalized. Three CHECK expressions were deparsed with equivalent
   array-versus-element text casts; only those exact equivalent forms were normalized.
   The initial literal catalog comparison rejected these expected representations;
   no source/proposal publication occurred until the structural verification passed.
   Live pre/post-backup inventories were identical. This does not claim restoration
   of original role ownership/ACLs or a full disaster-recovery rehearsal.
3. Under an operator lock, authenticated create returned three UUIDs. Each pending
   intent and successful receipt was durably written before the next create. No
   uncertain POST was retried. The manifest freezes these actual IDs and verbatim
   fixture input before source/proposal publication; simulation IDs are not reused.
4. Existing QH-8 fixture provider and QH-32 explicit resolver prepared the checkpoints
   in memory. All 18 quotes were exact; resolver changed no quote/span. Distinct original
   and derived extraction keys preserve lineage. Publication used UnderstandingExtractor
   and CanonicalRepository, with one source transaction and one atomic six-revision
   proposal transaction per Space. The publication provider cannot generate anything.
5. Identical proposal checkpoints were replayed: same IDs, no duplicate items,
   revisions, sources or intents. Only the existing running worker projected the
   new intents. All three scopes reached desired/applied **6/6**, zero non-ready rows.
6. Canonical hydration verified all 18 source citations/fingerprints, registered
   shapes, proposed states, null confirmation metadata and exact relation anchors.
   Every pre-existing row in all 14 tables remains identical. Browser/chat checks
   subsequently left the entire canonical inventory unchanged.

Observed deltas: +3 Spaces/state rows, +3 sources/source revisions, +18 items/
revisions/type bindings/provenance rows, +3 relation details and +18 outbox revision
intents. No current-pointer events, new users, identity links or registry definitions.
The protected backup and isolated restored database are retained as verification
artifacts; production demo data are intentionally retained for ongoing development.
The restore database is not another deployed QH environment.

[Machine-readable results and exact IDs/hashes](evidence/qh13-demo-seed-20261018/summary.json).
No destructive rollback, queue clearing, owner reassignment or graph reset occurred.

## Real-stack Chromium/OIDC checks

| Check | Observed result |
| --- | --- |
| Alice real login, owned list and opening all three Space links | PASS |
| All six proposed records, open descriptors, entity navigation, relation endpoint navigation, source quotes and revision history | PASS for each Space |
| Confirmed-current view | Empty as expected; no artificial confirmation |
| Chat with proposal inclusion off | Insufficient context, zero provided/declared references, null generation time |
| Explicit proposal inclusion, French question and follow-up | PASS; mock labels proposals, retains selected Space, displays canonical sources |
| Supplied versus declared source panels | PASS: five supplied revisions and three declared references per Space |
| Bob owned list | Excludes all three Alice Spaces |
| Bob direct UI and metadata/browse/exact-revision/chat APIs | PASS; no private Space rendered; 12 API denials, all 404 |
| Missing/invalid tokens | 401 / 401 |
| Web Storage / canonical chat writes | Zero localStorage keys observed; no token persisted by probe; all 14 SQL table inventories unchanged across browser/chat |
| Runtime preservation | Same six container IDs/images/start times/mounts/networks/environment hashes; .env and readonly realm unchanged |
| Personal Mac session | NOT TESTED by the agent; owner verification remains outstanding |

Graph trust was checked through normal authorized browse/chat; the live graph was
not stopped or corrupted. Existing isolated graph-outage regressions remain separate
[QH-13 evidence](qh-13-contextual-chat.md). The real-stack test used existing Alice/
Bob credentials privately, no identity provisioning or new authentication system.

## Context compaction proposal — NOT IMPLEMENTED

The **5/6** limit is confirmed on the actual demo: full canonical provenance/origin
metadata are repeated in every serialized revision. UUID scan coverage is complete
for six records, but the 8,000-byte context cap omits one whole revision. This is not
semantic ranking and the mock does not understand the question: it quotes the first
three eligible excerpts. Reference membership proves scope, not relevance/entailment.

| Space | Current chat: provided / declared | Observed context bytes / input bound | All-six current serialization | Proposed all-six compact serialization / input bound |
| --- | --- | --- | ---: | --- |
| Projet pilote | 5 / 3 | 6,975 / 8,904 | 8,297 bytes | 6,167 / 8,096 |
| Bien-être | 5 / 3 | 7,006 / 8,935 | 8,332 bytes | 6,227 / 8,156 |
| Organisation personnelle | 5 / 3 | 6,940 / 8,869 | 8,351 bytes | 6,196 / 8,125 |

The last column is a measured **offline candidate serialization**, not enabled code,
API tokens, inference usage, model quality or measured improved answers. For these
three initial questions it would fit all six records under the existing limits.
Longer dialogue, larger Spaces or other payloads may still require bounded omission.

Minimal proposal: retain each exact source/provenance object once in an internal
`sources` map keyed by its canonical source-revision ID; revisions keep references
into that map. Keep complete content, literal citations, actor/validation state,
temporal fields, revision IDs and relation anchors. An offline round-trip reconstructed
all six original provider-context records **exactly**, including provenance, for
each case. Do not abbreviate claims/quotes, infer metadata, suppress uncertainty,
raise budgets or alter canonical/public reference DTOs.

Before any later implementation/live experiment, add offline regressions for exact
reconstruction, cross-scope/source collision rejection, relation anchors, whole-record
budgeting and changing selection/readiness. Preserve authentication, CHAT policy,
canonical hydration, full pre/post selection fingerprints, limits 8,000 context bytes /
12,000 input bound, and explicit partial coverage. Apply caps to the actual compact
payload including the source map; do not grant an artificial token discount. This is
an internal formatting proposal, not semantic retrieval or a new persistence model.

## UX backlog and owner hand-off

[QH-43 — Demo A — Environment landing, chat-first Space and QH branding](https://contextlab.atlassian.net/browse/QH-43)
was created with the owner's confirmed scope, dependencies and verifiable acceptance;
status verified **À faire**, no implementation started. QH-13 review/merge/closure and
owner asset delivery precede its start. It covers environment landing, refined Space
overview, primary chat, accessible expandable exploration, original logo/glass sphere,
responsive/keyboard behavior and coherent Keycloak presentation with unchanged OIDC.
Actual theme activation remains separately authorized. No Domain backend or sharing.

On the Mac, keep existing private forwarding **5173 / 8000 / 8080**, log in as Alice
at `http://localhost:5173`, and open the three retained links above. Choose **Explorer : Propositions à examiner** to see all six records (the
overview itself is a five-excerpt preview), inspect sources, then choose **Inclure explicitement les propositions non
confirmées** in chat. Compare **Sources utilisées** (three declared) with **Contexte
fourni et limites** (five supplied). Current UI remains exploration-first pending
QH-43; this data operation does not implement its UX. A full reload needs login/SSO
again because the approved session is ephemeral.

Mistral remains disabled; any synthetic transmission and maximum-EUR-5 experiment
need new explicit consent, exact scopes/payload and verified pricing/FX/caps. QH-39
is not started. PR #14 remains unmerged and QH-13 is not DONE pending owner review.
