# Synthetic Mistral capture — 2026-10-16

Four original successful inference captures, one per frozen conversation. No retry,
quote repair, prompt tuning or reference edits. Standard inference key never appears
in these artifacts. The owner confirmed the key/workspace billing and available
quota in the console after the last historical 429; no independent Admin API audit.

For each case, `raw.json` is the harness capture of the parsed original API response
and exact request payload (not a raw HTTP byte stream); `output.json` preserves the
assistant's returned content string exactly, with no added newline or correction.
`understanding-candidates.json` is the unchanged candidate array, **not a claim of
canonical acceptance**. `source.json` contains synthetic source text/turn locators;
`citations.json` adds deterministic audit fields without changing generated spans.
`validation.json` is the live batch result where the harness reached it.

`personal/replay-*` records successful offline replay after the harness ordering
fix. Its five proposed canonical revisions are distinct from human validation.
`live-failure-state.json` retains the original five proposed revisions and sync state
before the live harness assertion and disposable cleanup; `live-harness-error.json`
retains that assertion failure. The replay replaces no original live result.

`semantic-assessment.json` is manual assistant assessment against the original,
provisional reference: no independent reviewer, confidence intervals or calibrated
semantic precision. Evidence-only text does not count as an extracted claim.
`ledger-before.json`/`ledger-after.json` preserve the same original request history
and audit reconciliation. Historical failed-call reservations are not API charges.
`manifest.json` records hashes and source/image identities.

Recompute deterministic measures without dependencies, secrets, network or QH:

```bash
python3 docs/evidence/qh8-mistral-20261016/audit.py
```

See the [full report](../../qh8-mistral-evaluation.md) for separate semantic,
temporal, uncertainty, provenance and pipeline findings.
