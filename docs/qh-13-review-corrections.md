# QH-13 — corrections after owner Demo A review

2026-10-18 (Europe/Rome). Same branch `feat/QH-13-context-chat`,
[PR #14](https://github.com/bl000m/qh/pull/14), executable correction commit
`35e6218690cb13b26de498ccb5dd951c25fead8a`. The owner personally reviewed the
earlier demo on the Mac and reported these problems. This report records agent
verification of the corrections, not owner acceptance of the revised UI.

## React identity and truthful mock presentation

Understanding and Chat were sibling components sharing `key={space.id}`. Their
keys now include distinct `understanding:` and `chat:` prefixes. Space identity
still remounts both; changing Space clears dialogue, draft, proposal opt-in and
selected understanding detail. No conversation is carried into another Space.

The Playwright regression fails on React duplicate/unique-key console warnings
or page errors. Alice visits all three fixture Spaces and returns to the first,
leaving a dialogue, draft and selected entity before navigation. All reset checks
pass. A separate late-response regression prevents a delayed answer populating
another Space.

Only `qh-mock-extractive/1` uses the heading **Extraits de démonstration — sans
compréhension de la question**. Other providers retain **Réponse de l’IA**; a
browser HTTP stub tests that branch without calling a model. The mock still quotes
three deterministic excerpts. It does not understand or answer the question.
**Sources utilisées** shows declared support separately from **Contexte fourni
et limites**, which exposes the complete canonical records actually supplied.

## Lossless internal context compaction

The Context Builder now uses `qh.chat.context/1`, an internal LLMProvider message
encoding, not a public API or persistence format. `sources` stores each complete
canonical source once by source-revision ID. Each revision keeps its ordered
provenance references. `common_metadata` factors only identical administrative
fields; revision identity, content, descriptors, temporal assertions, relation
anchors and validation state remain explicit. Expansion reconstructs every field
of each canonical revision exactly, including nested source metadata. It is
stronger than preserving only the former provider projection.

Source collisions fail closed across the complete input, including rows later
excluded by budget. A source-revision ID cannot denote different JSON, and a
source ID/revision number cannot denote two different revision IDs. JSON comparison
distinguishes booleans from numbers. Duplicate provenance, dangling or unused
source references, scope mismatch, malformed envelopes and nonfinite or
nonserializable values are rejected. Canonical hydration still establishes source
ownership; the serializer grants no authorization.

CHAT, visibility and pre/post selection/readiness/fingerprint checks are unchanged.
No SQL, public DTO, policy, dependency, retrieval strategy or database write changes.
The existing caps apply to the actual encoded payload: 8,000 UTF-8 context bytes,
12,000 input bound, whole-record omission and explicit partial coverage. The bound
is bytes plus a per-message allowance, **not observed API token usage**. Shared
encoding instructions were added to the system prompt; French remains active.

## Measured before/after on the retained VPS demo

Both observations use the same initial French question and original retained IDs.
The [earlier seed checkpoint](qh-13-demo-a-execution.md) remains historical evidence;
its offline compact candidate was a different projection, not this implementation.

| Space | Provided before → after | Mock-declared | Partial before → after | Context bytes before → after | Input bound before → after |
| --- | --- | --- | --- | --- | --- |
| Projet pilote | 5 → 6 | 3 → 3 | true → false | 6,975 → 6,439 | 8,904 → 8,533 |
| Bien-être | 5 → 6 | 3 → 3 | true → false | 7,006 → 6,499 | 8,935 → 8,593 |
| Organisation personnelle | 5 → 6 | 3 → 3 | true → false | 6,940 → 6,468 | 8,869 → 8,562 |

These are observed mock/browser measurements, not model latency, API tokens,
semantic relevance or improved comprehension. All six fit for these questions;
larger Spaces or longer dialogue can still have partial coverage. Retrieval remains
bounded UUID enumeration without semantic ranking. An entity name or a structurally
valid relation may be an unhelpful excerpt despite valid provenance.

## Verification and preservation

| Criterion | Executed evidence / boundary |
| --- | --- |
| Pure builder/codec/service/provider regressions | PASS: 67 offline Docker tests; no network, 0.62 s |
| Exact provider/public canonical equality | Added real PostgreSQL/Neo4j/API regression, including confirmed-current and explicitly opted-in proposed records |
| Three-Space state isolation and mock/non-mock labels | PASS: two new Playwright tests on the existing VPS, real Alice/Keycloak, 32.5 s; non-mock response is an HTTP test stub |
| Populated Alice navigation, sources, history, relation anchors and follow-up | PASS: all three retained Spaces, six exact citations each, six supplied / three declared, zero React key warnings |
| Bob isolation / invalid credentials | PASS: all three absent from Bob's list, 12 uniform 404 API denials; absent/invalid token 401 |
| Canonical data and runtime preservation | PASS: all 14 PostgreSQL table inventories identical before/after browser/chat; same six container identities/images/start times/mounts/environment; private .env and readonly realm hashes unchanged |
| Static checks | PASS: Ruff, strict TypeScript, whitespace and configured-secret guard |
| Full isolated integration | PASS: `run_qh30_integration.py`, **624 passed, zero skips**, 760.63 s, real dedicated SQL/Neo4j; HTTP mock/replay only |
| Final hosted CI | Verify the latest PR HEAD run; local evidence does not substitute for hosted results |
| Live Mistral and answer quality | NOT TESTED; zero provider requests, activation prohibited pending manifest approval |
| Owner acceptance / merge / Jira DONE | Pending; PR #14 remains open, QH-13 remains En cours |

Run the full existing isolated suite with the dedicated test credentials only:

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --mount type=bind,src=/home/ubuntu/qh,dst=/workspace,readonly \
  -w /workspace/apps/api --entrypoint python \
  qh12-api:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  -u /workspace/scripts/run_qh30_integration.py
```

This uses the existing dedicated test databases/graph, not persistent QH. Hosted
CI additionally runs the full browser/real OIDC and graph outage/restore harness.
No live graph outage, container replacement, deployment, migration, canonical
write, identity provisioning or paid request is authorized or performed here.
The three demo Spaces, prior captures and ledgers remain unchanged. The pre-existing
Starlette/AnyIO deprecation warning remains non-blocking.
[Public observations](evidence/qh13-review-fixes-20261018/README.md) contain no credentials;
protected browser traces/inventories remain in the ignored local archive.

## Proposed real-provider experiment — closed gate

The [sealed manifest and exact requests](evidence/qh13-mistral-chat-gate-20261018/README.md)
cover only the retained synthetic Alice Spaces, one per request, with explicit
proposal inclusion. Three Italian questions include **Di che cosa parla questo
Context Space?** No current record is confirmed; a real answer must preserve that
distinction and declare exact provided revision IDs. This is a future semantic
experiment, not a result of the compaction tests.

The minimum language change is proposed in a separate candidate system file:
normally follow the latest question's language, honoring explicit language requests.
French UI is unchanged; **the active system prompt still requests French**. Owner
approval of the exact manifest, disclosure, candidate wording and scoped activation
plan is required before applying it or sending data. CHAT permission alone is not
external disclosure consent.

A separate durable private ledger is initialized with zero attempts and blocked.
The plan reserves one authenticated model-metadata GET and three sequential chat
POSTs, no retries; stop on 429/error/drift/invalid usage or references. List-price
reservation is USD 0.0072 for three chats, not an observed charge. Existing USD 0.20,
8-attempt and EUR 5 ceilings remain; this manifest tightens attempts to four.
Authenticated account/model access and billing/quota are not independently verified.
The gate README records current official prices, conservative FX assumptions,
expiration and exact hashes. No Mistral configuration or secret is activated.

## Remaining review boundary

Technical regressions and measurements support the corrections, not semantic
correctness of a future model. The current ticket still needs owner review; real
Mistral smoke remains separately gated. UX/branding QH-43 and conversational
acquisition QH-39 are not started. No merge or Jira DONE is requested implicitly.
