# QH-45 — scoped generative chat sessions

2026-10-18 (Europe/Rome). PR #16, branch `feat/QH-45-generative-chat`, single
checkout `/home/ubuntu/qh`, from verified QH-43 merge
`fc8b9b92f54ab2caaf22cb2e1f96bf20cc48c39b`. The owner explicitly approved the
[session contract](qh-45-provider-session-proposal.md) after its initial draft.
[ADR 0007](adr/0007-scoped-provider-sessions.md) and the later Product Contract
amendment preserve ADRs 0003/0004/0005/0006 rather than rewriting their history.
No new real inference, VPS provider activation, migration, realm change or merge.

## Implemented path and exact boundaries

The existing `ContextualChatService` owns preparation and response. `ProviderSessions`
adds only ephemeral preview/consent/status/revoke orchestration around it. CHAT
policy runs before canonical retrieval; native graph freshness/exact hydration,
whole-record bounds, aliases, pre/post selection and policy checks remain in use.
Generation passes a request-local guarded LLMProvider rather than changing a shared
provider instance. The same unchanged canonical answer DTO feeds mandatory warnings.

FastAPI exposes the scoped routes documented in ADR 0007. Strict bodies forbid
owner/model/budget/scope overrides and query parameters; authenticated identity is
internal QH, never an OIDC string or payload owner. The existing OIDC verifier now
also exposes verified expiry for session ingress, with the original identity-only
method intact. Grants bind the SHA-256 of the actual verified bearer; they never
store its plaintext or accept browser expiry claims. No PKCE/state/nonce, issuer,
role/client/redirect, session lifetime, renewal or token storage changes occur.

Runtime startup rejects `QH_CHAT_PROVIDER=mistral`: the legacy global switch cannot
turn the public mock route into disclosure without session consent. Its standalone
QH-13 adapter remains available for historical offline tests.

`GET .../chat-sessions` is denied/disabled by default for real sessions; UI keeps
mock selected. Choosing Mistral without a separate server grant displays unavailable
and cannot infer. Where enabled **only in tests for this checkpoint**, preview
returns exact context/provenance and messages. The question remains visible;
proposal inclusion and disclosure have separate unchecked controls. Consent binds
the snapshot (system instructions plus exact encoded context packet) and requires a matching fresh selection; it does not itself call a
provider. The current context is recollected before/after generation, and changed
selection (including bounded-out rows) requires renewed consent. Later manually
submitted dialogue is untrusted input, not canonical evidence.

Private server authorization fixes model (`mistral-small-2603`), owner/Space
allowlist, short expiry, verified price/FX ceilings and configurable session limits.
The existing ledger is purpose-marked for QH-45 and must exist privately; startup
never creates/resets it or contacts Mistral. Each reservation records a random
session ID, checks per-session and aggregate limits under one lock, and fsyncs
before HTTP. Failed/unknown attempts retain reservations; 429/transport failures
block the ledger. Invalid references/JSON stop the session even after a provider
HTTP success/cost. No retry/fallback. Previous QH-8/QH-13 ledgers are untouched.

## Session lifecycle and POC limits

Default three attempts/0.01 USD, maximum five minutes capped by token and private
server receipt expiry. Private configuration may adjust session limits only within
the aggregate eight attempts/0.20 USD envelope; FX ceiling keeps this within the
previous five-EUR ceiling. Costs are observed-token list-price estimates, not invoices.
Preview/status/consent/revoke themselves are not inference requests.

Scope, proposal or provider change/new discussion clears temporary dialogue and
requests revocation; reload/logout/tab departure clear local memory. Logout starts
revocation with the current token before immediate local cleanup; DELETE uses
keepalive to survive the following OIDC navigation without delaying logout. Explicit
server acknowledgement blocks new calls and suppresses an already in-flight result;
it cannot recall transmitted data or cancel incurred charges. Offline cleanup
cannot promise a delivered DELETE, so fixed expiry is the backstop. A backend
restart loses all grant handles and requires fresh consent without resetting spend.

