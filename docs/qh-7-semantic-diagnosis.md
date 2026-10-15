# QH-7 offline semantic diagnosis — 2026-10-15

QH-7 remains in progress. No new external request, provider cost, data correction,
semantic graph write, push, merge, CI execution or Jira update was performed.
The previous local commits are preserved. This is diagnosis and a proposed
correction, not an implemented extraction-policy change.

## Evidence and reproducibility

Inputs: [saved experiment ledger](evidence/qh7-mistral-smoke.json), the previously
saved initial entity extraction, the two existing synthetic episode revisions,
and installed Graphiti **0.30.2**. The [diagnostic script](../scripts/diagnose_qh7_semantics.py)
uses an in-memory HTTP peer and a synthetic SDK key, plus scoped local Neo4j reads.
It does not send provider traffic, change the VPS `.env` or persist replay results.

The actual SDK request serialization was reconstructed for A entities, B entities,
B edges and B summary. **All four SHA-256 hashes exactly match** the recorded
original payload hashes. This verifies the analyzed prompts/schema/parameters,
not just their current approximate wording. The A and B entity request bodies are
identical after substituting `Bea founded` with `Ada founded`. Group IDs and
technical timestamps do not appear in these entity-extraction prompts.

Executed from the existing backend:

```sh
sudo -n docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T \
  -e PYTHONPATH=/workspace/apps/api backend \
  python /workspace/scripts/diagnose_qh7_semantics.py \
  --ledger /tmp/qh7-authorized-experiment/ledger.json \
  --first-result /tmp/qh7-first-request-result.json \
  --output /tmp/qh7-semantic-diagnosis.json
```

The two checkpoint paths are existing VPS experiment artifacts. The key-free
[diagnostic output](evidence/qh7-semantic-diagnosis.json) preserves hash matches,
schema acceptance, transformation replay and proposed violation checks. Ruff on
the script, staged whitespace review and the repository secret guard pass.
The first invocation needed PYTHONPATH corrected for a script outside the backend
package; this was a local import error before diagnostic execution, not an API call.
No model generation or new ingestion was performed to test a causal hypothesis.

## 1. Why Bea is missing

**Observed:** the model response itself lists only Cedar Observatory. The
original prompt contains the full source `Bea founded Cedar Observatory.`. There
is no preceding-context truncation, adapter replacement or post-response Bea
filter to explain this omission. The response consumed 44 output tokens against
a 4096 cap; the experiment accepted only completed responses.

**Model:** `ministral-3b-2512` produced an incomplete answer under the actual prompt.
This is directly evidenced. One observed failure and one earlier cached success
for Ada do not establish an intrinsic inability of all 3B models, a stable bias
against the name Bea, or the superiority of another model.

**Prompt:** Graphiti requests named entities but heavily emphasizes specificity,
unique identifiability and omission when uncertain. This may encourage a small
model to omit a short first name, but the same prompt includes a positive example
with a single first name. Bea's omission is therefore not a requirement of the
prompt. Prompt/model interaction is a plausible contributor, not an isolated,
experimentally proved root cause. We cannot infer the model's internal reasoning.

**Schema:** ExtractedEntities validates a list of named objects and numeric type
IDs. It does not express source coverage or require particular source participants.
The one-element response is schema-valid. Both Ada and Bea can be represented by
the existing generic Entity type (ID 0); a new ontology/Person type is unnecessary.

**Adapter:** the full text reached the SDK unchanged. There is no evidence of an
input or UUID defect here. Its integration does lack an early semantic failure
signal: successful Graphiti method return was allowed even when no useful fact
survived. The smoke detected this only at final retrieval.

## 2. Why the relation mentions an unextracted entity

Graphiti makes a separate edge-extraction request containing the full original
source and the extracted-entity list. The list contains only Cedar Observatory;
Bea remains visible in the source sentence. The prompt explicitly requires both
endpoints to come from the supplied list. The model instead returns a relation to
Bea, violating that constraint.

The relationship text is supported by the source; it was not invented as a fact.
It is invalid relative to the current graph-extraction node set. Edge endpoint
fields are plain strings, without a dynamic enum tied to the prior node list,
so the JSON/Pydantic schema still accepts the response.

Graphiti's extract_edges checks endpoint membership and drops unmatched edges
with a warning. Replaying the saved response with the actual function yields
**zero returned edges**. It correctly avoids creating a missing Bea node, but the
caller receives an empty list rather than an ingestion failure. The QH adapter
had no check before that lossy filtering. No aliasing, cross-space deduplication
or authorization mismatch is needed to explain the observed failure.

