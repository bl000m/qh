# QH-13 — proposed one-question alias trial

2026-10-18. **NOT AUTHORIZED / NOT EXECUTED. Public provider remains mock.**
[Manifest](manifest.json), [SHA-256](manifest.sha256), [exact request](project-request.json),
[system prompt](system.txt), [alias map](aliases.json), [new ledger proposal](ledger-proposal.json).
Executable unit: `47c1213149426c8a11228150883555d3e3cd5d7c`.

Manifest SHA-256:
`3f1141431d077faa2e2a93281552cda80f834236d86f7b354d1b2e38fa646d17`.

Exactly **one POST**, no metadata GET and no retry:
`mistral-small-2603`, Projet pilote `eb122625-1830-4557-b805-473d3b66132a`,
**Di che cosa parla questo Context Space?** Only its six retained synthetic proposed
revisions and exact source metadata/quotes are included. Quotes can reconstruct
synthetic conversation content; approval concerns these actual bytes, not IDs alone.
No other owner/Space, canonical history, previous dialogue or real personal data.

`qh.chat.context/2` adds the exact request-local map `R1…R6`; output must use
`reference_aliases`, not UUIDs. Public API citations remain full canonical revisions
after strict deterministic resolution. Original records/provenance/quotes/state
are unchanged. The active system normally follows the question's language and
explicitly distinguishes proposed from confirmed-current; French UI unchanged.
Valid aliases still do not establish semantic entailment. See
[protocol and UI decisions](../../qh-13-reference-aliases.md).

Measured offline from fresh authorized canonical retrieval: all six fit under the
unchanged caps, **6,733 context bytes / 9,594 input bound** (not observed tokens).
Requested output max 1,000, conservative input bound max 12,000. Official
[model](https://docs.mistral.ai/models/mistral-small-4-0-26-03) and
[standard prices](https://docs.mistral.ai/inference/pricing) rechecked at the time
in the manifest: USD 0.15 input / USD 0.60 output per million. Ignore cache discounts.
Worst-case reservation `(12000 × .15 + 1000 × .60)/1e6` = **USD 0.0024**.
Proposed trial cap **USD 0.01**, below existing USD 0.20 / EUR 5 ceilings.
EUR 2/USD is the prior conservative budget ceiling, not a market/card quote;
actual invoice, FX, taxes/fees and current workspace quota are not independently
verified. The previous exact-model GET/POST succeeded; no new model API request
is hidden in this preparation. If a new GET is required, stop for a revised plan.

The separate private ledger starts **blocked, zero calls**, max one attempt.
It records the exact parent state/file SHA and retained two attempts/estimated
USD 0.00062805 from the [closed prior trial](../qh13-mistral-chat-trial-20261018/README.md).
The old ledger is byte-identical, not reset/reconciled/unblocked. Even including
the new full USD 0.01 cap, prior estimated spend plus this cap is USD 0.01062805,
below USD 0.20; maximum cumulative attempts are three, below eight. This is
traceable budgeting, not permission to resume a failed experiment or ignore fees.

Before execution: explicit owner approval of this exact manifest and disclosure,
new short-lived private receipt (at most one hour and within 24h of refreshed
unchanged pricing), actual OIDC/CHAT, trusted graph/canonical hydration, same full
selection/source/alias/request hashes, outgoing exact-payload guard and one-attempt
ledger. Any drift stops before HTTP. No API key in files/browser/logs; activate
only the scoped backend binding needed for this one approved call, then restore
mock. Capture original response, observed usage/latency and strict QH acceptance
separately. Stop on 429/401/provider, alias, usage, freshness or budget error; no
normalization, item-ID repair or automatic retry. Semantic review remains separate.

Audit without network, dependencies, secrets, QH access or ledger writes:

```bash
python3 docs/evidence/qh13-mistral-alias-gate-20261018/audit.py
```

Green tests or prior consent to the old UUID payload do not authorize this request.
There is no active Mistral session or new inferred answer to evaluate yet.
