# QH-13 — second real chat trial: exact aliases accepted

2026-10-18 UTC. Owner-approved HEAD `178dd1db9e866851f226da9be51559ed19d77bef`;
[sealed gate](../qh13-mistral-alias-gate-20261018/README.md) remains unchanged.
[Full report](../../qh-13-mistral-alias-experiment.md).

One POST, zero GETs/retries/supplemental provider calls. Both Mistral and the QH
route returned 200. All six returned aliases resolved to the six transmitted
canonical revisions. This is protocol acceptance, not general semantic validation.
The Italian topic answer omits explicit proposed status; deterministic UI warnings
remain necessary. No independent human review is claimed.

- [Original response](project/raw-response.json) preserves decoded response text;
  [assistant output](project/output.json) preserves the exact returned content string
  without a newline/repair. These are UTF-8 content captures, not raw HTTP bytes.
- [Request](project/request.json) matches the authorized payload hash exactly.
  [Provided records](project/provided-revisions.json) expand that compact input
  losslessly. [Alias resolution](project/alias-resolution.json) maps the actual
  returned aliases to exact canonical revision IDs.
- [QH response](project/qh-response.json) is the actual authenticated route result
  from the temporary process-private binding inside the existing backend container.
  The public browser/API binding stayed mock throughout; [public verification](project/mock-comparison.json)
  confirms that after the experiment. No new listener, restart or worker was started.
- [Results](results.json) distinguish observed usage/latencies and list-price cost
  estimates. [Assessment](assessment.json) separates topic support, status omission,
  reference usefulness and untested dimensions; it is provisional assistant review.
- [Ledger before authorization](ledger-before.json) / [closed ledger](ledger-after.json)
  retain history and link to the unchanged first trial. The legacy `observed_usd`
  field is a token-based list-price estimate, not an independently observed invoice.
- [Preservation](preservation.json) records equality of all fourteen QH SQL tables,
  six container identities/configurations, private configuration and historical
  ledger. Session tokens, key, grant, full inventories and runner stay private in
  ignored `.local-archive/qh13-mistral-alias-trial-20261018/`.

[Manifest](manifest.json) seals artifacts. Recompute without network/secrets/QH:

```bash
python3 docs/evidence/qh13-mistral-alias-trial-20261018/audit.py
```

The one-call ledger is closed/blocked. No live browser session is enabled, no
further inference is authorized, and PR #14/Jira QH-13 remain open for owner review.
