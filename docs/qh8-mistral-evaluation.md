# QH-8 — real Mistral evaluation: resumed, still rate-limited

2026-10-15. Baseline `f1e0ae6` (QH-8 merged). Branch
`feat/QH-8-mistral-evaluation`; no merge, deployment, persistent QH writes or Jira
changes. This is an **attempted real experiment**, not evidence of real-model
understanding quality. Ordinary CI never calls Mistral.

## Frozen inputs and reference

Four new synthetic conversations and their expected evidence were committed in
`a0f85c07a0e2a8f792fde60f90318fe2d5903832` **before all API requests**:
[inputs](../apps/api/tests/fixtures/mistral_unseen_conversations.json),
[reference](../apps/api/tests/fixtures/mistral_evaluation_reference.json).
The input/reference files are separate. Only the source revision text, exact turn
locators and the existing QH-8 instructions are included in model requests; labels,
expected assertions and forbidden inferences are not sent. The reference is
hand-curated by the implementing assistant for human review, **not independently
validated by a person**. It must not be presented as independent human ground truth.
Reference SHA-256: `9290b477832ad8041119acf08b39ab36a44207fb2f590381d0ede86a7f4077e6`.

## Execution limits and original attempt

The official [model card](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
identifies Small 4 as **mistral-small-2603**, input **USD 0.15/M tokens**, output
**USD 0.60/M tokens**, verified on the experiment date. The official
[chat API](https://docs.mistral.ai/api/endpoint/chat) is
`https://api.mistral.ai/v1/chat/completions`; adapter uses JSON mode, temperature 0,
seed 42, one non-streaming completion, no tools or automatic retries.

User-authorized ceiling: **8 total requests / USD 0.20**. The implementation counts
metadata/error requests too. Per completion: at most 6,000 output tokens and a
16,000 input-token conservative bound (UTF-8 bytes plus 256/message, not an exact
local tokenizer; actual reported usage is checked). Worst-case reservation is
USD 0.006/completion. Four planned completions reserve at most USD 0.024.

Observed requests from exact image/source `f01374bc002df6521c2c20952f6e704d9bccf374`:

1. `GET /v1/models/mistral-small-2603`: **200**, exact ID and chat capability verified.
2. `POST /v1/chat/completions` for work conversation: **429**, experiment stopped.

**2/8 total attempts, 1 failed inference request, 0 completed generations.**
No retry, model fallback, second conversation request or citation repair occurred.
At this original checkpoint, the durable ledger was blocked and preserved the consumed attempts and USD 0.006
worst-case reservation. The provider returned no token usage for the failed call;
**actual tokens and invoiced cost are unavailable**, not asserted to be zero.
Six request slots remained unused at that checkpoint. The reviewed resumption below retains both original attempts.

[Mistral documents 429 as a rate-limit error](https://docs.mistral.ai/resources/error-glossary).
This observation does not distinguish request-rate, token-rate, organization quota
or a temporary provider condition. Initial code retained status only, so no
Retry-After/provider error code exists for this failed real attempt. The later bounded diagnostics were exercised in the resumption below. No account settings, billing or quota were changed by QH.

Private evidence remains under `/tmp/qh8-mistral-evidence/live-initial`: ledger,
model availability, input/reference hashes, first original source and error class.
No raw completion JSON exists because generation never succeeded. No raw model
JSON, Understanding Item or citation example can honestly be supplied from this run.
The uniquely created SQL database and graph namespace were cleaned by the harness;
source export/evidence remain. Persistent QH services/data were never targets.

## Authorized resumption after reported billing activation

The owner reported PAYG enabled, EUR 10 credit and automatic top-up disabled, and
explicitly authorized one first extraction followed by the remaining three only
if inference worked. The available secret is a **standard inference API key**.
No Admin API key or explicit workspace/organization ID is configured. The
[official key documentation](https://docs.mistral.ai/admin/identity-access/api-keys)
states that keys belong to a fixed workspace and use organization billing/quota;
[administrative access](https://docs.mistral.ai/admin/admin-api/overview) requires
separate privileges. QH therefore **could not independently verify the workspace
identity, its billing activation, balance or invoice**. The owner's statement is
separate from the operational inference test. No speculative admin requests were
made and no extra metadata request consumed the remaining request allowance.

Exact resumption code/image: `e2fde579b1bef86b8bfbf9fb0c12b476f998849a`,
`qh8-mistral:e2fde579b1bef86b8bfbf9fb0c12b476f998849a`, inspected image ID
`sha256:48c8c806107876c866cc6b5d1fd4da6ef2cd209493c426132cf3a6adaf913432`.
Built from that exact Git archive, without local credentials in its context.
Model, prompt, token caps, four conversations and frozen provisional reference
were unchanged. Dataset SHA-256 remains
`b3092510b443d0651ed4006d5a0164135da140f9ddad1edd171d5f1b8c1edf9a`.

The original `/tmp/qh8-mistral-evidence/live-initial/ledger.json` remains
**authoritative**. Its blocked state was reconciled once under a lock: retained
both original calls byte-for-byte as records, retained USD 0.006 uncertain reserve,
recorded UTC time/reason/previous-state hash, then allowed one new reservation.
A private before-reconciliation snapshot was saved. No reset, replacement ledger,
refunded slot or erased failed reservation was used.

At approximately **2026-10-15 20:20 UTC**, the single new work-conversation request
returned:

```json
{
  "http_status": 429,
  "code": "1300",
  "type": "rate_limited",
  "message": "Rate limit exceeded",
  "latency_seconds": 0.45021407600142993,
  "headers": {}
}
```

Latency is observed client-side elapsed HTTP time, including connection setup;
there was no completion. Neither `Retry-After` nor any allowlisted request-ID/
request-rate/token-rate header was supplied. Only bounded, sanitized diagnostic
fields were retained; the API key and complete error headers/body were not logged.
**Stopped immediately: no retry and no requests for the other three conversations.**
The original ledger is blocked again with **3/8 attempts**, two rejected inference
requests, **0 successful generations** and **USD 0.012 total uncertain reservation**.
Five request slots remain unused, but are gated until a separately reviewed
resumption. The USD 0.012 is a conservative budget hold, **not an observed charge**.

| Request | HTTP | Input tokens | Output tokens | Invoiced API cost | Observed latency | Budget reserve retained |
| --- | --- | --- | --- | --- | --- | --- |
| Original model metadata | 200 | N/A | N/A | Not independently queried | Not instrumented | USD 0 |
| Original work inference | 429 | Not reported | Not reported | Unknown | Not instrumented | USD 0.006 |
| Resumed work inference | 429, code 1300 | Not reported | Not reported | Unknown | 0.450214 s | USD 0.006 |

No token-based charge can be calculated for either rejected inference: usage was
not returned. Do not replace missing token/cost values with zero. No EUR/USD
conversion or independent balance/account verification was performed.

The response establishes an active **rate/quota rejection**, not its exact cause.
Organization/workspace limits, a token/request quota or billing activation not yet
reflected for this key are possible explanations, **not findings**. Positive credit
alone does not prove this key has usable inference quota. Next operational check
is in the Mistral console: match the key's workspace and billed organization, inspect
its effective Limits/Usage and activation status; use the sanitized UTC/code when
contacting support if necessary. QH does not change account settings or keep probing.

Private evidence: `/tmp/qh8-mistral-evidence/resumed-work` contains manifest,
resumption metadata, original source, ledger snapshot, sanitized error and failure
state. The source committed on the disposable SQL database before inference;
inspection found **1 source revision, 0 Understanding Item revisions and all four
scope counters at desired=applied=0**. No publication, outbox intent or partial item
batch followed the failure. The harness removed only its own disposable database
and graph namespace, retaining these evidence files; persistent QH was not targeted.
There are **no four model JSON outputs, Understanding Items or generated citations**
to save: no generation succeeded. The unreturned conversations were not evaluated.

## Evaluation matrix — no semantic measurements fabricated

| Conversation | Expected reference elements | Correct | Omitted | Unsupported | Actual outcome |
| --- | ---: | --- | --- | --- | --- |
| Work project | 8 | N/A | N/A | N/A | Original and resumed inference both HTTP 429 |
| Evolving project | 7 | N/A | N/A | N/A | Not requested after stop |
| Personal context | 7 | N/A | N/A | N/A | Not requested after stop |
| Italian/French/English | 9 | N/A | N/A | N/A | Not requested after stop |

N/A means **unmeasured**, not zero omissions/hallucinations. Coverage, semantic
precision, entailment/grounding, hallucination rate, temporal interpretation,
uncertainty and apparent-contradiction handling cannot be assessed. Offsets were
not produced, so there is no measured offset failure and no justification to add
an automatic quote resolver now. Once outputs exist, evaluate quote text equality
and source support separately; an exact quote never proves entailment.

| Layer | Finding |
| --- | --- |
| Provider availability | Original metadata succeeds; the single authorized resumed inference still returns 429/1300 |
| JSON/format/citation interpretation | Not reached in the real run |
| QH canonical publication | Not invoked for the failed real extraction |
| Offline safety/pipeline | Mock HTTP + real disposable SQL/outbox/worker/Neo4j tests pass: proposed state, exact source provenance, descriptor hydration and replay; simulated 429 retains source, publishes zero items/intents and stops |
| Real-model canonical/retrieval success | NOT TESTED; cannot be inferred from mock pipeline success |

## Adapter, harness and reproduction

`adapters/llm/mistral.py` implements existing LLMProvider with httpx already locked
in the repository; Core signatures/schema are unchanged. API key only from private
`MISTRAL_API_KEY` environment. Clients use official HTTPS, no redirects, no retries,
60-second timeout (10-second connect), explicit caps and redacted failures. A
mode-600 fail-closed ledger reserves before HTTP, accounts observed usage at list
prices, and blocks after uncertain errors/crash. Synthetic raw successful API JSON
and QH validation results are saved to separate files; provider errors are never
silently converted into successful understanding.

`scripts/evaluate_qh8_mistral.py` creates its own disposable database and graph
namespace on enforced `qh30-sql-test`/`qh30-native-neo4j-test` hosts. It provisions
existing generic profiles, uses unchanged QH-8 validation/resolution, native worker
and policy, then checks descriptor/text retrieval, canonical hydration and denial.
It never reads reference labels into a provider request. Sources commit first;
only accepted output is published. The live mode is prohibited when CI is set.
The offline replay mode uses captured provider content only, not new API calls.

Offline verification with the existing dedicated test credentials:

```bash
# From this feature checkout; only disposable infrastructure, no provider key.
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  --mount type=bind,src="$PWD",dst=/workspace,readonly \
  -w /workspace/apps/api --entrypoint python \
  qh8-extractor:9ccf69b34edaad5249c6a38756addda9a8e99934 \
  -u /workspace/scripts/run_qh30_integration.py
```

Manual interface, **not permission to restart this now-blocked experiment**:

```text
# The command actually used for the single authorized resumption:
python /workspace/scripts/evaluate_qh8_mistral.py --live --resume-from /evidence/live-initial --reviewed-resumption --case work --out /evidence/resumed-work
# Never rerun with another output directory to bypass the now-blocked ledger.
python /workspace/scripts/evaluate_qh8_mistral.py --replay-from /evidence/completed-run --out /evidence/replay-run
```

Run only inside a reviewed backend image with dedicated SQL/graph variables and a
private artifact mount. Pass only MISTRAL_API_KEY from a mode-600 temporary env file
for the live mode, never the complete production .env. No published database ports.
The exact original live image was built from git archive f01374b; this experiment's
ledger path must remain authoritative during any reviewed resumption. The current
blocked run has **no completion capture to replay**. CI mocks are explicitly labeled
mock responses, not invented Mistral outputs or semantic regression evidence.

## Critical conclusion and next priorities

QH's deterministic integrity and offline provider substitution remain tested.
**Real Understanding Extractor reliability is not yet measurable.** A valid key and
an advertised model do not establish usable inference access; this run demonstrates
that operational gap, not good or bad Mistral comprehension.

1. Resolve the actual workspace/organization inference quota in the console before
   another explicitly reviewed resumption. Preserve all **3 attempts and USD 0.012**
   uncertain reservations. Diagnostics are now observed on the real rejection; no
   automatic backoff/retry or model substitution is introduced.
2. Obtain all four successful, untouched outputs and score each reference element,
   every additional unsupported assertion, temporal lifecycle and descriptor certainty.
   Measure citation text/span failures before considering a deterministic uniqueness-
   checked locator step; never repair semantic claims to make acceptance pass.
3. Have a person independently review the provisional reference and assessments,
   including implicit multilingual contradictions and historical versus current facts,
   before exposing any real conversations. Four synthetic samples alone would still
   not establish production reliability or authorize real-data disclosure.

## Executed code verification

- First adapter/dataset + extractor/Core checks: **111 passed**, no external HTTP.
- Final adapter and real SQL/Neo4j mock-HTTP suites: **17 passed**, including
  retained source/zero publications/zero desired-version increments after 429.
- Exact final code image `qh8-mistral:db2c3715a2f57d9478e605e9082f205f1c383102`,
  inspected ID `sha256:158a576bdec5e4b0397994e689205bfa2b19b88f49ad553473fa50beb2cee783`:
  **17 passed, 8.93 s without any bind mount**. No provider key supplied to tests.
- Ruff, whitespace/index guard and staged comparison with private root configuration
  passed without revealing values. 25 local documentation links/anchors resolved.
- Both Mistral test modules are required by the existing strict native CI entry
  point (missing infrastructure or skips fail). Hosted status is reported by this
  feature PR's checks; successful mocks never replace the blocked real evaluation.

Local commits: `a0f85c0` adapter + frozen dataset/reference;
`f01374b` manual isolated live/replay harness (the actual attempted live image);
`db2c371` real SQL/Neo4j mock pipeline and sanitized 429 failure diagnostics.
Subsequent publication documentation does not change these executable artifacts.
Original live image ID:
`sha256:34b63e0b4592445fa72c287114ff5fb75241e88a52d57438f4310342e677340e`.

## Resumption regression evidence

`e2fde57` adds only reviewed ledger reconciliation, case-scoped resumption and
bounded latency/error diagnostics. A subsequent mock-only integration regression
exercises the same original-ledger resumption on real disposable PostgreSQL/Neo4j:
exactly one POST (no metadata GET), old records/reservation unchanged, third failure
reblocks, source retained, no raw completion/partial item batch or next-case request.
These are integrity regressions, **not successful real-model outputs**. Model
quality remains unmeasured and the reference remains provisional, not independently
validated. No incremental extraction, quote repair, optimization or schema change.

Executed after the resumption: **19 targeted tests passed, 9.81 s**, including the
extended one-POST resumption integration case; exact resumption image with **no
source bind mount: 19 tests passed, 8.04 s**. Both runs use real dedicated SQL/Neo4j
and mock HTTP, no real API key. Ruff (without cache on the read-only mount) and Git
whitespace checks passed. Frozen dataset/reference have no diff from a0f85c0.
Private evidence was checked against configured secret values without printing them.
A final read-only comparison confirms all 13 persistent canonical/operational table
counts and hashes, production container IDs/images/mounts/networks and the six
historical Graphiti nodes/relations unchanged; schema remains 0005, zero non-ready
intents. This does not assert a successful real extraction.
