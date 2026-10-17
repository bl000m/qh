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

The owner explicitly approved the minimal CHAT contract on 2026-10-17:
owner-only CHAT for one Space, rechecked before retrieval/disclosure;
confirmed-current by default, proposed only after explicit opt-in, no canonical
history; browser-memory dialogue without conversation storage; scoped POST;
mock by default and Mistral disabled until separately approved. See
[ADR 0006](adr/0006-scoped-contextual-chat.md). READ_CONTEXT alone grants no CHAT.

## Responsibilities and product boundaries

The application path is authenticated browser → ChatService → shared
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

## Application, API and UI

POST `/context-spaces/{id}/chat` accepts only `messages` and optional strict boolean
`include_proposed` (false by default). Messages are alternating user/assistant,
ending in user; no system message, owner, view, source, revision selector or second
Space is accepted. Authentication is the existing OIDC/internal QH identity.

The application reads at most two pages of ten per selected view: at most twenty
current revisions and, with opt-in, twenty proposed revisions. It uses three bounded
selection passes (initial, immediately before generation, before disclosure), each
with existing policy/graph/hydration checks. Changing selection/policy or unavailable
canonical/graph state fails closed. No SQL fallback or transaction across generation.
This does not promise atomic multi-page snapshots or lock out concurrent writers.

The response separates `references` (IDs the provider declared and backend resolved)
from `provided_revisions` (all transmitted records), partial coverage, estimated input
bound/context bytes, and observed generation duration when a provider was invoked.
No API token usage is fabricated; no-provider insufficiency has null generation time.

The French UI keeps browsing primary and opens chat only on request. It displays
model, temporary answer, expandable sources using the existing QH-12 renderer,
coverage/insufficiency and loading/errors. Proposal opt-in resets dialogue. Four
questions per discussion are allowed, then an explicit new discussion is required;
no silent dropping of history. Late responses after navigation cannot populate a
new Space. Errors clear prior answers; no automatic retry.

## Configurable Mistral preparation (not activated)

`adapters/llm/chat_config.py` selects mock unless backend `QH_CHAT_PROVIDER=mistral`
is explicitly configured. Mistral additionally requires existing mode-600 JSON
`QH_CHAT_AUTHORIZATION_FILE` and `QH_CHAT_LEDGER_FILE`, and the private API key.
No files are created at startup. The current VPS Compose environment is unchanged
and uses mock. Future activation/configuration is separately authorized.

The authorization records purpose `QH-13 contextual chat`, exact model, allowed Space
IDs, explicit owner authorization, expiry, verified pricing timestamp, pinned input/
output USD prices and a finite positive upper bound EUR/USD. Verification must be
recent (within 24 hours); changed prices or invalid/expired authorization fail closed.
The separate chat ledger reuses the stricter existing budget gate: at most eight
attempts and 0.20 USD total reserved/observed, never QH-8's ledger. The required
EUR/USD upper bound cannot exceed 25, so even the full USD sublimit reserves at most
5 EUR. This is an enforced reservation ceiling under the operator-verified price/
exchange assumption, not a guarantee about taxes or an independently audited invoice.
Do not activate without verifying prices/FX and obtaining the separate approval.

The concrete adapter delegates to the existing MistralProvider with 12,000 input
bound / 1,000 maximum output tokens, JSON mode, pinned model, no retry, redirect or
environment proxy. Errors/429 retain reservations and block subsequent calls.
No real pricing/model compatibility, latency, semantic behavior or invoice was
measured. Tests use HTTP MockTransport and synthetic keys only.

## Verification checkpoint — IN PROGRESS

Executed: 110 offline service/provider/Core/architecture/policy checks passed;
18 dedicated SQL/Neo4j pipeline tests passed on 0004 and 0005, using the existing
fixtures. Native pipeline checks cover actual canonical references, unchanged
canonical snapshots, current/proposed selection, authenticated Alice/Bob, invalid
input and pending/unavailable graph. Counts overlap earlier targeted checks.

Pending: complete strict regression suite, Chromium/real Keycloak CI, archive and
published PR with latest-head green CI. No live Mistral smoke, human semantic review,
persistent Alice demo or owner Mac session is attested. No READY FOR REVIEW/DONE
claim until the technical requirements and publication gates are verified.
