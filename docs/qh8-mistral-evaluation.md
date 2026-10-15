# QH-8 — first real Mistral evaluation (blocked at inference)

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

## Actual execution and spend

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
The durable ledger is blocked and preserves the consumed attempts and USD 0.006
worst-case reservation. The provider returned no token usage for the failed call;
**actual tokens and invoiced cost are unavailable**, not asserted to be zero.
Six authorized request slots remain unused; do not erase/reset the ledger to resume.

[Mistral documents 429 as a rate-limit error](https://docs.mistral.ai/resources/error-glossary).
This observation does not distinguish request-rate, token-rate, organization quota
or a temporary provider condition. Initial code retained status only, so no
Retry-After/provider error code exists for this failed real attempt. Later code
adds bounded code/type/numeric Retry-After diagnostics without retaining arbitrary
error bodies/messages or secrets; that enhancement is offline-tested, not a second
real observation. No account settings, billing or quota were changed.

Private evidence remains under `/tmp/qh8-mistral-evidence/live-initial`: ledger,
model availability, input/reference hashes, first original source and error class.
No raw completion JSON exists because generation never succeeded. No raw model
JSON, Understanding Item or citation example can honestly be supplied from this run.
The uniquely created SQL database and graph namespace were cleaned by the harness;
source export/evidence remain. Persistent QH services/data were never targets.

## Evaluation matrix — no semantic measurements fabricated

| Conversation | Expected reference elements | Correct | Omitted | Unsupported | Actual outcome |
| --- | ---: | --- | --- | --- | --- |
| Work project | 8 | N/A | N/A | N/A | Inference rejected: HTTP 429 |
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
| Provider availability | Metadata succeeds; chat inference is blocked by 429 |
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

Manual live interface, **not permission to restart the blocked experiment**:

```text
python /workspace/scripts/evaluate_qh8_mistral.py --live --out /evidence/unique-run
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

1. Resolve the actual chat rate/quota restriction and review bounded pacing/error
   diagnostics before resuming, preserving the original 2 attempts/budget reservation.
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