The existing token lasts 300 seconds. A user consenting after four minutes gets
approximately one remaining minute, not another five. Remaining session time is
shown; expiry removes private UI and requires login/fresh consent. Already sent
requests can incur cost even when expiry prevents display. No silent renewal or
persistent dialogue; QH-42 owns future session changes. Single-process in-memory
grants, 1000-entry bounded capacity and cleanup on new preview are deliberate POC
limits, not a distributed session system. Retrieval remains bounded/non-ranked;
alias membership is not entailment and prompt-injection immunity is not proven.

## Verification

Executed results and final CI are recorded at the review checkpoint below; planned
checks alone are not PASS. All new provider exercises use `httpx.MockTransport` with
the real Mistral adapter and real ledger; no paid network call or model availability,
semantic quality, billing-workspace or live cost improvement is inferred.

The existing native integration entry now collects session unit/API and reused
SQL/Neo4j pipeline tests. Existing browser harness gains `--chat-sessions`, injecting
a test-only factory guarded by its disposable namespace/flags. It retains actual
Code+PKCE, Keycloak, PostgreSQL, Neo4j, canonical state, restore/outage checks and no
published ports. The normal backend never reads a test activation switch.

Reproduction (dedicated test images/credentials only; never substitute VPS env):

```sh
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh45-api:offline --browser-image qh45-browser:offline \
  --frontend-image qh45-web:offline --understanding --qh-login-theme \
  --chat-sessions --output /tmp/NEW-EMPTY-QH45-BROWSER-ARTIFACTS
```

The first native pipeline attempt correctly rejected a test helper issuing a fresh
token for every HTTP call. The fixture was corrected to reuse one verified token;
the grant's token binding was preserved. An initial API error wrapper remapped 404
into 503; the corrected wrapper preserves authorization denials. Neither change
weakens policy, expiry, graph checks or budgets.

## Later real session — not authorized or executed

