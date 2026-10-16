# QH-33 — proposition-level semantic evaluation

2026-10-16. [QH-33](https://contextlab.atlassian.net/browse/QH-33) starts from
consolidated main `21f13d615fc097996370603c1025c25df36859ec`, in the sole development
checkout `/home/ubuntu/qh`, branch `feat/QH-33-semantic-fidelity`.
**Technical delivery for review; not DONE.** Independent human validation of the
reference is still pending, explicitly assigned to QH-38 for later work. The
[current scope amendment and second AI review](qh33-closure-scope.it.md) propose
replacing the earlier sequence requiring personal review before finalizing this
technical delivery. The amendment is not yet recorded in QH-33's Jira description;
the original human-validation requirement is not marked satisfied.
No new inference, persistent write/migration, deployment
or Jira status change. QH-8 originals/reference, QH-32 derivations and the original
7/8 ledger remain unchanged. No model comprehension improvement has been measured.

Per la revisione del proprietario: [guida sintetica in italiano con fonti, JSON e
impatti da valutare](qh33-semantic-review.it.md). È materiale preparatorio; non
registra alcuna validazione indipendente.

## V2 — approved decisions, personal verification pending

The owner explicitly approved D1–D5, including reconstructible historical context,
the distinction between certain/partial defects, positive-control limitations,
citation versus meaning, and the documented POC limits. This approval **does not
attest independence, completeness or personal verification of the 74 units**.

Start with the [compact navigable v2 matrix](evidence/qh33-v2-20261016/review-matrix.it.md).
Every ID links to source, complete output and per-dimension reasons. Stars mark
critical/partial units and reference changes; unstarred units still require review.
[Package instructions](evidence/qh33-v2-20261016/README.md),
[v2 rubric](evidence/qh33-v2-20261016/rubric.it.md),
[provisional metrics](evidence/qh33-v2-20261016/metrics.json) and
[blank personal-review template](evidence/qh33-v2-20261016/review-template.json).

The separate `benchmark-v2.json` retains all 74 IDs and every original source/output
identity. There are 46 source propositions, of which 44 have active coverage:
two resolved historical uncertainties remain reconstructible, with N/A rather than
pass ratings. Planned duration, conditional avoidance and wishing to ask Lee have
precise reference wording. The context is evolutionary understanding, not the last
message alone. V1 benchmark, evaluator, sealed archive, raw outputs and ledger are
unchanged. V2 reuses the existing personal-review gates through a naming adapter.

### Provisional assistant counts — not independently verified

| Source-proposition dimension | Pass | Partial | Fail | N/A | Assessed denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| `active_coverage` | 41 | 1 | 2 | 2 | 44 |
| `semantic_support` | 39 | 3 | 0 | 4 | 42 |
| `attribution` | 15 | 0 | 0 | 31 | 15 |
| `negation` | 12 | 0 | 2 | 32 | 14 |
| `temporality` | 24 | 1 | 0 | 21 | 25 |
| `uncertainty` | 18 | 0 | 1 | 27 | 19 |
| `citation_traceability` | 39 | 1 | 2 | 4 | 42 |

These rows do not describe every generated claim. The **separate extra-claim
group** contains two semantic failures and one partial interpretation, despite all
three having traceable quotes. The five annotation units retain partial
classification/relation/time-linkage judgments. Among 20 authored controls, semantic
support is 11 pass / 9 fail, while citation traceability is 19 pass / 1 fail:
genuine evidence can accompany an incorrect interpretation and vice versa.
All seven dimensions for all four groups remain explicit in the metrics JSON;
there is no overall score or exhaustive claim-precision estimate.

The original 23/34 exact spans, 11 uniquely repairable offsets and three evidence-free
relations are unchanged. Candidate-level resolver diagnostics do not publish valid
siblings: multilingual still fails whole-batch derivation. The model's outputs,
token consumption and quality have not improved merely because rubric/annotations
changed. V1/v2 figures are not a before/after model-quality comparison.

**Personal review:** null metrics, 0/74 accepted judgments; reviewer, review date and
independence are null, completeness/payload attestations false, every decision
pending. D1–D5 approval does not fill these fields. Corrections during personal
review must be recorded faithfully and hash-bound to this version/rubric.

### Current scope and remaining step

Implemented here: versioned offline benchmark/rubric/accounting and a reproducible
review package only. Application/Core/provider/SQL/runtime behavior is unchanged.
The supported POC limits are accepted for QH-33 reporting, **not certified as fixed**:
the hypothetical applied-discount flag, missing non-approval/non-decision, personal
rejection inference and weak labels/relations/time linkage remain visible.
The candidate prompt experiment remains prepared and unexecuted.

Run `python3 scripts/evaluate_qh33_v2.py --out /tmp/qh33-v2-review` and
`python3 docs/evidence/qh33-v2-20261016/audit.py` without a key, network or QH.
The 19 v1/v2 accounting/review regressions and sealed-v1 reproduction cover technical
integrity, not semantic truth. CI also verifies the v2 artifact audit.
The exact packaging check passed **19 v1/v2 tests, 2.391 s**, with network disabled
and no source bind/key, image `qh33-v2-review:f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`,
ID `sha256:684d040c124af536ba6ed13f9e6fc738e0278354f9c5c60eb4259ba04ab969d0`.
The final hosted CI result for this increment is recorded on PR #8 after execution.

**Updated closure proposal:** defer the unchanged personal-review protocol to
[QH-38](https://contextlab.atlassian.net/browse/QH-38), which explicitly covers all
74 units and the two new control-coverage reservations from the second AI review.
No v2 rating or provisional metric is changed by that review. Human metrics remain
null. See the [criterion-by-criterion scope proposal](qh33-closure-scope.it.md#scope-e-definition-of-done-proposti)
for technical evidence, the remaining Jira scope mismatch and authorization gates.
No merge or Jira transition is performed; this is not a final Done declaration.

## Historical v1 record (preserved)

The sections below retain the earlier v1 method, counts and executed evidence.
Their contextual-provenance rubric and 46-unit active denominator are historical;
they do not supersede the approved v2 rubric or imply a completed personal review.

## Responsibilities and method

`scripts/evaluate_qh33.py` owns offline benchmark integrity, review packets and
arithmetic over explicit proposition judgments. It is not an entailment model or
canonical acceptance gate. No semantic score comes from quote matching, descriptor
spelling, publication success or evidence-only text. No Core port, public API,
ontology, table, service or permission changes. ADRs 0003/0004 remain authoritative.

The versioned [benchmark](../apps/api/tests/fixtures/qh33/benchmark.json) pins source
and original output hashes, exact source-turn evidence, and claim JSON pointers
with value hashes. Missing/mutated assets, stale anchors and evidence-only claim
anchors reject before scoring. Every dimension has explicit pass/partial/fail/n/a
counts and its own assessed denominator. No aggregate semantic score is produced.

There are four frozen Mistral outputs (37 candidates), 46 proposed atomic source
propositions, three targeted extra claims and five output annotations. The 46
propositions split/expand the old 31 bundled expectations: their denominators are
not comparable. The extra-claim inventory is targeted, not exhaustive precision.
Ten new sources supply ten good/mutated control pairs (20 **authored** outputs,
not additional LLM results), giving 14 distinct sources and 74 review units.
Controls cover conditionality, explicit non-approval, actually applied discounts,
collective and individual decisions, proposal/adoption/suspension/non-resumption,
conditional future intentions, completed past events, uncertain attendance and
Unicode provenance, across IT/EN/ES/FR/DE. These cases were authored during this
work, not sampled as a held-out or independently labeled test set. No population
accuracy or inter-reviewer agreement is measured. Positive counterexamples guard against
blanket rules such as banning an applied discount or an individually made decision.

## Draft semantic results — independent validation pending

These are assistant-authored judgments, recomputed from annotations. They are not
human benchmark accuracy, calibrated scores, confidence intervals or evidence that
QH automatically detects the defects. “Semantic support” below concerns mapped
source propositions only; targeted extra claims/annotations are reported separately.

| Dimension, source-proposition group | Pass | Partial | Fail | N/A | Assessed denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coverage/completeness | 41 | 1 | 4 | 0 | 46 |
| Semantic support of represented propositions | 41 | 1 | 0 | 4 | 42 |
| Attribution | 11 | 0 | 0 | 35 | 11 |
| Negation/non-decisions | 13 | 0 | 2 | 31 | 15 |
| Temporal meaning/event linkage | 13 | 3 | 2 | 28 | 18 |
| Uncertainty/conditionality | 17 | 0 | 5 | 24 | 22 |
| Contextual provenance support | 42 | 0 | 0 | 4 | 42 |

The attribution/provenance rows do **not** mean all output claims have correct
agency or provenance. The separate extra-claim group contains two unsupported
claims (applied discount and personal rejection), plus a partial agency judgment
for the suspension wording. Likewise exact contextual support for a represented
proposition does not validate every property of its containing item.
Four proposed omissions are explicit no-order-approved, explicit not-a-decision,
initial tax uncertainty and the initial fit hypothesis. The relevance of preserving
the last two historical uncertainties must be reviewed by the owner; changing that
scope requires a new benchmark revision rather than quietly improving the score.
Human metrics are currently **null**, with **0/74 accepted review units**.

## Five priority defects: cause, minimal response and remaining work

The observed defects are in the original returned content. Prompt-level explanations
are plausible hypotheses, not experimentally established root causes. The current
validator checks structural/source integrity; it has no general entailment oracle.

| Defect and concrete evidence | Cause established by inspection | Minimal general response; implementation status |
| --- | --- | --- |
| Multilingual item-5: `discount_applied=true` for a hypothetical discount | Property meaning asserts application although text/evidence preserve a condition; genuine quotes do not validate every field | Preserve modality consistently in text, properties and relations; general prompt candidate prepared, not activated or tested by inference. No property blacklist or automatic rewrite |
| Multilingual item-4: order not approved appears only in evidence | Extraction omits the explicit non-event from claim text/properties; locator repair cannot add a proposition | Include material denials/non-events in extraction and evaluate proposition coverage; benchmark/control added, missing model claim unchanged |
| Evolving item-2 and suspension: adopted trial labeled `counter-proposal` | Lifecycle text and annotation disagree; open descriptor strings intentionally remain legal | Preserve proposed/adopted/suspended transitions and unknown resumption separately; prompt/control prepared. No closed descriptor enum or inference from descriptor certainty |
| Evolving relation-1: “Jo rejects Mina's proposal” | Selection of an alternative is interpreted as individual rejection; source identifies collective choice | Distinguish speaker, explicit decision actor and collective agency; include collective and individual controls. Original relation unchanged |
| Evolving temporal-1/2/3: dates attached to timestamp entities | Literal date extraction substitutes for linkage to proposal/adoption/suspension assertions | Attach supported timestamps to the corresponding assertion using existing fields, leaving unknown bounds absent/null; candidate instruction and lifecycle controls only. No inferred intervals or canonical model change |

Jo's suspension wording is a **partial/contestable** agency loss; it does not prove
that the output explicitly says “Jo alone decided.” Work relation-1's statement/goal
endpoints also require usefulness review; they are structurally legal. Those two
issues remain distinct from the five priority defects.

## Implemented correction and controlled before/after

Inspection found a separate, general implementation bug in the existing literal
temporal-evidence rule: substring matching accepted a timestamp that was merely a
prefix of a longer timestamp/token. For example, extracted
`2031-04-03T10:00:00+01:00` matched cited `2031-04-03T10:00:00+01:00:30`, although
the offsets describe different instants. `literal_timestamp` now requires complete
lexical boundaries, including offset seconds/fractions (dot or comma), signed years and adjacent word/numeric
characters. It performs no date inference or semantic rewriting. Conservative
rejection leaves the complete batch unpublished, including a valid sibling.

The same frozen benchmark/probe hashes were run before and after against the real
extractor, in network-disabled images. Only the temporal guard differs. The probe
repository is in-memory; these numbers are not a claim of SQL persistence testing.

| Observation | Main baseline | QH-33 | Interpretation |
| --- | ---: | ---: | --- |
| False acceptance, invalid timestamp-prefix controls | 9/10 | 0/10 | Deterministic validation improvement |
| Valid literal timestamp controls accepted | 7/7 | 7/7 | Positive cases retained |
| Invalid literal batch sibling revisions published | 18 across nine bad batches | 0 | Atomic rejection after correction |
| Original four batches accepted without resolver | 1/4 | 1/4 | Frozen outputs unchanged |
| Same batches accepted with QH-32 resolver | 3/4 | 3/4 | No semantic correction from offsets |
| Authored semantically mutated controls accepted as proposed | 9/9 | 9/9 | Remaining entailment gap, not a pass score |
| Authored invalid-provenance mutation rejected | 1/1 | 1/1 | Strict evidence guard retained |
| Provider calls | 0 | 0 | No generated improvement measured |

The rejected-prefix count includes one already rejected wrong literal (thus nine
new rejections among ten invalid cases). The 18 baseline revisions count both
siblings in each of nine accepted two-item batches, not 18 semantically bad items.
Every accepted probe revision remains `proposed`. Multilingual remains rejected
atomically for three evidence-free relations; valid siblings do not publish.

## Independent review procedure and rubric

Start with [source-only.md](evidence/qh33-semantic-20261016/source-only.md), writing
your own proposition/actor/negation/time/uncertainty inventory before inspecting
assistant judgments. Next read the [full-payload packet](evidence/qh33-semantic-20261016/review-packet.md):
it includes all output fields, not only the selected claim pointers. Confirm or
amend inventory completeness, including unlisted unsupported claims, before rating.

Use a private copy of [review-template.json](evidence/qh33-semantic-20261016/review-template.json).
Each unit starts `pending`, with every rating null. Coverage asks whether the claim
is actually extracted; semantic asks whether its meaning is supported; attribution
asks who acts versus speaks; negation preserves non-events/denials; temporality asks
order/state/event linkage; uncertainty preserves conditional/hypothetical meaning;
provenance asks contextual support, separately from exact spans.
For each applicable dimension use `pass`, `partial` or `fail`; use `n/a` only for
inapplicable dimensions. Require full judgments to accept a row. Scope/applicability
changes, split/additional propositions or disputed meanings use `changes_requested`
and notes, followed by a new benchmark revision. Never silently alter frozen data.

A complete imported review must retain every ID, match the benchmark hash, identify
the reviewer and offset timestamp, and explicitly attest independence, source
inventory completeness and full candidate-payload review. The tool reports only
**reviewer-declared completion**; it cannot authenticate a human or establish truth.
Any pending/disputed row prevents human metrics. No review import writes canonical
state or confirms knowledge. The original provisional reference stays unchanged.

```bash
# Stdlib-only; new output directory, no dependencies/key/network/database.
python3 scripts/evaluate_qh33.py --out /tmp/qh33-review --prepare-protocol
# Once the owner has supplied an independently completed review:
python3 scripts/evaluate_qh33.py --out /tmp/qh33-reviewed --review /private/review.json
python3 docs/evidence/qh33-semantic-20261016/audit.py
```

## Next experiment — prepared, not authorized or executed

[Prepared protocol/payloads](evidence/qh33-semantic-20261016/future-protocol.json)
compare baseline versus the separate [candidate prompt](evidence/qh33-semantic-20261016/prompt-candidate.txt)
on evolving, multilingual and a new actually-applied-discount counterexample.
Six generations form three diagnostic pairs. Only the system-prompt suffix changes;
model `mistral-small-2603`, JSON mode, source, seed, temperature and limits stay fixed.
No reference labels/ratings enter requests. This is not a generalization benchmark
or a `json_schema` experiment; those need separate protocols.

Require owner reference/rubric approval first, then explicit authorization for this
new experiment and current price/model/workspace verification. Proposed total cap:
8 HTTP requests, including at most one metadata request and six generations;
16,000 input / 6,000 output tokens per generation, USD 0.05 maximum. At frozen
2026-10-16 experiment rates (USD 0.15/M input, 0.60/M output), uncached generation
reservation is **estimated USD 0.036**, not an observed charge or current quote.
The original ledger remains 7/8; a distinct authorized experiment must retain linked
history and must not reset/resume that counter. No retries/fallback/parallel calls;
stop on errors/429/truncation or model/budget mismatch. Log observed usage/latency
separately from calculated cost. Current new API usage/cost/latency: **not observed**.
No inference is required to reproduce this report; it is required to claim that the
candidate prompt improves the LLM's actual comprehension.

## Definition of Done and residual proposals

| Jira/user criterion | Verdict | Delivery classification | Evidence / remaining condition |
| --- | --- | --- | --- |
| Proposition-level metrics and explicit limits | PASS | Implemented and tested, provisional semantic labels | Separate groups/dimensions, null human metrics, immutable anchors |
| Independent human reference validation | NOT TESTED | Not verified | Owner must review inventory, all judgments and extra claims; no assistant self-validation |
| Targeted fixtures and controls | PASS | Implemented and tested | Ten positive/mutated pairs, 17 lexical temporal probes |
| Offline comparison, one variable | PASS | Implemented and tested | Identical inputs, temporal guard only; no changed LLM outputs |
| Generalizable correction without contract change | PASS | Implemented and tested | Complete timestamp tokens, atomic rejection; five model defects remain |
| Candidate prompt improves model fidelity | NOT TESTED | Not verified | No new inference; bounded protocol only |
| Distinct content/time/evidence/human state; no auto-confirmation | PASS | Implemented and tested | Proposed revisions and rejection assertions, review gates |
| Reproducible report and next-experiment recommendation | PASS | Implemented and tested | CLI, archived inputs/results, audit and prepared request hashes |
| Reviewed merge and Jira completion | FAIL / pending | Not implemented | Await owner review and effective merge; Jira status unchanged |
| Ontology, semantic gate, staging, migration, deployment | N/A | Out of scope | No implementation or persistent writes |

No new architectural decision is needed for the implemented guard/tooling. If QH
must automatically adjudicate entailment, actor identity or event linkage at
publication, a reviewed semantic-validation contract and governance/failure policy
would be needed; do not infer one from this benchmark. Typed modality/agency/event
representations would likewise be a separate canonical-model proposal, not a fix
smuggled into QH-33.

Priorities within this ticket: **P1** independent reference/claim review; **P1** keep
five model defects visible until a separately authorized paired inference measures
an improvement; **P2** consider a reviewed semantic gate/representation only if the
existing envelope proves insufficient. No new Jira ticket is created or started.

## Executed verification

Executable/OCI source `16c280f373e9842c311188d147bb33abedba900e`, image
`qh33-semantics:16c280f373e9842c311188d147bb33abedba900e`, immutable image ID
`sha256:757883a007c92c4ce134e6640e3858e04f156d1558d7f4e974621d1debbfeb62`.
Built from Git archive, no ignored configuration. Offline packets/probes use the
exact image with network disabled, no source mount/key. Later archive/report changes
do not alter application, test, workflow, fixture or packaging code.

- Docker targeted regression run: **122 passed**, 1.36 s, including architecture guards and isolated imports; overlaps full integration.
- Exact-image stdlib accounting/review gates: **8 passed**, 0.152 s.
- Baseline/current in-memory probes: 17 temporal cases, four originals and 20 authored
  controls; same benchmark/probe hashes, zero provider calls.
- Ruff, workflow lint, frozen-source/default-prompt comparison and index credential
  guard checked. Artifact reproduction and original QH-8/QH-32 audits pass.
- Protected file bytes/modes and existing container IDs/start times/mounts/networks
  remain unchanged. The architecture guard explicitly admits stdlib `re`; an
  isolated `-I -S` import verifies the extractor needs no installed SDK/framework.
- Full strict integration and hosted CI results are recorded on the associated PR
  after execution; they are required before integration. The exact local command is:

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -w /workspace/apps/api --entrypoint python \
  qh33-semantics:16c280f373e9842c311188d147bb33abedba900e \
  -u /workspace/scripts/run_qh30_integration.py
```

Targeted counts overlap integration and are not summed. The existing Starlette/AnyIO
deprecation warning is unrelated. No hosted CI success is asserted by this snapshot.
