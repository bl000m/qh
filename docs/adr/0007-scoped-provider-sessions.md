# ADR 0007 — Scoped ephemeral external-provider chat sessions

2026-10-18. Owner-approved session contract in QH-45 / PR #16, following
[ADR 0006](0006-scoped-contextual-chat.md). Implementation/verification and any
later real-provider activation remain separate gates. No paid-call authorization.

## Decision and rationale

The QH-13 ContextualChatService remains the only chat orchestrator. Its existing
policy/retrieval/build path now exposes an internal preparation operation; explicit
per-request LLMProvider injection reuses identical generation, canonical alias
validation and pre/post freshness checks. There is no second Context Engine or RAG.

The existing backend's chat module owns short-lived disclosure previews/grants.
FastAPI owns strict scoped ingress. Provider adapters own HTTP and durable cost
accounting. OIDC's existing verifier can additionally return the verified expiry;
its original identity-only method remains compatible. A hash binds grants to the
actual verified bearer, without retaining or accepting client-supplied token claims.
Issuer, grant flow, PKCE/state/nonce, roles, token memory and lifetimes do not change.

| Decision | Rationale / alternatives | Consequences and limits |
| --- | --- | --- |
| Mock default; real sessions denied unless a separate private server receipt and ledger authorize owner/Space/model | A key or a UI checkbox alone is not disclosure/spend authorization; replacing the global provider would obscure mock choice | Normal mock endpoint remains available; runtime startup rejects legacy global Mistral mode, so it cannot bypass session consent. Standalone experiment adapters remain reproducible. No startup HTTP, automatic activation, retry or provider fallback |
| Exact canonical preview followed by separate affirmative disclosure consent | READ_CONTEXT/CHAT and proposal inclusion cannot substitute for external disclosure; implicit or blanket consent rejected | Preview exposes exact supplied records/messages, state, source provenance, alias map, coverage/bounds and snapshot hash. Strict input forbids client-selected owner/model/budget |
| One owner/Space/model/token/snapshot per grant | Prevent cross-Space reuse, renewed-token resumption and silent widening after context updates | Recollect/verify canonical graph-backed selection at consent and generation, including rows omitted by bounds. A changed context requires new consent; each manually submitted question/dialogue is additional explicitly displayed input |
| At most five minutes, capped by verified token and private receipt expiry | Extending or silently renewing OIDC would belong to QH-42 | Fixed expiry never extends through status calls. Browser expiry/login, reload, Space/proposal/mode change/new discussion and explicit revoke clear temporary dialogue; no automatic resume |
| Process-memory grants; existing ExperimentBudget ledger for costs only | No canonical session table, new persistence system, Redis, agent framework or transcript storage | One current application process; restart loses grants and requires consent again, while durable accounting survives. Capacity bounded to 1000 unexpired previews/grants; expired entries pruned on new preview. Future multiworker routing requires separate design |
| Default 3 attempts/0.01 USD; configurable private lower/upper limits within aggregate 8 attempts/0.20 USD and approved EUR ceiling | Independent per-session counters alone could reset aggregate spend | One flock/fsync ledger atomically checks session and aggregate reservation before HTTP. Reopening sessions cannot reset calls; pending/crash or HTTP failure remains fail-closed. No public ledger path, credentials or global other-owner usage |
| Server-side revocation and late-answer suppression | Cancelling only React rendering would not revoke disclosure permission | No new sends after acknowledged revoke; in-flight transmitted data/spend cannot be recalled. Local cleanup is immediate; offline browser cleanup cannot promise server acknowledgement, so short expiry is the backstop |

## Public ingress

All routes require authenticated internal QH identity and single-Space CHAT policy.
No owner, model, scope array, key, prompt-system override or budget is accepted.

- GET `/context-spaces/{id}/chat-sessions`: scoped capability/limits; never invokes a provider.
- POST `.../chat-sessions/preview`: existing bounded dialogue plus explicit
  `include_proposed`; returns a short-lived, unconsented preview and exact records/messages.
- POST `.../chat-sessions/{session_id}/consent`: exact snapshot hash and strict
  `disclosure_consent=true`; rechecks context before grant activation, zero inference.
