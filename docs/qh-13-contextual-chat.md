# QH-13 — first contextual chat

## Baseline and current decision gate

QH-12 / [PR #13](https://github.com/bl000m/qh/pull/13) was reviewed and merged with
history preserved on 2026-10-17 as `92dc300c03147a7fb7978203d97f2320c8c3051f`.
Jira QH-12 is DONE. QH-13 uses the single checkout `/home/ubuntu/qh`, branch
`feat/QH-13-context-chat`, from that exact updated main. The existing guarded
`dev-stop` / switch / `dev-up` sequence preserved the infrastructure, MCP, private
configuration, readonly realm and existing app container identities.

The [QH-13 ticket](https://contextlab.atlassian.net/browse/QH-13) requires scoped
chat, relevant canonical references, a replaceable existing LLMProvider and mock
tests. A separate real-provider smoke remains subject to explicit disclosure and
paid-call authorization. No permission to infer, persist or confirm understanding
follows from a chat answer; conversational acquisition remains QH-39.

**Pending owner decision:** the current shared PolicyService explicitly denies
CHAT. ADR 0004 states that READ_CONTEXT is not permission for external disclosure.
The proposed minimal contract is owner-only CHAT for one Space, rechecked before
retrieval/disclosure; confirmed-current by default, proposed only after explicit
opt-in, no canonical history; browser-memory dialogue with no conversation store;
a scoped POST adapter; mock by default and Mistral disabled until separately
approved. No CHAT grant or public endpoint has been enabled while this is pending.

## Responsibilities and product boundaries

The intended application path is authenticated browser → ChatService → shared
PolicyService → existing ContextService browse/native engine/canonical hydration →
deterministic Context Builder → existing `LLMProvider.generate`.

The Context Builder is an internal pure formatter. It does not read SQL, operate a
graph, authorize a user, select a provider or write understanding. All revisions
must already have passed canonical retrieval and provenance checks. Source text,
origin metadata and descriptors remain untrusted data, never system instructions.
Only the backend provides canonical reference cards; the model cannot fabricate
those cards or select a foreign revision. Reference membership is mechanically
checkable; semantic support of a free-text answer is not established by membership.
No claim of prompt-injection immunity or measured live-model fidelity is made.

Browsing remains primary under [ADR 0005](adr/0005-browse-first-context-understanding.md).
Chat is a complementary action from the selected Space. QH-10 substring search is
not semantic retrieval. The initial retrieval design is a bounded, deterministic
canonical scan, not relevance ranking, vector search or an unlimited graph export.
An incomplete page/context cannot establish that a decision or fact does not exist.
The UI must distinguish confirmed-current, unconfirmed proposals and generated
answers; an asserted descriptor never confirms a proposition.

## Implemented offline formatter and mock

`app/chat/context.py` formats canonical revisions and dialogue into the unchanged
QH-2 `GenerationRequest`. It enforces one scope, distinct revision IDs, explicit
visibility and at most 40 revisions. Canonical historical/rejected revisions cannot
enter this formatter. Optional proposals preserve their proposed state.

The context JSON is at most 8,000 UTF-8 bytes. Total input has a 12,000 upper-bound
check: UTF-8 content bytes plus 256 per message. This is a conservative engineering
allowance, **not observed tokenizer usage or a model-independent mathematical
proof about provider framing**. The live adapter must check actual returned usage
and stop on any cap violation. Dialogue has at most seven alternating user/assistant
messages ending with a user question, 4,096 characters per message. Excess dialogue
fails instead of silently dropping turns. Oversized canonical records are omitted
whole, with partial coverage explicitly recorded; no quote, negation, date or
proposition is truncated to fit the context. The available canonical source origin
and revision identity are preserved; no original source body is invented.

`adapters/llm/chat_mock.py` is an explicit deterministic extractive demonstration:
it quotes up to three selected records, marks proposed records, and says that it
does not analyze the question. It performs no network request and establishes no
semantic LLM quality. Empty usable context yields an insufficient-context response.

The output decoder requires exactly answer, revision_ids and insufficient_context.
Unknown/duplicate reference IDs, invalid types, extra fields, malformed/oversized
output and unsupported answers without references fail closed. A well-formed
citation does not prove that the cited proposition entails the answer. AI answers
remain plain untrusted text; they are never accepted canonical revisions.

## Paid-provider preparation boundary

No real Mistral request is authorized or executed by this increment. The existing
`adapters/llm/mistral.py` already implements the QH-2 port, JSON output, pinned
`mistral-small-2603`, durable reservation accounting and zero automatic retries.
The frozen QH-8 ledger and artifacts must never be reused or reset for chat.

Before a later real smoke, prepare a separate private authorization and ledger:
fixed model/endpoint `POST https://api.mistral.ai/v1/chat/completions`, exact allowed
synthetic Space/actor, purpose, explicit disclosure, maximum attempts, verified
current input/output prices and an EUR conversion assumption. The total EUR
reservation ceiling is **5 EUR**; count failed and pending attempts conservatively,
reserve maximum input/output before each call, and block on unresolved reservations,
HTTP 429 or any provider error. No automatic retry or parallel paid calls. The
initial candidate limits are 12,000 input bound and 1,000 requested output tokens;
these are protocol proposals, not consumption measurements or new authorization.
Actual usage, latency and price-derived estimates must remain separate from the
invoice. No secret reaches browser, logs, Git or test fixtures. Live activation
requires separately approved backend configuration; key presence alone is never
consent. Future local models implement the same LLMProvider, without a ChatService
or Context Engine rewrite.

## Verification checkpoint — not READY FOR REVIEW

Implemented and tested: pure Context Builder, strict answer-reference decoder and
deterministic offline mock: 18 tests passed with network disabled. This verifies
formatting, visibility rejection, bounds, empty context and output validation; it
is not an authenticated chat API/browser or a live provider test.

Pending: owner decision on CHAT/ingress/disclosure contract; application retrieval
orchestration, API, browser chat, integration/regressions, real Keycloak/Chromium
checks and publication of the single QH-13 PR. No claim of technical readiness,
Jira DONE, semantic correctness or real-provider operation is made here.