The [protocol](qh-45-provider-session-proposal.md#later-first-real-session--unexecuted-protocol)
starts with one synthetic Alice Space, exact preview/alias/source hashes, proposed
opt-in, current price/model/billed-workspace verification and a new private linked
ledger/receipt. Initial question: “Di che cosa parla questo Context Space?”. Proposed
maximum three sequential POSTs/0.01 USD, always under remaining aggregate limits;
no GET, retry or extra call is implicit. Review each question and actual payload,
reserve before HTTP, stop on the first error, invalid reference, unknown usage or
drift. Explicitly revoke/end session, return to mock and verify integrity afterward.
A separately approved manifest/configuration window is mandatory. Nothing here
activates public Mistral or starts QH-39/QH-42/QH-49 implementation.

## Review checkpoint: evidence and Definition of Done

[Executed receipts and desktop/mobile consent screenshots](evidence/qh45-provider-sessions-20261018/README.md)
separate isolated simulated-provider testing from actual VPS mock/disabled checks.
The initial wireframes remain preserved as an explicitly non-integrated proposal.

| Jira QH-45 criterion | Classification / evidence |
| --- | --- |
| Explicit owner approval of the session contract | Approved: “Approvo il contratto proposto”; versioned Product Contract/ADR 0007, no inference authorization implied |
| UI/API exercise with simulated real provider, consent/budget checked | Implemented and tested — PASS: existing real OIDC/SQL/graph browser harness; distinct opt-ins, preview, reference resolution, follow-up, reset, revoke and error controls |
| Default mock unchanged until separate live authorization | Implemented and tested — PASS: key presence cannot enable sessions; legacy global Mistral mode rejected at runtime; actual VPS Alice/Bob smoke confirms mock and real-session disabled |
| Canonical references/aliases, epistemic warnings, permissions, errors, cost ledger, no data loss | Implemented and tested — PASS in unit/API/dedicated native pipeline and reused browser/outage/restore checks. Durable reservation, cross-session limits, crash/pending and concurrency regressions; canonical snapshots unchanged |
| Separately authorized real smoke, if approved | NOT TESTED / outside the current authorization: zero real requests. Separate exact manifest, disclosure, budget and configuration review still required |
| Document demonstrated limits and no chat/Understanding persistence | Implemented: reports/ADR/protocol; bounded non-ranked retrieval, five-minute/token cap, single-process grants, citations not entailment, no renewal/BFF or canonical writes |
| Owner review, merge and Jira DONE | Not performed; technical readiness is distinct from DONE. No automatic merge or Jira transition |

The artifact records exact executed counts/image IDs, preserved rows/configuration
and source hashes. Targeted/full counts overlap and are not added. Final hosted
CI must be green on the PR's exact HEAD before technical READY FOR REVIEW; its
immutable run link/verdict is recorded in PR #16's review summary, not inferred
from a previous commit's green checks.

Autonomous corrections remained within scope: API 404 propagation, exact route
allowlists, test tokens reused across a grant, future-token timestamps evaluated
at execution rather than collection, question-first mobile layout, response-ID
validation and revocation before OIDC logout with keepalive. Runtime startup rejects
the old global real-provider switch rather than letting the public mock route
bypass session consent. No authentication checks or required tests were weakened.

Residual POC limits: response semantic correctness is unproven; proposed status
warnings remain mandatory independently of model text. Long dialogue may make the
original snapshot exceed bounds: stop and require a new preview/consent instead of
silently changing sent records. Revocation cannot recall data already sent; offline
cleanup relies on fixed expiry. Grant state is memory-only/single-process, cost
accounting durable. QH-42 owns any future session renewal, QH-39 ingestion remains
excluded, and QH-49 theme delivery must precede future ordinary Keycloak recreation.
No follow-up implementation or new paid session starts automatically.

### Executed local checks

- Strict dedicated PostgreSQL/Neo4j entry point: **707 PASS, zero skips**, 856.74 s,
  on `qh45-api:final`; exact image ID in the artifact. Later bearer-header
  assertions/response guards are additionally covered by current targeted tests
  and the final exact-HEAD hosted suite, not silently attributed to an older image.
- Targeted session/API/architecture **79 PASS**; typed response/composition checks
  **52 PASS**; bearer/API/OIDC **39 PASS**; complete OIDC guard file **30 PASS**.
  These overlap, were executed as separate commands and are not a combined count.
- Local browser full phase **55 PASS**, followed by latest targeted phase **5 PASS**
  (four QH-45 cases plus existing mobile chat-first regression). Existing real
  OIDC **1 PASS**, graph outage/control phase **4 PASS**, post-restore browser
  **1 PASS**. Restore compares every canonical table and rebuild preserves IDs.
  Hosted full browser runs the final keepalive/server-state test at exact HEAD.
- Actual VPS read-only smoke **PASS**: Alice's three capabilities disabled, Bob
  denied three times, six proposed records through the mock, no real send from UI.
  Fourteen QH tables, six runtime identities/configuration/start times/mounts,
  `.env`, readonly import, original assets and closed ledgers remain equal.
- TypeScript, Ruff, configured-secret guard, links/anchors, whitespace and sealed
  archive audit **PASS**. No provider/model availability or real spend test executed.

Reproduction of the strict native run uses only the existing dedicated test network
and its protected test credentials; never use the VPS .env or production DB target.
The receipt's image IDs and the source manifest identify what was checked. Final
hosted CI is linked from PR #16 and must refer to its current HEAD.

### Commit units

The following task commits preserve history. Their checks are covered by the
executed unit/API/native/browser evidence above and final exact-HEAD CI; the
final evidence/documentation commit is the published PR HEAD.

| Commit | Purpose |
| --- | --- |
| `8f5c976` | docs(QH-45): propose scoped provider session contract and offline consent preview |
| `c20ef85` | feat(QH-45): enforce scoped expiring disclosure grants and durable session budgets |
| `f399746` | feat(QH-45): add explicit provider consent UI and isolated browser session acceptance |
| `bc8a3ee` | test(QH-45): evaluate future OIDC claims at execution time |
| `a620e5e` | test(QH-45): retain exact route allowlist for session ingress |
| `0e092e8` | feat(QH-45): expose typed provider-session response schemas |
| `76b43cd` | fix(QH-45): prevent global provider mode from bypassing session consent |
| `93d1fb2` | test(QH-45): share delayed future-claim evaluation across OIDC guards |
| `84c0c19` | fix(QH-45): keep revocation requests alive through OIDC logout |
| `b9b75f9` | fix(QH-45): preserve bearer challenges on session authentication failures |
| `310b8bf` | test(QH-45): verify server revocation after keepalive logout |
