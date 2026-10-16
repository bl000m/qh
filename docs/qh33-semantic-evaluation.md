# QH-33 — proposition-level semantic evaluation

2026-10-16. Work starts from consolidated main `21f13d6` in `/home/ubuntu/qh`.
Only QH-33 is active. No inference, persistent migration/write or deployment.
QH-8 originals/reference and QH-32 derivations remain immutable. The ticket requires
an independently reviewed reference; that prerequisite is **not yet satisfied**.

## Scope and responsibilities before implementation

The offline evaluator in `scripts/evaluate_qh33.py` owns benchmark integrity,
review packets and arithmetic over explicit proposition judgments. It is not an
entailment model or a canonical acceptance gate. It never infers a semantic score
from quote matching, descriptor spelling, publication success or evidence-only text.
Reference/assessment proposals are assistant-authored; human fields start pending.
No new Core port, public API, ontology, table or permission is introduced.

The existing extractor retains the approved atomic/proposed publication path.
One local correction tightens its existing literal temporal-evidence requirement:
a timestamp must be a complete lexical occurrence, not a prefix inside a longer
offset or numeric token. This changes deterministic evidence validation, not LLM
comprehension. It cannot establish whether an event occurred, whether a timestamp
was negated, or which proposition it qualifies.

A candidate prompt is a separate offline artifact, not the default/live prompt.
Its future paired experiment requires independent reference review and explicit
paid-call authorization. Current request fingerprints and model output are frozen.

## Acceptance and limits

Deliver reproducible source-proposition/extra-claim judgments, separate coverage,
semantic support, attribution, negation, time, uncertainty and provenance measures;
new controlled cases and counterexamples; explicit before/after guard results;
review material and a bounded future experiment protocol. Any assessment by this
assistant remains provisional, regardless of how many deterministic tests pass.
QH-33 can be READY FOR REVIEW with human review/inference still missing; never DONE
before Jira acceptance, reviewed merge and authorized Jira closure.
