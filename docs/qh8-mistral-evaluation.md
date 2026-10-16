# QH-8 — four real full-conversation Mistral extractions

2026-10-16. PR #5, branch `feat/QH-8-mistral-evaluation`, baseline `f1e0ae6`.
**Four HTTP 200 generations, one accepted QH batch out of four.** The experiment
measures the unchanged full extraction, with no incremental delta, optimization,
quote repair, retry or model fallback. No merge, deployment, Jira change or
persistent QH write occurred. Only harness-owned temporary SQL databases and Neo4j
namespaces were written and removed. Captures remain available for review.

## Persistent storage after worktree relocation

2026-10-16 lifecycle maintenance moved this checkout to
`/home/ubuntu/qh8-mistral-evaluation` using `git worktree move`; HEAD, branch,
tracked/untracked/ignored contents and file hashes/modes were verified unchanged
before this documentation-only path update. The four committed captures remain
in `docs/evidence/qh8-mistral-20261016/` with their original manifest hashes.

Original private evidence now lives at
`/home/ubuntu/qh-finalization-evidence/worktree-lifecycle-20261016/mistral-evidence/`.
The old `/tmp/qh8-mistral-evidence` is only a compatibility symlink to those same
files, including the one original ledger, not a copied/restarted experiment.
Historical commands, frozen manifests and original captures retain historical
paths. Do not use archived helpers to resume paid calls without fresh authorization.
No API call, experiment retry, publication push, merge or deployment occurred as
part of relocation. The two review-ready experiment commits remain local pending
separate publication; this path note adds no policy to experimental PR #5.

## Inputs, authorization and billing evidence

The four synthetic conversations and provisional reference remain byte-identical
to their pre-call commit `a0f85c07a0e2a8f792fde60f90318fe2d5903832`:

- [Inputs](../apps/api/tests/fixtures/mistral_unseen_conversations.json): SHA-256
  `b3092510b443d0651ed4006d5a0164135da140f9ddad1edd171d5f1b8c1edf9a`.
- [Reference](../apps/api/tests/fixtures/mistral_evaluation_reference.json): SHA-256
  `9290b477832ad8041119acf08b39ab36a44207fb2f590381d0ede86a7f4077e6`.

The reference was prepared by the implementing assistant, frozen before requests,
and **not independently human-validated**. Assessments below are by that same
assistant. Expected labels/claims were never included in inference requests.

