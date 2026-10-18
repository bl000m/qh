# QH-13 — offline alias and epistemic-warning checks

Executable source `47c1213149426c8a11228150883555d3e3cd5d7c`.
[Results](results.json) record offline tests, real OIDC/mock browser checks and
preservation observations. [Protocol report](../../qh-13-reference-aliases.md)
explains membership versus semantic support and reproduction.

101 targeted Docker tests passed with network disabled. Three targeted Playwright
cases passed on the existing VPS with real Alice OIDC: three-Space reset/key checks,
mock/non-mock heading and all-proposed warning despite omitted/contradictory prose.
The non-mock response is an HTTP stub, never a model request. Separate real Alice/
Bob probes passed all retained six-record Spaces and twelve foreign API denials.
All 14 canonical table inventories, six container/configuration identities, .env,
realm and historical closed ledger remained unchanged.

The complete isolated/native and hosted CI run results are recorded in the report
and PR after execution; overlapping counts are not summed. Mixed confirmed/proposed
browser controls use the existing hosted isolated fixture, not new persistent data.
Protected traces/screenshots/inventories remain under ignored mode-700
`.local-archive/qh13-alias-protocol-20261018/`, with no credentials published.

The exact original first Mistral trial is unchanged. Its old item IDs still fail,
including under the new alias output field. Valid aliases only resolve canonical
membership; these tests do not validate natural-language entailment or improve a
measured live-model score. New inference count is zero. The
[proposed one-POST gate](../qh13-mistral-alias-gate-20261018/README.md) remains blocked.
