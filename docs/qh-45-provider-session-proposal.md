# QH-45 — interactive provider session contract for owner review

**Later owner approval — 2026-10-18:** “Approvo il contratto proposto”. The
single-Space/session/public-ingress proposal below is approved for implementation
and offline tests, not paid inference or live activation. See the current
[implementation and verification report](qh-45-generative-chat.md) and
[ADR 0007](adr/0007-scoped-provider-sessions.md). The initial draft checkpoint and
its pending/not-implemented matrix below are retained as historical evidence,
superseded by the implementation report; they are not the current delivery verdict.


2026-10-18 (Europe/Rome). Implementation starts from the verified QH-43 merge.
This proposal does not enable Mistral or authorize disclosure/spending. The Jira
activity explicitly requires approval of this session/public-ingress contract
before implementing it. Existing QH-13/ADR 0006 responsibilities remain unchanged.

## Proposed session and public ingress

1. Mock remains the default. Selecting Mistral does not send anything to a provider.
   A backend capability response must say whether sessions are enabled; the live
   VPS remains disabled. Simulated real-provider testing is injected only in tests.
2. Preview uses CHAT policy, existing graph-verified canonical selection and the
   pure Context Builder. Show actual context/revision/source records, model,
   proposed/confirmed state, partial coverage and input/output bounds. Owner and
   timestamps come from authenticated server context, never payload claims.
3. Disclosure consent and proposal inclusion are separate controls. Consent covers
   one exact context snapshot plus the explicitly displayed current question and
   temporary dialogue in this Space, not other Spaces/history or future changed
   understanding. Changes to the selected snapshot require a new preview/consent.
4. A scoped grant records authenticated owner, Space, fixed model, include_proposed,
   exact context fingerprint, expiry and lower server budget/call limits. No
   canonical table, source/revision, projection or new persistence system is added.
   Runtime grants are ephemeral; accounting reuses the existing durable ledger.
5. Proposed API additions in the existing backend: scoped POST chat preview,
   POST session consent, GET session status, DELETE session (logical revoke only),
   and explicit session-bound generation. Default existing mock POST remains
   compatible. Session IDs grant no access without the same authenticated owner,
   Space, current CHAT permission and graph freshness checks.
6. Maximum five minutes and never beyond the validated access-token expiry. Do not
   renew tokens or sessions. Change Space/proposal choice, reload, logout, expiry,
   backend restart or explicit revoke invalidates the grant, clears temporary
   dialogue and requires renewed consent; no silent resumption. Client cleanup
   attempts a scoped revocation while its token is still valid, then clears local
   state. If disconnected, immediate server revocation cannot be promised: the
   fixed expiry is the backstop. Explicit revocation requires a server acknowledgement.
7. Proposed default: 3 POST attempts, 0.01 USD per session. Configurable limits may
   only reduce the experiment-wide 8-attempt/0.20 USD envelope and owner-approved
   EUR ceiling; opening another session must not reset the aggregate ledger.
   Reserve conservative input/output cost before disclosure using the existing
   locked, fsynced ledger. Unknown outcomes retain reservation and block further
   calls until reviewed. Grant/session concurrency must not double-spend.
8. No retry, provider fallback or automatic continuation. HTTP 429/401, timeout,
   provider/JSON/reference failure, revocation, stale context or unknown usage
   stops the session. Already transmitted information cannot be recalled by
   revocation. In-flight spend remains recorded; suppress late revoked responses.
9. Exact R1–Rn resolution, canonical warnings and proposed-only disclosure notices
   remain mandatory. References identify declared support, not proven entailment.
   Generated prose remains distinct from canonical Understanding State (QH-39).

## Browser/session consequence

The existing access token lasts 300 seconds. A session opened after four minutes
can have approximately one minute left, not a new five-minute period. Display
remaining authenticated/session time; expiry clears dialogue and requires login
(SSO may help) followed by fresh disclosure consent. A request sent before expiry
may incur cost even if its response cannot be displayed after expiry. No renewal,
BFF or session redesign is included; QH-42 owns that decision.

## Offline acceptance to execute after contract approval

- UI desktop/mobile selects mock by default; selection alone makes zero provider
  calls; separate unchecked disclosure/proposal controls and exact preview.
- Simulated real LLMProvider through the same ContextualChatService, Context Builder,
  PolicyService, alias resolution and ExperimentBudget, with network denied/mocked.
