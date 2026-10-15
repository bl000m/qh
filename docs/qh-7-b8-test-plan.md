# QH-7 — prepared B-only Ministral 8B experiment

Status: **prepared and offline-tested, not authorized or executed**. Prior
`ministral-3b-2512` authorization does not cover this model or a new run.
No VPS `.env` model setting was changed. No push, merge or Jira write is included.

## Availability and expected cost

Official documentation lists **Ministral 3 8B**, ID `ministral-8b-2512`, as GA,
with chat completions and structured outputs. Public documentation checked on
2026-10-15; no authenticated model-list/key-validation request was made. Actual
availability/entitlement of this specific Mistral account is therefore untested.
[Model and tariff](https://docs.mistral.ai/models/ministral-3-8b-25-12),
[current pricing](https://docs.mistral.ai/inference/pricing).

Rate: **0.15 USD / million input tokens and 0.15 USD / million output tokens**.
Embeddings remain `mistral-embed`, 1024 dimensions, at the documented **0.10 USD /
million input tokens**. The installed Graphiti 0.30.2 generic client supports this
JSON Schema request path; no claim of improved live semantic reliability is made.

Proposed grant: **maximum 12 new HTTP attempts, estimated spend ceiling 0.01 USD**,
only these two models and the two existing Mistral endpoints. Expected spend for
the short B fixture is roughly **0.0005–0.002 USD**, dependent on actual usage.
This is not a bill or a guarantee of token count. Before each send, the runner
reserves a conservative token allowance from UTF-8 request bytes + framing + the
actual output cap; a risk of exceeding 0.01 USD stops before send. Charges are
estimated from returned usage. Failed attempts count and never retry. No API calls
are made to retrieve billing or check credentials separately.

## Scope and requests

New UUID-scoped synthetic B episode: `Bea founded Cedar Observatory.`
Retain the old failed B, successful A and all database volumes/data. This runner
never re-ingests A and never creates canonical PostgreSQL records or Understanding
Items. It uses a fresh source/revision reference for the derived B episode.

The source is explicitly undated. Technical reference_time/created_at remain
metadata, not proof of founding time. Required semantic dates are null.

Nominal requests without cache assumptions:

1. 8B entity extraction: both Bea and Cedar Observatory must be present before
   any embedding or further LLM call. A missing/extra fixture participant stops.
2. Two single-input candidate embeddings (Bea, Cedar Observatory).
3. 8B relation extraction: raw endpoints must be available; the fixture's grounded
   founding fact must be present and no unsupported date is permitted.
4. Fact embedding and two internal fact-candidate query embeddings.
5. A possible 8B timestamp extraction when the edge's time bounds are null; the
   result must still be null for this fixture. This is a distinct conditional call.
6. Two final name embeddings, then one query embedding and local semantic search.

This is normally **up to 11 requests** (3 LLM + 8 embedding); **12 is the hard
limit**, not a promise to consume all attempts. Unexpected/invalid outputs stop
rather than triggering recovery. A summary call, if needed by Graphiti, is also
counted and fixture-grounding checked. All sends are serial: outer approved
transport lock plus an in-flight assertion; SDK/transport and Graphiti retries
remain disabled. No paid reranker, parallel send, new provider or other model.

## Success criteria

- Full fixture entity coverage, checked only in smoke code.
- Every edge references existing extracted entities, checked before Graphiti can
  silently discard inconsistent outputs.
- Correct founding fact, with supported participants, no unsupported years,
  semantic dates or numeric claims; technical timestamps remain separate.
- ContextEngine search returns a QH hit for the founding fact with the new B scope
  and exact synthetic source/revision provenance, without a confirmed item revision.
- At most 12 new attempts and estimated cost at most 0.01 USD; ledger records
  per-call usage, cost, raw parsed extraction observations and final facts.
- Errors/invalid output terminate with nonzero exit; partial derived data is
  retained for inspection, never silently repaired/deleted or marked approved.

Passing B would provide targeted evidence, not retrospectively validate the old
A semantic timestamps or automatically complete every QH-7 Done criterion.

## Prepared entry point, authorization still required

`adapters.context.smoke_b` is separate from startup, automatic tests and CI. The
safe inspection command `python -m adapters.context.smoke_b --help` invokes no
provider. Missing `--authorized-experiment` is rejected before client creation.
The model override is confined to that process; credentials are read through the
existing backend environment and are never printed or written to the ledger.

Only after an explicit new grant for the scope/limits above, the prepared command
is the backend `python -m adapters.context.smoke_b --authorized-experiment --ledger
/tmp/qh7-b8-new-experiment.json`. The ledger path must not exist: the runner refuses
to restart a prior/partially spent experiment. No command with the authorization
flag has been executed. No additional authorization is needed for local checks;
the next authorization boundary is the new real 8B experiment itself.
