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
visibility and at most 40 revisions. Non-current confirmed and rejected revisions cannot enter this formatter.
Explicitly opted-in proposed revisions follow QH-12: all retained proposed revisions
are eligible, including older ones; no active approval queue or latest intent is inferred. Optional proposals preserve their proposed state.

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
The separate chat ledger must carry `purpose="QH-13 contextual chat"`; unmarked
extraction ledgers are rejected without modification. It reuses the stricter existing
budget gate: at most eight
attempts and 0.20 USD total reserved/observed, never QH-8's ledger. The required
EUR/USD upper bound cannot exceed 25, so even the full USD sublimit reserves at most
5 EUR. This is an enforced reservation ceiling under the operator-verified price/
exchange assumption, not a guarantee about taxes or an independently audited invoice.
Do not activate without verifying prices/FX and obtaining the separate approval.

The concrete adapter delegates to the existing MistralProvider with 12,000 input
bound / 1,000 maximum output tokens, JSON mode, pinned model, no retry, redirect or
environment proxy. HTTP/transport/usage failures, including 429, retain accounting and block subsequent
calls. Invalid/incomplete answers are rejected without automatic retry; completed
API usage remains accounted even when answer validation fails.
No real pricing/model compatibility, latency, semantic behavior or invoice was
measured. Tests use HTTP MockTransport and synthetic keys only.

## Verification and Definition of Done evidence