## 3. Where the unsupported date comes from

After the edge is dropped, Cedar Observatory has an empty summary and no new
edge fact to append. Graphiti therefore invokes extract_summaries_batch using the
source episode. This is the generic summary prompt, not the stronger separate
extract_entity_summaries_from_episodes prompt present elsewhere in the package.
Its instructions already restrict content to the supplied context.

The hash-matched summary request has empty prior episodes, empty existing summary
and attributes, the synthetic source, and no `2023` anywhere in its messages or
schema. The phrase `Founded by Bea in 2023.` first appears in the model response.
This is an unsupported semantic addition. It cannot be attributed to a 2023 source,
retrieved history, the SDK or conversion of the episode's technical timestamp.
The exact model-internal origin is unknowable from this record.

The technical reference timestamp is **2026-10-14T23:04:07.515975Z** for B. The
model's edge valid_at exactly matches that reference. A's edge similarly copies
its reference timestamp. Those timestamps identify episode/reference time; they
do not demonstrate when an observatory was founded. The edge schema describes
valid_at as when the relationship became true, and the prompt permits null when
no time is stated. For these past-tense, undated fixtures, copying reference time
into semantic validity is itself unsupported. Keep technical created_at/reference
time separate from asserted event time. Do not reinterpret the previous A
retrieval PASS as a temporal-grounding PASS.

SummarizedEntities accepts arbitrary summary strings. Replaying Graphiti's actual
attribute/summary transformation accepts the saved `2023` text unchanged. The
schema and the QH adapter did not enforce grounding of free-text summaries.

## 4. Smallest proposed correction

No automatic completion of missing nodes, inferred relations, date removal,
canonical Understanding Item changes or new human-validation workflow.

1. **Smoke-only coverage assertion immediately after entity extraction.** For
   the fixed B fixture, require the expected participants Bea and Cedar Observatory.
   If missing, stop before embeddings or edge extraction. This is a deterministic
   test oracle, not a general rule that every source must have two entities and
   not a mechanism that inserts the missing entity.
2. **Integration coherence check before Graphiti's edge filtering.** Validate
   raw edge endpoints against the extracted node names; reject mismatches before
   further provider calls or semantic persistence. Use the existing private client
   wrapper seam, with source/phase context confined to the adapter. Do not patch
   Graphiti internals, broaden Core contracts or silently repair outputs.
3. **Narrow grounding assertions for these undated fixtures.** Summary/fact text
   must not introduce unsupported years/numeric claims, and semantic temporal
   bounds must remain null without evidence. Keep technical reference metadata.
   Reject violations rather than adding, deleting or reclassifying semantic facts.

The saved outputs already demonstrate the proposed checks would flag missing
Bea, an unknown Bea endpoint and unsupported 2023. Checks should also cover the
unsupported reference-time-to-event-time assignment. Add offline regressions from
these fixtures; keep all correction logic outside Core. These checks are necessary
consistency conditions, not proof of general factual truth or exhaustive semantic
entailment. A broad validator for arbitrary paraphrases/dates would exceed this
small correction and must not be inferred from these tests.

The smallest first patch is the smoke coverage assertion plus adapter edge
coherence rejection and fixture-grounding checks, not a prompt overhaul. A short,
generic instruction to retain explicitly named participants can be evaluated
separately, but stronger wording alone offers no grounding guarantee.

## Model alternative and proposed failed-test repeat

The observed 3B answers are faulty. The evidence does not prove that model size
alone caused them, or that a particular alternative is more reliable. A reasonable
**comparison candidate is `ministral-8b-2512`**, retaining the same Mistral API,
JSON Schema path and `mistral-embed`. More capacity is a hypothesis to test, not a
measured improvement or a final provider/model decision. Availability and current
price were not checked online because this task is explicitly offline.

After the proposed guards are implemented and verified offline, repeat only B's
synthetic source under a fresh derived scope, preserving the failed scope. Do not
reuse the defective B extraction as a successful cache entry. Reuse unchanged
embedding vectors where appropriate and existing A only as a read-only isolation
control. Check both named participants before subsequent calls, endpoint coherence,
absence of unsupported dates, then semantic retrieval with precise QH provenance.
No A re-ingestion, source augmentation, new provider, QH-8 persistence or governance
work is required. A new failed-test experiment needs explicit model/scope/cost
approval; this diagnosis performs no new API calls or automatic retries.
