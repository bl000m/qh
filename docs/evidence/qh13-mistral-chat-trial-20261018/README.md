# QH-13 — first real chat trial, stopped on invalid references

2026-10-18 Europe/Rome. Approved source HEAD `4f0f3b23971b0f393c796b5dc4adb3750e531f23`.
[Original approved gate](../qh13-mistral-chat-gate-20261018/README.md) is unchanged.
[Report](../../qh-13-mistral-chat-experiment.md) separates raw text quality from
canonical acceptance and describes the temporary process-private backend binding.

- [Results](results.json): one model GET and one project POST, zero retries;
  two other inference cases NOT EXECUTED. Provider 200, QH 503. Ledger blocked 2/4.
- [Original API response](project/raw-response.json) preserves decoded HTTP response
  text exactly; [assistant content](project/output.json) preserves its returned
  string exactly, no newline/repair. These are UTF-8 content captures, not an HTTP
  byte-stream archive. [Request](project/request.json) captures original parsed
  JSON; its canonical hash matches the approved exact payload.
- [Provided records](project/provided-revisions.json) expand the actual compact
  request exactly. [Declared-ID audit](project/declared-reference-audit.json) explains
  three item IDs versus one valid revision ID. Matching item/revision mappings are
  diagnostic only, never output correction or acceptance.
- [QH rejection](project/qh-response.json) is the actual sanitized route response.
  The raw answer was not shown as accepted understanding or an accepted chat answer.
- [Exact-question mock comparison](project/mock-comparison.json) comes from the
  public runtime after the stop, with real Alice OIDC and no provider inference.
- [Assessment](assessment.json) is provisional assistant review, not independent
  human validation. Unexecuted cases receive no semantic result.
- [Before](ledger-before.json) / [after](ledger-after.json) retain the same ledger
  history and authorization transition. `observed_usd` is a legacy field name for
  list-price cost calculated from observed tokens, not a verified invoice charge.
- [Preservation](preservation.json) records unchanged canonical tables/runtime.
  Protected inventories, consent, session receipts and operational runner stay in
  the ignored `.local-archive/qh13-mistral-chat-trial-20261018/`; no keys/bearers or
  complete authenticated traces are published.

[Manifest](manifest.json) seals the capture hashes. Run without network/secrets/QH:

```bash
python3 docs/evidence/qh13-mistral-chat-trial-20261018/audit.py
```

The audit performs no inference, authorization change or ledger reconciliation.
The stopped ledger is not permission for the two unused POSTs. No merge/Jira DONE.