The owner explicitly authorized one first extraction followed by the other three
on successful inference, with **8 cumulative requests / USD 0.20**, no automatic
retry, model `mistral-small-2603`. The owner subsequently confirmed checking the
local key's workspace, active billing and available inference quota in the console
after the last historical 429. This is **owner-confirmed**, not independently
verified using admin credentials. Only the standard inference key is configured.
[Mistral key scope](https://docs.mistral.ai/admin/identity-access/api-keys) associates
the key with a workspace and organization plan; the
[Admin API](https://docs.mistral.ai/admin/admin-api/overview) requires separate
access. No speculative account/admin request or billing change was made.

All four authorized inference requests returned 200; the previous 429 therefore
did not recur in this sample. This does not establish unlimited quota or prove
which earlier account setting caused the historical rejections.

## Preserved ledger and request accounting

Preflight found **3/8 attempts / USD 0.012 uncertain hold**, newer than the requested
2/8 checkpoint. The original metadata request and both failed inference records
were retained unchanged. The authoritative path remains
`/home/ubuntu/qh-finalization-evidence/worktree-lifecycle-20261016/mistral-evidence/live-initial/ledger.json`
following the verified storage relocation below; no replacement ledger or reset.
A locked reviewed reconciliation appended UTC time, actual retained count/hold,
reason and previous-state hash before permitting the new first reservation.
[Before](evidence/qh8-mistral-20261016/ledger-before.json) and
[after](evidence/qh8-mistral-20261016/ledger-after.json) snapshots preserve the trail.

Final state: **7/8 cumulative attempts**, including one historical metadata GET,
two historical 429s and four new POST completions. One unused request slot remains;
no additional request is part of this completed experiment. Each new completion
reserved at most USD 0.006 before HTTP and settled against reported usage.
Historical uncertain holds remain **USD 0.012**. Accounted budget exposure is
**USD 0.01595415** (holds + calculated new usage), below USD 0.20. The holds are not
observed charges. Historical errors supplied no usage, so their actual tokens and
invoiced cost remain unknown.

## Observed usage and latency

Official endpoint: `https://api.mistral.ai/v1/chat/completions`, JSON mode,
temperature 0, seed 42, non-streaming, no tools; unchanged 16,000 input bound and
6,000 output cap. The local input bound uses UTF-8 bytes plus per-message allowance,
not an exact tokenizer. Actual values below come from provider `usage`.
The [official pricing](https://docs.mistral.ai/inference/pricing), rechecked
2026-10-16, lists USD 0.15/M input, USD 0.015/M cached input and USD 0.60/M output.
The personal response reports **232 cached input tokens**, already included in its
653 input total; other responses report zero. No output reasoning tokens are reported.

| Conversation | HTTP | Input tokens | Output tokens | Cache-aware calculated USD | Observed HTTP latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Work project | 200 | 650 | 1,552 | 0.00102870 | 6.766313 s |
| Evolving project | 200 | 667 | 2,180 | 0.00140805 | 8.746279 s |
| Personal context | 200 | 653 | 951 | 0.00063723 | 3.854056 s |
| Italian/French/English | 200 | 703 | 1,239 | 0.00084885 | 5.402201 s |
| **Total** | **4 successes** | **2,673** | **5,922** | **0.00392283** | **24.768849 s summed** |

Latency is client elapsed HTTP time, including connection setup, excluding
validation/publication. Prices multiplied by observed tokens give a **calculated
API charge**, not an independently observed invoice, balance delta or tax-inclusive
amount. The existing ledger conservatively prices all prompt tokens at the
uncached rate: **USD 0.00395415**, overstating cache-aware list-price usage by
USD 0.00003132. Those settled ledger records are preserved, not rewritten for a
discount; budget exposure above deliberately uses the conservative value. No currency conversion was performed. Provider/model and finish reason
checks passed. No new 429, transport error or retry occurred. The final request
used the harness correction below; model, prompt, data and reference were unchanged.

## Raw outputs, candidates and exact provenance

[Evidence index](evidence/qh8-mistral-20261016/README.md),
[deterministic metrics](evidence/qh8-mistral-20261016/metrics.json),
[manual element assessments](evidence/qh8-mistral-20261016/semantic-assessment.json).
Each case contains the parsed original API envelope/request, exact returned JSON
content string, unchanged candidate array, source revision/turns and audited
citations. Raw content was never repaired. Captures are synthetic; no key or
production data is included. A parsed response capture is not a raw HTTP byte log.

| Case and original JSON | Candidates | Exact spans / returned citations | Quotes present literally | Missing evidence | QH batch |
| --- | ---: | ---: | ---: | ---: | --- |
| [Work](evidence/qh8-mistral-20261016/work/output.json) | 9 | 4/9 | 9/9 | 0 | Rejected: mismatched span |
| [Evolving](evidence/qh8-mistral-20261016/evolving/output.json) | 14 | 8/14 | 14/14 | 0 | Rejected: mismatched span |
| [Personal](evidence/qh8-mistral-20261016/personal/output.json) | 5 | 5/5 | 5/5 | 0 | 5 proposed revisions; offline replay pipeline PASS |
| [Multilingual](evidence/qh8-mistral-20261016/multilingual/output.json) | 9 | 6/6 | 6/6 | 3 relations | Rejected: required evidence field absent |
| **Total** | **37** | **23/34 (67.65%)** | **34/34** | **3/37 candidates** | **1/4 accepted batches (25%)** |

All 34 supplied citations name the correct synthetic source revision. All returned
spans lie inside identified turns, but **11 spans do not equal their quote**.
Three relation candidates provide no evidence at all. Literal quote presence and
valid JSON (4/4) therefore do not establish usable provenance or batch validity.
For example, work-1 returns `[6,70)` for a 109-code-point quote actually occupying
`[6,115)`. The original offset is retained; no resolver or second API request was
used. A single invalid citation rejects the whole batch, including valid siblings.
The multilingual batch fails the required-fields check before citation validation;
the six exact spans in that batch are measured separately by the offline audit.

Only the five personal candidates became canonical proposed revisions in a
disposable database, with immutable IDs/provenance, `current_revision_id=null` and
no human validator. Work, evolving and multilingual published zero revisions.
All experiment databases/namespaces were then removed by their owning harness;
exports and original model candidates remain in the evidence directory.

## Separate semantic assessment

Coverage counts **reference propositions retained in candidate text/properties**,
not assertions present only inside a quote. One candidate may cover several
reference elements. This measures textual retention, not semantic precision or
successful canonical retrieval. Errors in descriptors, properties and added
relations are assessed separately even when the source text was copied correctly.

| Case | Reference elements | Retained textually | Partial/inconsistent | Omitted from claims |
| --- | ---: | ---: | ---: | ---: |
| Work | 8 | 8 | 0 | 0 |
| Evolving | 7 | 7 | 0 | 0 |
| Personal | 7 | 7 | 0 | 0 |
| Multilingual | 9 | 7 | 1 | 1 |
| **Total** | **31** | **29** | **1** | **1** |

- **Correctness:** work preserves the 20% goal, two-week pilot, EUR 300 cap, CRM
  restrictions and unanswered access/security ownership. Personal preserves the
  canceled train and the planned walk as separate events. Multilingual preserves
  net 300, gross 360 and ceiling 350, and the 10 EUR excess; the tax-basis explanation
  is retained in relation-2, whose missing evidence still makes it unusable by QH.
- **Omissions:** the multilingual statement that no order is approved appears only
  in item-4's quote, absent from its text/properties and the other claims. It does
  not count as an extracted understanding proposition. This is one omitted reference
  element; no claim of exhaustive omission detection beyond the reference is made.
- **Invented/overstated information:** multilingual item-5 emits
  `discount_applied=true`, although the source only discusses a possible discount.
  This is one definite unsupported property. Evolving relation-1 says “Jo rejects
  Mina's proposal”; the cited collective choice of another trial is weaker than an
  explicit personal rejection. That is an overinterpretation requiring review,
  reported separately from the definite unsupported property.
- **Semantic classification:** evolving-2 copies the decision literally but labels
  it `counter-proposal`. This underrepresents an adopted trial as another proposal.
  Open descriptor vocabulary is permitted: absence of a specific English keyword
  alone is not a failure. The issue is the meaning of this particular descriptor.
- **Temporality:** work retains a date-only deadline without inventing a timestamp.
  Personal uses the two literal timestamps and preserves past cancellation versus
  future conditional intention. Evolving retains proposal, withdrawal, suspension
  and no-return-to-weekly history in text, but attaches its three temporal fields
  to standalone timestamp entities rather than the affected assertions; temporal
  lifecycle is therefore much less structured than the text suggests. No restart
  date is invented. The fixture's acquisition time precedes some narrated future
  dates; evaluation concerns internal narrative order, not real-world chronology.
- **Uncertainty:** personal preserves temporary crowd avoidance, weather dependence
  and unconfirmed attendance without a diagnosis or enduring personality inference.
  Multilingual preserves unassigned discount work and unknown delivery date, but
  its conditional order claim is internally weakened by `discount_applied=true` and
  omission of the explicit non-decision. Descriptor `certainty=asserted` concerns
  the assignment, not confirmation that an uncertain event happened.
- **Provenance quality:** exact offsets, literal quotes, source IDs and entailment
  are distinct checks. The 34 literal quotes do not excuse 11 bad offsets, three
  absent relation citations, or the unsupported discount property. Work relation-1
  connects a pilot-statement item to a goal item for a team/panel management claim;
  universal item endpoints allow that structurally, but entity/relationship quality
  needs review. No structural domain change follows from this finding.

No aggregate hallucination/precision percentage is asserted: candidates mix
multiple propositions, repeated text, properties and relations, and the small
manual reference is not an exhaustive, independent claim annotation.

## Harness interruption and offline correction

The live personal batch validated and published five proposed revisions; worker
sync reached desired=applied=5. Its subsequent retrieval check raised
`AssertionError`: the harness queried `rows[0].content.text` but expected `ids[0]`,
assuming snapshot ordering equaled publication ordering. The failure was in the
measurement code, not HTTP or extraction validation. Original failure/sync exports
are retained separately. No further API request was made while diagnosing it.

Local commit `1ee72f18f1b6cfef7755f2ae5b34a3c09a393dd8` checks the revision belonging
to the queried snapshot row. A regression uses different snapshot/publication
orders. This changes no Core, prompt, provider, reference or public contract.
An exact image built from Git archive, without source mounts, replayed the already
captured personal output **offline, without a provider key**: 5 proposed items,
exact citations, worker, descriptor retrieval, text retrieval and foreign-owner
denial **PASS**. Replay is not a second live extraction. Only then was the remaining
multilingual conversation requested once using the corrected harness image.

| Artifact | Source / immutable image ID |
| --- | --- |
| First three live completions | `e2fde579b1bef86b8bfbf9fb0c12b476f998849a`; `sha256:48c8c806107876c866cc6b5d1fd4da6ef2cd209493c426132cf3a6adaf913432` |
| Offline replay and fourth completion | `1ee72f18f1b6cfef7755f2ae5b34a3c09a393dd8`; `sha256:e3528ebc399e3a6391a5e742bf502e8b6b8c4b0fc9f40e85d77ab73d4a8b3aba` |

## Verification and limits

| Criterion | Verdict and execution evidence |
| --- | --- |
| Workspace billing | Owner-confirmed console check; independent admin verification NOT TESTED |
| 429 operationally resolved | PASS for this sample: four POSTs, all HTTP 200, no retry |
| Frozen model/data/reference | PASS: exact hashes and source comparisons; unchanged prompt/adapter |
| Preserve ledger and caps | PASS: audit verifies first three records unchanged; 7/8 calls, USD 0.01595415 exposure |
| Save four outputs/candidates/citations | PASS: evidence directory, untouched content strings and source exports |
| Semantic quality | MIXED: manual coverage/omission/unsupported/temporal/uncertainty assessment above; no human validation |
| QH batch contract | FAIL in 3/4 cases; personal PASS with five proposed revisions |
| End-to-end retrieval | Personal live harness FAIL after publication; corrected offline replay PASS. Other rejected batches NOT TESTED downstream |
| Targeted regression suite | PASS: Docker `python -m pytest -q -p no:cacheprovider tests/test_mistral.py tests/test_mistral_pipeline.py`: **20 passed, 9.62 s** on reviewed source and **20 passed, 10.15 s** on the exact final image without source mounts; real disposable SQL/Neo4j, mock HTTP only, no key |
| Lint | PASS: Docker `ruff check --no-cache scripts/evaluate_qh8_mistral.py apps/api/tests/test_mistral_pipeline.py` |
| Four-case offline replay | PASS: exact final image, no key; reproduces three rejected batches and the five-item personal pipeline |
| Deterministic capture audit | PASS: `python3 docs/evidence/qh8-mistral-20261016/audit.py`; actual usage, preserved ledger prefix, exact content/candidate comparisons |
| Artifact integrity/privacy | PASS: raw captures byte-compared to private originals, frozen fixtures byte-compared to a0f85c0, manifest hashes, local file links, configured-secret guard and Git whitespace check |
| Hosted CI for new commits | NOT TESTED; local commits have not been pushed |

Previous mock/native verification is reused; it does not establish live-model
quality. Four short synthetic examples, one completion each, one model/seed and an
assistant-authored reference do not measure run-to-run variance, real sensitive
data, production reliability or broad multilingual ability. Raw preservation and
an accepted personal batch are evidence, not independent human validation.
Full extraction shows adequate textual retention in several cases but unreliable
contract compliance and a concrete unsupported conditional property. Measure these
baseline failures before deciding whether any optimization is warranted.

## Historical 429 evidence retained

Original run: metadata GET 200, first work POST 429; two requests, USD 0.006 hold.
First reviewed resumption on 2026-10-15 at about 22:20 Europe/Paris: work POST 429,
code `1300`, type `rate_limited`, sanitized message `Rate limit exceeded`, observed
HTTP latency 0.450214 s. No `Retry-After` or allowlisted request/quota diagnostic
headers were supplied. It stopped immediately, leaving three attempts and
USD 0.012 uncertain hold. The exact limiting quota was not established.
Private historical artifacts remain in `live-initial` and `resumed-work` under
`/tmp/qh8-mistral-evidence`; the new experiment has not erased or reinterpreted them.