- Alice/Bob, unknown grant/scope/model, denied CHAT and missing consent fail before
  disclosure; exact snapshot/proposed visibility and history exclusions preserved.
- Multi-turn dialogue and cancellation; expiry/logout/Space change/reload/revoke,
  including in-flight revoke; no canonical writes or secret-bearing output.
- Serial/concurrent reservations, cumulative limits across sessions, errors/429,
  malformed JSON/aliases, graph drift/outage and restart fail closed without retry.
- Existing full browser/OIDC/Core/native CI and immutable experiment ledger audits.

## Later first real session — unexecuted protocol

Only after a new owner-approved manifest: one named synthetic Alice Space (initial
candidate Projet pilote), exact current canonical payload/alias/source hashes,
explicit proposed opt-in, model mistral-small-2603, freshly verified price/FX and
server configuration. Proposed maximum 3 sequential questions/0.01 USD and at
most the remaining global envelope. Private existing experiment authorization and
new linked ledger must retain all historical ledgers and counters; no reset.

Freeze first question "Di che cosa parla questo Context Space?". Later question
and dialogue are reviewed before each manual send. No GET/model lookup or extra
call is implicit. Reserve before each POST; stop on the first error, 429, invalid
reference, unknown cost or unexpected payload. Revoke session and restore default
mock immediately; verify data/ledger/configuration. No public activation now.

## Checkpoint status

Session/public-ingress contract: proposed, owner approval pending. No feature
implemented or tested by this document. QH-45 is IN PROGRESS, never DONE/READY FOR
REVIEW while required implementation/tests remain missing. No Jira transition or
new live experiment is implied. QH-49 tracks Keycloak theme delivery separately.

## Verified starting point and checkpoint material

QH-43 / PR #15 is merged by merge commit
`fc8b9b92f54ab2caaf22cb2e1f96bf20cc48c39b`; Jira QH-43 transitioned to
Terminé(e) only after actual merge/reachability verification. Initial requested
HEAD `b1d721a` was verified, then the owner's final bubble-centring condition
added `510f937`; all four required hosted jobs passed before merge. No squash,
rebase or lost ancestry. Reproducible Keycloak theme delivery is [QH-49](https://contextlab.atlassian.net/browse/QH-49),
required before ordinary future container recreation but not blocking QH-45.

The single checkout is `/home/ubuntu/qh`, branch `feat/QH-45-generative-chat`,
created directly from this fast-forwarded main. Guarded dev-stop/dev-up stopped
and resumed only existing frontend/backend containers for branch selection;
PostgreSQL/Neo4j/Keycloak/MCP, root readonly import, private configuration,
synthetic Spaces, original references and both closed ledgers are retained.
No live provider configuration or real session is changed by this proposal.

[Desktop/mobile contract wireframes](evidence/qh45-session-proposal-20261018/README.md)
are explicitly non-integrated mockups, rendered offline with no external requests.
They help review the pending contract; they are not screenshots of implemented
QH-45 functionality. The existing QH-13 application remains unchanged.

| Actual QH-45 Jira criterion | Current classification / evidence |
| --- | --- |
| Propose and obtain explicit session-contract approval | Proposed in this document; owner approval pending, NOT TESTED as an implemented contract |
| Exercise UI/API with simulated real provider | Not implemented; NOT TESTED for QH-45. Wireframes only; no claim of feature readiness |
| Reuse ContextualChatService/PolicyService/builder/aliases/ledger | Existing code read and reuse points identified; new integration not implemented |
| Test permissions, consent, error/revocation, references, budget, no canonical writes | Planned above; NOT TESTED for new session behavior. QH-43/QH-13 baseline checks do not prove this increment |
| First separately authorized real smoke, if approved later | Out of scope now; no consent/spend authorization or request executed |
| Document limits and remaining gates | Implemented: 300-second expiry consequences, session proposal, offline matrix and unexecuted real protocol |
| Review, merge and Jira closure | Not performed; this PR is draft/IN PROGRESS |

Architecture references: [Product Contract](product/QH_PRODUCT_CONTRACT.md),
[architecture](architecture.md), [ADR 0006](adr/0006-scoped-contextual-chat.md),
[QH-13](qh-13-contextual-chat.md) and [QH-43 activation](qh-43-keycloak-activation.md).
This document proposes new session ingress; it does not silently amend those
approved contracts. There is no QH-42 session redesign or QH-39 write workflow.
