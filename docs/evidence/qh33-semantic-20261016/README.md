# QH-33 offline semantic review — 2026-10-16

All ratings are assistant-authored proposals, pending independent owner review.
No new model output, paid request, canonical confirmation or persistent QH write.
The four original captures and QH-32 archive remain unchanged.

1. Read [source-only.md](source-only.md) and write your own proposition inventory.
2. Read [review-packet.md](review-packet.md), including full output properties and
   relations. Assess missing/unsupported propositions, not only listed annotations.
3. Complete a private copy of [review-template.json](review-template.json). All 74
   rows start pending; never submit the assistant's ratings as independent review.
   Disputed/split/new units require a new benchmark revision before comparison.

[Metrics](metrics.json) keep assistant draft counts and null human metrics apart.
The [before](before-engine-probes.json)/[after](after-engine-probes.json) probes use
identical benchmark/temporal inputs and different extractor code identities.
They exercise actual QH validation/resolution/publication on in-memory synthetic
repositories, **not SQL persistence**. Nine semantically mutated outputs still pass
structural checks as proposed. The temporal correction establishes complete literal
support, not entailment or improved LLM understanding.

[Future protocol](future-protocol.json) contains six prepared paired payloads and
budget estimates, **not authorization or executed calls**. The separate candidate
prompt is not the live/default instruction. Original ledger is unchanged at 7/8.
[Full report and rubric](../../qh33-semantic-evaluation.md).

Recompute packet/metrics/protocol and verify artifact identities offline:

```bash
python3 docs/evidence/qh33-semantic-20261016/audit.py
python3 scripts/evaluate_qh33.py --out /tmp/qh33-review --prepare-protocol
```

No key, network, third-party package or QH service is used by these two commands.
Archived Markdown removes trailing blank lines; the audit repeats that packaging
normalization. JSON results are copied unchanged. The manifest pins files and source
identities; it does not authenticate judgments.