- GET / DELETE `.../chat-sessions/{session_id}`: scoped status / logical revoke,
  with no deletion of canonical data. Status rechecks graph and selection.
- POST `.../chat-sessions/{session_id}/messages`: bounded dialogue and matching
  proposal choice through the original service; unchanged QH-13 canonical answer DTO.

Responses are private/no-store. Foreign identities, Spaces and unknown grants
return non-disclosing 404; invalid input is 422, expired/unavailable grants 409,
provider/graph failures sanitized 503. No fallback or retry is triggered by errors.

## Epistemic and operating limits

Confirmed-current remains default; historical/rejected revisions never enter the
provider payload. Proposed membership, descriptor certainty, confirmation, citation
identity and semantic support remain distinct. Existing mandatory UI warnings derive
from verified canonical states even if generated prose omits them. Answers/dialogue
never create sources, revisions, confirmations or graph writes (QH-39 remains separate).

A 300-second access token may have only seconds left when consent is given. UI shows
remaining grant time and explains reauthentication; requests already sent may incur
cost even if expiry prevents showing the response. No refresh/BFF is introduced.
Preview can be partial/bounded, not semantic-ranked; citations prove membership,
not entailment or prompt-injection immunity. HTTP-simulated testing is not measured
Mistral comprehension, live cost, latency or a billed-workspace compatibility result.

See [QH-45 report](../qh-45-generative-chat.md) and the separately gated
[real-session protocol](../qh-45-provider-session-proposal.md). The actual VPS stays
mock/session-disabled until a new explicit authorization and controlled configuration.


## Later owner amendment — RESULT FIRST, 2026-10-19

The owner now authorizes actual availability, overriding this ADR's historical
preparation-only gate within the named synthetic scope. Separate **provider
availability** (fixed 30 days) from **conversation grant** (unchanged five minutes,
token-bound) and **price freshness** (at most 24 hours). The alternative of daily
receipt/manifest approval is rejected as unnecessary administration within an
already approved budget/scope. No extension, new owner/Space/model or budget reset.

The outbound adapter verifies the fixed official model documentation over HTTPS
without credentials/QH payload, redirects or retry; bounded HTML/structured pricing
parsing rejects unknown/tiered/conflicting/increased prices or retired model. Cache
only a successful fresh result in memory; after expiry/failure deny paid requests.
This is not live billed-workspace/quota attestation: the single authorized smoke
is the actual workspace test. No API model GET is authorized. Document-format
changes may safely make the mode unavailable until the parser is reviewed.

Receipt alteration/removal revokes eligibility; reopening cannot extend its fixed
expiry. An exact context hash pins the authorized six synthetic proposed revisions.
Capabilities additionally show provider expiry/global remaining calls/cost to that
owner/scope only. Preview, consent, CHAT, graph checks, aliases and canonical answer
DTO remain unchanged. Same application/backend, no extra service or canonical table.

A backend-only guarded lifecycle option supports the authorized configuration and
rollback; it cannot target dependencies and verifies all non-target containers.
Private receipt/ledger mount and server-only key are restricted to that backend.
No recurring owner manifest approval is needed; audits remain durable. Prior ADR
sections describe the original checkpoint and are retained, not retroactively rewritten.

## QH-52 owner-approved development amendment — 2026-10-20

The owner explicitly approved contracts A/B/C in
[QH-52](../qh-52-stabilization.md) for implementation and isolated tests.
The normal product interface now offers an authorized real provider or explicit
unavailability. Mock responses require an explicit isolated test/replay binding;
no provider failure falls back to a mock.

Two independent default-off switches prepare bounded browser memory-only refresh
and verified OIDC-session-bound disclosure. The latter requires signed issuer,
subject, sid and auth_time after the same full resource-server validation and QH
identity resolution. Only a derived session hash crosses the authentication port.
Grants remain ephemeral exact-snapshot authorizations, at most thirty minutes and
within the eight-hour work session and private receipt expiry. Access tokens still
expire and every request must present a currently valid verified credential.
Renewal never extends disclosure; changed selection, scope, model or proposal
choice requires new consent. Existing policy/provenance/graph checks remain.

