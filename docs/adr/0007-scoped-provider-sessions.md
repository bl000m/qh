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
| Mock default; real sessions denied unless a separate private server receipt and ledger authorize owner/Space/model | A key or a UI checkbox alone is not disclosure/spend authorization; replacing the global provider would obscure mock choice | Normal mock endpoint remains available. No startup HTTP, automatic activation, retry or provider fallback |
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
