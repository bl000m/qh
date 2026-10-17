# QH-13 — proposed synthetic Mistral chat gate

Prepared 2026-10-18 Europe/Rome. **NOT AUTHORIZED, NOT ACTIVE, NOT EXECUTED.**
This archive is a reviewable proposal, not a consent receipt or an instruction to
enable the provider. The VPS continues using the deterministic mock.

Review [manifest.json](manifest.json), [its SHA-256](manifest.sha256) and the three
exact request payloads. Manifest SHA-256:
`553b56c219e150bed675fa86c0960a124b2087a99b950098fc82794206cc76c1`.
Source: correction commit `35e6218690cb13b26de498ccb5dd951c25fead8a`.

| Synthetic Alice Space / exact payload | Proposed question |
| --- | --- |
| [Projet pilote](project-request.json) | Di che cosa parla questo Context Space? |
| [Bien-être](health-request.json) | Quali elementi sul benessere sono soltanto proposte e quali informazioni risultano confermate? |
| [Organisation personnelle](personal-request.json) | Quali preferenze e questioni aperte emergono, senza dare per certa la partecipazione di nessuno? |

Each payload contains all six canonical proposed revisions of exactly one retained
Space, complete source metadata, literal citations, descriptors, temporal fields
and relation anchors. There is no confirmed understanding in these three Spaces.
Quotes can collectively reproduce the synthetic conversation; this is a consent
to those actual bytes, not merely to identifiers. No other owners, historical data,
real personal records, previous chat or API key are included. No Authorization
header is stored. Immutable original extraction captures/ledger are not reused.

## Model, prices and reservation — estimates only

Official documentation checked 2026-10-17 UTC / 2026-10-18 Europe/Rome lists
[`mistral-small-2603`, Mistral Small 4](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
and [standard inference prices](https://docs.mistral.ai/inference/pricing) of
USD 0.15 input / USD 0.60 output per million tokens. Cached input is documented at
USD 0.015 but no cache discount is assumed. The existing adapter omits
`service_tier`; the [tier documentation](https://docs.mistral.ai/inference/priority-tier)
states that omission defaults to `standard_only`. No priority premium is budgeted.
This documentation check does not establish authenticated workspace access,
billing/quota or an executed response from this exact model.

- One metadata GET `/v1/models/mistral-small-2603`, then three sequential chat POSTs.
  Four total attempted requests maximum, including failures and the metadata check;
  the existing absolute eight-attempt cap is not relaxed. Metadata is not a paid
  inference; it is still prohibited before explicit approval of this manifest.
- Each POST: at most 12,000 conservative input-bound units and 1,000 output tokens;
  context at most 8,000 UTF-8 bytes. The input bound is not observed token usage.
- Per-chat worst-case list-price reservation: `(12000 × 0.15 + 1000 × 0.60) / 1e6`
  = **USD 0.0024**; three = **USD 0.0072**. Observed tokens/charges remain null.
- Existing **USD 0.20** sublimit is stricter than the **EUR 5** owner ceiling.
  The proposed conservative conversion ceiling is **EUR 2 per USD**, yielding
  EUR 0.0144 planned reservation and EUR 0.40 at the full USD sublimit. This is
  a reservation assumption, not a card conversion or tax/fee guarantee.
  The [ECB reference](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html)
  for 2026-10-16 is USD 1.1253 per EUR. Account currency/charges and current prices
  must be rechecked before execution; refresh and reseal if assumptions change.

The existing [chat endpoint](https://docs.mistral.ai/api/endpoint/chat) supplies
JSON mode, not proof of semantic fidelity. Preserve raw returned content, usage,
latency and sanitized errors separately. Verify declared IDs against the exact
provided canonical set; membership alone does not prove entailment. Compare the
answer with the question, proposal status, uncertainty and source meaning manually.

## Minimal language proposal and execution prerequisites

[active-system.txt](active-system.txt) records the current French instruction.
[candidate-system.txt](candidate-system.txt) changes only that language sentence:
normally follow the latest user question, respecting an explicit requested language.
The request files use this **proposed** candidate. UI remains French and active
application code still says French. Owner approval of this wording is required;
no measured improvement is claimed.

Before any request, obtain explicit consent to this exact manifest/payload,
candidate wording and a reviewed scoped backend activation plan, separately from
CHAT authorization. Current Compose does not expose live provider configuration;
no service replacement or configuration activation is performed by this preparation.
Recheck authenticated owner/CHAT, canonical hydration, graph readiness, current
selection, scope and source fingerprints. Rebuild and compare exact request hashes;
any change requires a new reviewable manifest. Set a short approval expiry only
after consent, no later than 24 hours after refreshed pricing verification.

A new protected, durable ledger already exists at the path in the manifest, with
zero calls, `blocked=true` and a purpose marker distinct from QH-8. The separate
authorization proposal has `owner_authorized=false`. Neither file is a valid
permission to call the provider. Do not reset historical counters, clear pending
reservations or replace the old ledger. Persist each reservation before a request
and reconcile observed usage with an auditable record; ambiguous usage stops work.
Keep the metadata attempt in the same experiment audit. No automatic retry or
parallel generation. Stop immediately on HTTP 429, provider/usage/reference error,
pending reservation, scope/hash/readiness drift or any limit risk. Preserve status,
Retry-After and sanitized diagnostic; never log keys, bearer tokens or private data.

Run the offline audit without dependencies, secrets, QH access or network:

```bash
python3 docs/evidence/qh13-mistral-chat-gate-20261018/audit.py
```

The audit establishes file/record consistency and conservative arithmetic only.
It does not attest live availability, approval, semantic quality, true tokenizer
usage or a charge. No paid request is authorized by green tests or this archive.

## Subsequent authorization and closed execution

The owner later explicitly approved this exact manifest SHA, all three payloads
and the language candidate. [Trial evidence](../qh13-mistral-chat-trial-20261018/README.md)
records one GET plus one project POST; QH rejected wrong-kind references and the
operator stopped without retry. The other two POSTs were not executed. Preparation
flags above and inside manifest.json remain the immutable historical proposal,
not the later consent receipt. The dated private authorization/ledger audit
records that approval; the final ledger is blocked 2/4. Public provider is mock.
No approval of different payloads or an interactive browser window follows.
