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
requests revocation; reload/logout/tab departure clear local memory. Explicit
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