[PR #14](https://github.com/bl000m/qh/pull/14) is the only QH-13 PR. Its current
exact-head checks are authoritative for hosted readiness; no merge or DONE is
authorized. The owner approval covers the minimal CHAT contract, not a claim of
live-model correctness or a personal browser test.

| Ticket/user criterion | Classification and executed evidence | Limit |
| --- | --- | --- |
| Existing services, scoped retrieval and replaceable provider | Implemented and tested: existing QH-2 Protocol checks and architecture tests; `test_chat_service.py`, `test_chat_mistral.py`; concrete adapter with HTTP MockTransport | No new Core provider signature or store; no real external model tested |
| Explicit scope/CHAT before reads and disclosure | Implemented and tested: default current, explicit proposed, foreign owner/scope denial before browse/generation; revocation and concurrent mutation discard output | Owner-only POC; not guest/shared authorization |
| Canonical provenance and no writes | Implemented and tested: `test_chat_pipeline.py`, actual SQL/Neo4j on 0004/0005; canonical snapshot equality, exact source/revision identity, invalid input and pending/unavailable graph | Declared reference membership is not semantic entailment |
| Bounded context, unsupported answers, provider errors | Implemented and tested: 45 final targeted chat tests, network disabled, 0.69 s; whole-record exclusion, explicit partial coverage, duplicate JSON rejection, unsupported/foreign references, no-provider insufficiency, no retry and 429 budget block | Byte-plus-margin bound is not observed API tokens; bounded scans may miss relevant data |
| Native regressions | Implemented and tested locally: strict entry point **594 passed, zero skips, 763.18 s**, reusing dedicated SQL/Neo4j; final small guards separately checked in the 45 targeted tests | Local run collected before the final added regressions; complete latest-head hosted suite supersedes it. Counts overlap and are not summed |
| French chat and explicit browser session boundaries | Implemented; strict TypeScript and **12 frontend contract checks PASS**, 2.0 s; real populated Chromium/Keycloak job **36 PASS**, 59.7 s, including five chat browser cases | Includes temporary follow-up, opt-in reset, sources, real Bob denial, late navigation and provider error cases; no human visual approval implied |
| Existing VPS accessibility and persistent preservation | Implemented and tested: real Alice OIDC/browser opens an existing empty Space, sends mock question, receives 200/insufficient with zero references and null generation time; six container IDs/images/mounts and infrastructure uptime unchanged | No populated persistent demo, no personally attested Mac session; test creates no Space/source/item |
| Lint/security and frozen evidence | PASS: Ruff, strict app/test TypeScript, whitespace, index secret guard, local links; original evidence/ledger trees unchanged | No secret values published |
| Hosted verification | **PASS on executable source `f88e690`**: [run 39060747371](https://github.com/bl000m/qh/actions/runs/39060747371), all four jobs SUCCESS; strict native **599 passed, zero skips, 249.22 s**; browser/contract **36 PASS**, actual outage follow-up **3 PASS** (includes two contract cases), restored-ID browser **1 PASS**. Real OIDC checks **1 PASS/1 live-only deselected** each, plus the browser-job OIDC regression. Final documentation-only HEAD checks are separately required on [PR #14](https://github.com/bl000m/qh/pull/14/checks) | Superseded/cancelled/failed runs are not counted as success |
| Live Mistral smoke and semantic fidelity | NOT TESTED: separate disclosure/spending authorization required | No observed API tokens, charge or model latency; mock duration is not live latency |
| Review/merge/Jira closure | Not complete: stop at technical READY FOR REVIEW after CI; owner review and explicit merge/DONE authorization remain separate | No QH-39/QH-35 or other ticket started |

The initial hosted browser run found an ambiguous test locator matching a quote in
both the declared-source and provided-context panels. It was narrowed to the actual
declared-source panel; no assertion or policy guard was bypassed. The final native
CI includes regression for a saved fingerprint resisting in-place content mutation,
graph failure before provider calls, and rejection of unmarked extraction ledgers.
Existing Starlette/AnyIO deprecation remains non-blocking.

The persistent integrity comparison deliberately uses the retained QH-12 checkpoint,
not a fabricated immediately-before snapshot. Twelve table counts/hashes match
exactly. Two tables additionally retain one empty Space and its projection state,
created at **2026-10-17 18:17:49 UTC**, before QH-12 closure/QH-13 start. Excluding
that pre-existing addition from the comparison only, all retained rows in all
fourteen tables match exactly. No row is deleted or rewritten; the actor/cause of
that pre-task addition is not asserted. The private comparison/probe artifacts stay
outside Git. No QH-8 ledger or reference is changed.

### Reproduction

Use the existing dedicated test network and protected test credentials, never
persistent QH configuration. The local strict command uses the existing dependency
image and readonly app/script mounts; immutable source packaging is executed by
the exact-head hosted workflow. The browser job reuses `test_qh11_browser.py
--understanding` on disposable hosted runners, not a second VPS preview stack.

```sh
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  --mount type=bind,src=/home/ubuntu/qh/apps/api,dst=/workspace/apps/api,readonly \
  --mount type=bind,src=/home/ubuntu/qh/scripts,dst=/workspace/scripts,readonly \
  -w /workspace/apps/api --entrypoint python \
  qh12-api:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  -u /workspace/scripts/run_qh30_integration.py
```

### Optional persistent synthetic demo plan — NOT EXECUTED

The first populated chat is tested only in isolated fixtures/CI. Alice's existing
VPS Spaces remain unpopulated by this task. If the owner later wants a persistent
populated demo:

1. Read-only preflight: authenticated internal Alice identity, the exact chosen
   owned Space, schema 0005, existing pinned profiles, graph readiness and private
   manifest/checkpoint. Do not reassign historical data or repoint the test harness
   at QH. Freeze a clearly synthetic conversation and deterministic source/item
   IDs, literal quotations/spans and input fingerprint using existing QH-8 machinery.
2. Present exact rows/IDs/Space/content/provenance and idempotency behavior. **STOP
   AND ASK before storing the source**. Existing identical source is reused;
   conflicting identity/content stops without replacement or new hidden IDs.
3. Prepare one atomic proposal checkpoint, normally six generic fixture meanings/
   relations with exact source support, using the existing offline fixture provider,
   resolver and CanonicalRepository/outbox. **STOP AND ASK before publication**;
   preserve proposed state and null confirmed pointer. Exact replay returns the
   same IDs; no duplicate batch, type registration, paid call or schema change.
4. Let the existing worker project only that committed batch; verify the same IDs
   through browse and explicitly opted-in mock chat. Retain all source/checkpoint/
   revision evidence and demo data. No cleanup/delete/confirmation is implied.

This is a bounded future operational plan, not QH-39 implementation or present
write authorization. A real Mistral experiment requires its own disclosure/budget
gate even if the fixture data are synthetic.

## Source and verified units

Executable source: `f88e690c27db553d02bcca269744ebb25ddd53da`. The following
archive/report commit changes documentation only; compare executable paths and
verify its own latest-head CI before marking the PR ready. [Recorded measurements](evidence/qh13-chat-20261017/README.md).

| Commit | Purpose and checks |
| --- | --- |
| `46153ed` | Pure bounded Context Builder and deterministic mock; 18 dedicated tests, 18 existing contract and 37 architecture checks |
| `ac838d9` | Approved CHAT/service/REST, concrete gated adapter and ADR; 111 offline checks and 18 real SQL/Neo4j pipeline cases |
| `6bf3b00` | French ephemeral UI, explicit proposal choice, canonical reference validation; strict TypeScript, contract tests, backend bounds/regressions |
| `54b6798` | Architecture/Product Contract/report/deployment boundary; file links, whitespace and secret guard |
| `161b99c` | Correctly scope browser citation assertion to the declared-source panel; strict TypeScript, later full browser CI |
| `6af6081` | Freeze comparison fingerprint, real Bob CHAT denial and graph-before-generation regression; targeted tests and full latest-source CI |
| `f88e690` | Reject accidental reuse of unmarked extraction ledger without modifying it; 45 final targeted chat checks and all four hosted jobs green |

No new feature remains hidden behind a claimed DONE: live provider behavior is
unmeasured, bounded retrieval is not semantic ranking, and references do not prove
entailment. No populated persistent Alice demo, owner Mac session, human semantic
review, merge or QH-13 Jira DONE is claimed.