Durable per-work-session accounting uses the verified session hash, not an ephemeral
grant UUID: reconsent, renewed tokens or an application restart cannot reset the
3-attempt/USD0.01 session cap or aggregate8/USD0.20. Historical ledger rows are not
rewritten. No active ledger conversion, flag enablement, realm write, paid call,
new allowlist, duration extension or provider activation is authorized here.
An offline browser cannot guarantee immediate server acknowledgement of revocation;
JWT expiry remains the resource server bound and rotated/revoked refresh credentials
prevent new access tokens. Neither this amendment nor a UI logout claims retroactive
recall of data already transmitted.


## Superseding development AI decision — 2026-10-22

The owner explicitly replaces prior development UI snapshot/session consents and
Alice/Projet pilote eligibility with ordinary AI use by the exact verified owner
OIDC account in all its owned Spaces, present/future. **Envoyer** authorizes one
chat processing request; **Proposer avec Mistral** authorizes one selected-source
UUM extraction. There is no preliminary activation, provider checkbox, mandatory
snapshot preview/confirmation or per-Space/conversation grant. No inference on
opening a page. The active model and transmitted data scope are visible. Only
confirmed-current Space elements and the explicitly submitted dialogue are sent
by default; proposed inclusion is a separate user choice. Chat never confirms or
persists facts; UUM creates proposed revisions reviewed through QH46.

This exception retains verified OIDC/CHAT/owner policy, graph freshness, exact
source validation, immutable revisions and isolated ownership. Only development,
one configured OIDC principal, Mistral AI/mistral-small-2603. Preserve the original
QH45 ledger and aggregate8 requests/USD0.20, old entries and absolute expiry; no
QH51 allocation transfer or reset. Historical3 requests/USD0.01 session limits do
not apply in this mode. Reserve the bounded maximum cost atomically before HTTP;
concurrent requests cannot overspend. No retry/fallback. Insufficient global
reservation returns « Plafond IA atteint. Aucune nouvelle requête ne sera facturée. »
before sending. Previous decisions above remain historical and continue outside
this precisely scoped development mode. See [implementation contract](../qh-51-essai-ia.md).


## Owner amendment — diagnostic POC envelope, 22 October 2026

The owner now authorizes **100 aggregate API attempts / EUR5 maximum**, shared by
ordinary chat and UUM extraction for the same exact verified development account.
Use USD2.50 with the existing conservative EUR2/USD accounting bound: 2.50 × 2 =
EUR5, including all historical spend. ECB reference on 22 October: EUR1 = USD1.1205
([official reference](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.eu.html));
this is a reference, not a guaranteed transaction rate. The EUR2/USD bound supplies
substantial margin; do not expand USD based on a more favorable spot rate.
Original expiry, exact model, all old calls/charges and failure/pending guards remain.
No refill, session ceiling, automatic retry/fallback or new real Codex inference.
The private receipt explicitly records this additive budget amendment; the original
ledger gets new ceiling metadata and an append-only amendment record, never a reset
or alteration of historical calls. Old limits above are historical for this mode.

Private development diagnostics capture provider response JSON before last_exchange
cleanup and application validation results independently of economic completion.
Store only response + safe attempt/check/accounting metadata, never request prompts,
authorization headers or credentials. Exact known-key echoes are redacted and flagged.
Storage is private (0700/0600), outside Git/canonical SQL, expires after one hour,
and is pruned on operations plus every thirty seconds while the app runs. Stopped
apps cannot execute housekeeping; startup purges expired content before serving.
Owner/verified principal/current token/work session/Space CHAT gates every read/delete;
price verification and remaining budget are unnecessary for reading old diagnostics.
The Modèles panel exposes scoped authenticated reads and individual controlled delete.
No raw content in ordinary logs, CI artifacts or repository. Repetitive tests use
synthetic transport only. Validation admission rules are unchanged; the proposed
[functional contract and audit](../qh-51-validation-audit.md) await owner approval.
