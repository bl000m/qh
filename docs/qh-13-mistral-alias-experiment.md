# QH-13 — second authorized Mistral chat experiment

2026-10-18 UTC. **One exact POST accepted by QH (200), with all six aliases resolved;
model prose still omits the explicit unconfirmed qualification.** No application
change, canonical write, deployment, migration, merge or Jira transition occurs.
PR #14 stays open; the public runtime remains mock. This is one synthetic sample,
not independent human validation or a general model-quality guarantee.

## Authorization and execution

The owner approved HEAD `178dd1db9e866851f226da9be51559ed19d77bef` and the
[sealed manifest](evidence/qh13-mistral-alias-gate-20261018/manifest.json), SHA-256
`3f1141431d077faa2e2a93281552cda80f834236d86f7b354d1b2e38fa646d17`.
Only Alice's synthetic Projet pilote (`eb122625-1830-4557-b805-473d3b66132a`),
its six existing proposed revisions and exact authorized question were transmitted:
**Di che cosa parla questo Context Space?** Model `mistral-small-2603`, internal
`qh.chat.context/2`, one POST, no metadata GET, retry or supplemental provider call.

Public official [pricing](https://docs.mistral.ai/inference/pricing) and
[Small 4 model documentation](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
were rechecked: standard input USD 0.15/M and output USD 0.60/M, unchanged.
Authenticated model access was established in the previous trial and observed again
by this successful POST; no independent Admin/billing audit or extra model GET is
claimed. The new private grant lasted at most 30 minutes, covered only this Space,
manifest and payload, and was used only in a non-listening process inside the
existing backend container. No environment file or public provider binding changed.

Real Alice OIDC/internal identity, owner CHAT, authorized canonical/graph hydration
and freshness checks ran through the existing FastAPI/ChatService path. The current
canonical records and full outgoing payload matched the manifest before disclosure:
payload SHA-256 `8528984a9033e397d6516f4a3ac29f5992f7be34157e1e900f17ce874fda29c1`.
Bob was denied with 404 before generation in both pre/post probes. All six records
fit without partial coverage: 6,733 context bytes and 9,594 input bound, neither
figure being an observed tokenizer count.

## Complete generated answer

The accepted answer text is preserved exactly in the
[original assistant JSON](evidence/qh13-mistral-alias-trial-20261018/project/output.json):

> Questo Context Space riguarda una discussione di progetto in cui si parla di avviare un piccolo pilota con Team Cedar, le possibili riduzioni dei tempi di attesa, e domande su cosa misurare. Viene menzionata anche la possibilità di prendere una pausa reversibile.

`insufficient_context=false`. The returned `reference_aliases` were exactly
`["R1","R2","R3","R4","R5","R6"]`. QH resolved these through its actual sent map,
without normalization, item-ID repair or inferred citations:

| Alias | Exact canonical revision ID | Meaning in this request |
| --- | --- | --- |
| R1 | `03b72464-d157-550e-8eae-39431bdf2acb` | Reversible pause possibility |
| R2 | `06b29078-984f-5a4a-894e-b19b811f8227` | Alex entity |
| R3 | `285e1392-4a35-5beb-8e1b-8e4739659917` | Choice stated by Alex relation |
| R4 | `2bb9c6ea-6e50-56e8-9c88-7b79b521fd2e` | Possible reduction of waiting |
| R5 | `8fbcd4e5-c974-5900-a083-e154611eab2f` | Small pilot choice with Team Cedar |
| R6 | `ad227e63-c35f-562a-b9b8-a17953c89628` | Open measurement question |

The [actual QH response](evidence/qh13-mistral-alias-trial-20261018/project/qh-response.json)
returns full unchanged canonical reference DTOs, not aliases. Both provider and
QH route status were **HTTP 200**. The source revision remains
`9675cf4c-7601-5dad-9043-ebe0e3018dbd`; literal quotes, offsets, turn identities,
relation endpoints and source metadata match the authorized records exactly.

## Separate quality findings

| Dimension | Observed result and limit |
| --- | --- |
| Answers the question / Italian | PASS in this sample: concise Italian topic overview, rather than a mock excerpt list |
| Source support | No clearly unsupported factual claim found in this provisional assistant assessment. Pilot/Team Cedar, possible waiting reduction, measurement question and possible pause correspond to R5/R4/R6/R1 and their literal quotes |
| Proposed versus confirmed | PARTIAL: prose does **not** explicitly say that the support is unconfirmed. All six provided/cited revisions remain `proposed`; zero confirmed-current revisions were sent |
| Uncertainty | Preserves “possibili” reduction and “possibilità” of a pause; does not invent achieved benefits, an executed pause or a measurement result |
| Actor attribution | Does not invent an individual decision-maker. Alex is not mentioned in the answer, so the returned R2/R3 add no explicit claim support |
| Negation / temporal reasoning | Not demonstrated by this answer: no material negated proposition/date is discussed. No unsupported date or event interval is introduced |
| Reference validity / usefulness | Six valid exact aliases; usefulness remains partial because all six are declared globally, including unused Alex/relation references. There is no sentence-by-sentence support mapping |

The existing UI computes both warnings from verified canonical DTOs, independently
of the prose: **Cette réponse cite des propositions non confirmées…** and **Tout le
contexte fourni est proposé et non confirmé…**. Both predicates are true for this
captured response. Their implementation/browser regressions were verified in the
[alias checkpoint](qh-13-reference-aliases.md); this private trial did not display a
live Mistral answer in a public browser session. Deterministic warnings protect the
presentation boundary but do not rewrite the model's text or establish entailment.
No item was confirmed and no generated answer was persisted as Understanding.

The mock still deliberately extracts up to three records without understanding the
question. The new live sample demonstrates actual topic generation and correct
reference namespace use; it does not demonstrate semantic-ranked retrieval or
reliability over other questions/Spaces. The [first trial](qh-13-mistral-chat-experiment.md)
remains unchanged: relevant raw Italian answer, invalid item/revision references,
QH 503 and immediate stop. No causal success rate is inferred from these two samples.

## Usage, cost and closed ledger

| Measure | Actual observation / estimate |
| --- | --- |
| Provider attempts | 1 POST, 0 GET, 0 retries |
| Observed input/output/total tokens | **3,609 / 101 / 3,710**; reported cached/reasoning tokens both 0 |
| HTTP transport elapsed | **1.055168326 s**, local measured duration through body capture |
| Adapter generation elapsed | **1.069156194 s**, wider boundary; not server-only model latency |
| Cost from observed tokens and published rates | **USD 0.00060195 estimated**, not an observed invoice |
| Reservation / authorized cap | USD 0.0024 / USD 0.01, within prior USD 0.20 and EUR 5 envelopes |
| Separate ledger | **1/1 attempt, closed/blocked**, one settled entry, no pending reservation |
| Historical lineage | First ledger remains byte-identical and blocked 2/4; cumulative history 3 attempts, estimated USD 0.00123000 |

The original sealed gate retains its historical proposal flags; the later owner's
approval is recorded in a separate dated private receipt and audited ledger entry.
No counter or closed ledger was reset. The operational hardlinks were removed after
durable capture; the private ledger/receipt/history remain preserved. No key, bearer
or complete authenticated trace is included in the public archive.

## Verification and current closure boundary

PASS: exact-manifest preflight, real Alice/Bob authorization, full canonical/graph
retrieval, actual QH route/alias resolution, ledger settlement/closure, process mock
restoration and public port 8000 mock verification. Before/after read-only inventories
match across all fourteen QH SQL tables and six container identities/configurations;
private `.env`, readonly realm and original experiment ledger match byte-for-byte.
No backend restart, new worker/listener, database write or configuration change.

Recompute [artifact/lineage audit](evidence/qh13-mistral-alias-trial-20261018/README.md):

```bash
python3 docs/evidence/qh13-mistral-alias-trial-20261018/audit.py
python3 docs/evidence/qh13-mistral-alias-gate-20261018/audit.py
python3 docs/evidence/qh13-mistral-chat-trial-20261018/audit.py
```

The executable HEAD's CI run [39099591596](https://github.com/bl000m/qh/actions/runs/39099591596)
passed quality, native-integration, browser and OIDC before this experiment. This
results-only commit changes documentation/evidence, not application/configuration;
its latest hosted CI must also be checked on PR #14. No new semantic score or
independent human validation follows from green tests.

**READY FOR OWNER REVIEW, not DONE.** The next action is the owner's QH-13 closure
review, explicitly accepting or rejecting the remaining prose qualification and
reference-usefulness limits. No merge/Jira DONE is performed, no further inference
or interactive Mistral session is enabled, and QH-39/QH-43 are not started.
