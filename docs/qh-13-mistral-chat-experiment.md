# QH-13 — first authorized real Mistral chat experiment

2026-10-18 Europe/Rome (2026-10-17 UTC). **Stopped after the first inference;
no retry. Public provider verified mock.** Same QH-13 branch / PR #14, no merge
or Jira DONE. Application source remains the approved
`4f0f3b23971b0f393c796b5dc4adb3750e531f23`; this increment records evidence only.

## Authorization, preflight and execution

The owner explicitly approved the [original sealed manifest](evidence/qh13-mistral-chat-gate-20261018/manifest.json),
SHA-256 `553b56c219e150bed675fa86c0960a124b2087a99b950098fc82794206cc76c1`,
its three exact synthetic Alice payloads and candidate language instruction.
Authorization covered one metadata GET and three sequential POSTs, no retry,
EUR 5 maximum with the existing stricter USD 0.20 / four-total-attempt envelope.
The manifest remains unchanged, including its historical pre-approval flags;
the dated private consent/ledger authorization audit records the later approval.

Preflight PASS: matching HEAD and manifest/payload hashes, key present without
disclosure, all three exact six-record canonical selections, `proposed` state,
source identity, scope, CHAT, graph readiness and Bob 404 before generation.
Official [model catalog](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
and [pricing](https://docs.mistral.ai/inference/pricing) were rechecked: pinned
`mistral-small-2603`, USD 0.15 input / USD 0.60 output per million standard tokens.
No price/configuration/payload drift. One authenticated model GET returned 200,
the pinned ID and `completion_chat=true`. Billing uses the owner's previously
recorded console confirmation; inference credentials do not independently audit
account billing, taxes, card FX or quota balances. The successful POST establishes
actual inference access for this call, not unlimited future capacity.

The live adapter was bound temporarily in a **process-private FastAPI application
inside the existing backend container**. It reused the real OIDC authenticator,
PolicyService, native authorized ContextService, ContextualChatService, scoped
Mistral adapter, public chat endpoint implementation and canonical hydration. HTTP
entered that same route through an in-process ASGI transport, with Alice's real
OIDC bearer. It was not a browser-to-port-8000 Mistral session. No extra listening
server, container, worker startup, source edit, environment edit or restart was
needed. The public browser endpoint remained mock throughout. This bounded binding
prevented unrelated browser questions consuming the approved request allowance.

The approved candidate system string was loaded only into this temporary process,
with its exact SHA checked. Persistent application wording still requests French;
UI remains French. The outgoing transport checked the entire payload hash against
the approved request immediately before sending, permitted one attempt per phase
and used zero transport retries. Existing pre/post policy/readiness/selection
checks remained active. Full canonical records were reconstructed in preflight.

The **same original separate ledger** was unblocked by an append-only authorization
audit, not recreated or reset. Protected temporary aliases in an already ignored,
build-excluded scripts directory shared its inode with the durable host ledger;
reservation/settlement therefore fsynced the original file before/after HTTP. The
grant expired in one hour; the stopped ledger is blocked and all temporary aliases
were removed after capture. Consent and ledger history remain protected/retained.
The key existed only in the temporary process; no key, bearer or authenticated
trace is published. Original QH-8 evidence/ledger and all Understanding are unchanged.

## Actual calls, usage and stopping condition

| Call / Space | Provider HTTP / QH result | Observed input / output tokens | HTTP latency | Estimated list-price USD |
| --- | --- | --- | --- | --- |
| Model GET | 200; pinned chat model available | No inference usage returned | 0.125 s | Ledger bookkeeping 0; no invoice audit |
| Projet pilote | 200 / **503, invalid revision references** | **3,251 / 234** | **1.582 s** | **0.00062805** |
| Bien-être | NOT EXECUTED after stop | — | — | — |
| Organisation personnelle | NOT EXECUTED after stop | — | — | — |

Total **2/4 attempts: one GET and one POST**, zero retries. API total tokens 3,485,
cached input 0, reasoning output 0, observed service tier `standard`. Requested
output cap 1,000; actual context 6,439 bytes and conservative input bound 8,679
are not observed token counts. The API response ended normally with `stop`.
Cost is `(3251 × 0.15 + 234 × 0.60) / 1,000,000`, calculated from observed usage;
the ledger's historical `observed_usd` field stores that estimate, not a verified
charge. Actual EUR conversion/fees are unknown. The USD 0.0024 reservation covered
the call, and neither budget nor token limit was exceeded. Remaining budget is
**not permission** to continue: the failed QH validation blocks the experiment.
No HTTP 429 or 401 occurred; no Retry-After was returned in the captured allowlist.

The provider returned four `revision_ids`. Only one was a supplied revision ID;
the other three were supplied **stable item IDs**:

| Returned ID | Actual namespace | Corresponding supplied revision, diagnosis only |
| --- | --- | --- |
| `d8141c7a-4d1b-5424-9c9f-93b391ae6767` | Pilot item | `8fbcd4e5-c974-5900-a083-e154611eab2f` |
| `b84ab369-8a74-57ab-853d-00a4990617dc` | Hypothesis item | `2bb9c6ea-6e50-56e8-9c88-7b79b521fd2e` |
| `436fdb87-93ea-535c-a425-f3449d17d0e9` | Open-question item | `ad227e63-c35f-562a-b9b8-a17953c89628` |
| `03b72464-d157-550e-8eae-39431bdf2acb` | Valid pause revision | Same ID |

These are not four valid canonical citations. No ID was repaired or remapped.
The existing decoder rejected the answer; the route returned only the sanitized
503 error. A stable item ID cannot substitute for an immutable exact revision
anchor, particularly after later revisions. The body below was retained for
inspection, **not accepted or shown as an answer by the QH application**.

## Raw answer and provisional semantic assessment

Exact question: **Di che cosa parla questo Context Space?**

> Questo Context Space riguarda una discussione di progetto tra Alex e Sam. Si parla della scelta di avviare un piccolo progetto pilota con il Team Cedar, delle possibili riduzioni dei tempi di attesa grazie al pilota, e della domanda su cosa misurare per valutare l'impatto. Inoltre, viene menzionata la possibilità di prendere una pausa reversibile.

The following is assistant assessment of one synthetic answer against the original
provided records/quotes, **not independent human validation** or a semantic score.
The complete raw JSON and all six supplied records are in the
[trial archive](evidence/qh13-mistral-chat-trial-20261018/README.md).

| Dimension | Observation and limitation |
| --- | --- |
| Answers the question | Raw text gives a coherent description of the Space topic; unlike the mock, it is not merely three extracts. One answer does not establish general conversational ability |
| Uses authorized content | Pilot/Team Cedar, possible waiting reduction, measurement question and possible pause occur in supplied quotes. Alex/Sam occur in source turn locators. No outside Space content was observed |
| Proposed versus confirmed | **Fails explicit distinction:** all six records are proposed, but the answer never says unconfirmed/proposed. It does not explicitly claim human confirmation either; the unqualified narrative remains misleading |
| Hypotheses and uncertainty | “possibili riduzioni” and “possibilità” retain expressed modality. This does not fix the omitted governance uncertainty |
| Negation | Not exercised by this project question; the health/personal inference cases were not run. No broad negation pass claim |
| Actors | Describes Alex and Sam as conversation participants, supported by source locators; no sole-person attribution of the collective choice is observed |
| Temporal meaning | No unsupported date asserted. The source report timestamp is not presented as a validity date. This does not test changing decisions or temporal reasoning generally |
| Exact canonical references | **FAIL:** three item IDs and one valid revision ID. Successful JSON mode did not enforce identifier semantics |
| Semantic support | Main clauses have literal topic support in the supplied context. “Per valutare l'impatto” is a plausible explanatory paraphrase, not an explicit source statement. Supported prose does not cure an invalid support-ID set |
| Italian | PASS for this response; proper names remain unchanged |

For **Bien-être** and **Organisation personnelle**, every live-answer quality
dimension is **NOT TESTED**. They were intentionally not sent after the first
invalid answer; there are no replacement responses, imputed scores or token totals.

## Comparison with the mock

The public mock was checked again with all three **exact Italian questions** after
the stop. It still receives six revisions and declares three valid revision IDs
per Space; those declared IDs need not make the excerpts relevant to the question.
For the project question, its output is:

> Mode mock : extraits conservés, sans analyse de votre question.
> [Proposé, non confirmé] We can take a reversible pause.
> [Proposé, non confirmé] Alex
> [Proposé, non confirmé] The choice was stated by Alex.

| Aspect | Mock | Observed Mistral project answer |
| --- | --- | --- |
| Question-aware topic explanation | No; deterministic excerpt selection | Yes in raw text, provisional single-case assessment |
| Proposal labels | Explicitly unconfirmed per excerpt | Missing |
| Declared revision membership | Three valid IDs; no semantic relevance guarantee | One valid revision / three wrong-kind item IDs; rejected |
| Input records | Six exact proposed revisions | Same six exact records, approved candidate system |
| Accepted by QH | Yes, clearly labelled mock excerpts | No, 503 fail-closed |

No paired baseline/candidate Mistral comparison, repeated sampling or general
semantic-quality improvement is claimed. Compaction made full fixture coverage
possible; its causal effect on model quality was not measured.

## Preservation and executed checks

PASS: after stop, all three public port-8000 chat calls returned
`qh-mock-extractive/1`, six supplied records each. Process-private mock checks also
passed the exact three payloads and Bob 404 before generation. All **14 PostgreSQL
table inventories**, schema 0005, source/revision/current pointers/outbox, six
container IDs/images/start times/mounts/networks/environment hashes, private .env
and readonly realm remained identical. No worker started in the runner, no restart,
canonical write, auto-confirmation, deployment, migration or other-owner change.

Offline replay of the actual raw answer reproduces the existing decoder rejection;
the evidence audit verifies original payload hash, exact returned content, all four
IDs, usage/cost arithmetic, stop counts and ledger lineage. Existing full source CI
on 4f0f3b2 passed all four jobs (624 native / main browser 38); it is prior source
evidence, not a new live semantic test. Latest documentation-head CI must be checked
separately. Checks and counts overlap; no summed pass total or DONE follows.

## Minimal next experiment and future Mac session — proposal only

Observed failure is **identifier-namespace confusion** plus omitted proposal
labelling. The payload contains both item/revision IDs; whether that caused the
model mistake has not been isolated. Propose a small generic system-prompt revision:
copy only each row's `revision_id` into `revision_ids`, never `item_id`, source IDs
or relation endpoints; explicitly state when all support is proposed/unconfirmed.
Keep the current strict decoder and immutable records. No auto-remapping, retry,
new retrieval, canonical change or new architecture. This would change the approved
payload and therefore needs a **new reviewed manifest and authorization**. It has
not been implemented or tested with another inference here.

Before a brief interactive Mac test, first obtain a valid bounded real-provider
result under a new approved protocol. Then prepare a separate consent/manifest for
one synthetic Alice Space initially, an explicit short time window (e.g. ten
minutes), one optional metadata GET plus at most three POSTs, the unchanged token
caps and a proposed USD 0.01 sub-budget within all existing EUR 5 / USD 0.20 limits.
Use a new linked ledger without resetting this stopped experiment. It must cover
the precise allowed interactive disclosure, not merely reuse this approval for
different questions. Prepare a reviewed backend-only temporary configuration,
preserve the original configuration and rollback, restrict the scope and expiry,
stop on any 429/provider/reference/budget error and restore mock immediately after.
No API key reaches the browser. Applying that configuration is future work requiring
specific authorization, not performed by this report.

Mac procedure after that separate activation: preserve private forwarding
5173/8000/8080, open localhost:5173, log in as Alice, open the one authorized Space,
choose **Discuter avec ce contexte**, explicitly include unconfirmed proposals,
ask only the agreed synthetic questions, verify model label, Italian response,
proposal qualification, **Sources utilisées** versus **Contexte fourni et limites**.
A failed strict response must remain an error, not a repaired answer. Verify mock
again at closure. Current browser access is still mock, not an interactive Mistral
window. QH-39/QH-43 are not started; PR #14 remains open and QH-13 remains En cours.
