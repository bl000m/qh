# QH-8 — offline citation resolution and unified engine follow-up

2026-10-16. Dedicated follow-up to PR #5, from frozen local baseline
`5a604f62fd7dfabf77a618e5d40cdee5572da38b`. No new inference, live adapter/prompt
change, migration, deployment or persistent QH write. Original reference and all
files in `docs/evidence/qh8-mistral-20261016/` are unchanged. The reference remains
assistant-authored, provisional and **not independently human-validated**.

## Architecture: approved direction, bounded implementation

[ADR 0004](adr/0004-unified-understanding-engine.md) records the owner's decision:
one provider-agnostic QH Understanding Engine owns validation, conservative
reconciliation and canonical publication. QH-owned conversations use outbound
`LLMProvider` (current experimental Mistral; future replaceable QH-hosted open-weight
model). Authorized external clients may in future submit structured proposals via
MCP without sending the full conversation or requiring a second inference.

The two inputs converge on the same governance, revisions and PostgreSQL/outbox;
Neo4j remains derived and rebuildable under ADR 0003. The inbound external proposal
interface is documented separately from outbound generation, with no public DTO,
MCP tool, backend API, service, local model or new table implemented here. Its future
receipt/policy/provenance representation still requires a reviewed implementation.
Source-verifiable and external-declared provenance are distinct; the current strict
QH-8 path does not accept evidence-free external proposals. Authenticated submission,
quoted support, semantic correctness and human confirmation remain different facts.

## Deterministic resolver and derivation

`app/understanding/citations.py` locates each exact, nonempty quote within original
identified turns of the one authorized source revision. It counts overlapping
matches and requires exactly one across those turns; provider offsets never break
a tie. Python string offsets are Unicode code points, not UTF-8 bytes or grapheme
indices. No trimming, case folding, Unicode normalization, fuzzy match, inferred
quote, missing-relation evidence or semantic correction is performed.

Missing/empty quotes, missing evidence, foreign source references, ambiguous matches,
quotes outside identified turns and cross-turn quotes reject the entire derivation.
An incorrect numeric offset alone is repairable when the referenced source is
correct and the exact quote has a unique allowed occurrence. Bounds are derived
from the source, never from an unauthorized revision or a provider-supplied scope.
Missing offsets may be derived; missing source identity/quote may not be invented.

`UnderstandingExtractor.resolve_citations` is an explicit internal operation. It
checks the existing owner-read policy, source/scope and input fingerprint before
resolution, uses a distinct extraction key, and runs the unchanged whole-batch
validator on the result. Resolution itself invokes no provider or repository write.
`publish` rechecks policy/source/fingerprint and validates the entire checkpoint
before the existing atomic repository call. Default extraction/live mode still
rejects malformed citations exactly as before; the resolver is not auto-enabled.

Derived JSON, checkpoint and locator audit are separate artifacts. Audit records
original/derived output hashes, source fingerprint, resolver version, original and
new spans, turn identity and quote hash. Rejected batches have diagnostics and no
partially corrected output/checkpoint. Neither original captures nor published
revisions are rewritten. New keys prevent treating a changed extraction as the old
publication. An accepted derived batch remains `proposed`, with null confirmed
current pointer and no human-validation actor.

## Before/after: four frozen conversations

These are contract/pipeline results, **not semantic correctness scores**. The native
integration replay uses original content with exact request fingerprint checks,
then explicit citation derivation. No external HTTP or token generation occurs.

| Batch | Original strict validation | Original exact spans | Corrected spans | Derived strict validation | Proposed revisions in disposable SQL |
| --- | --- | ---: | ---: | --- | ---: |
| Work | FAIL | 4/9 | 5 | PASS, 9/9 exact | 9 |
| Evolving | FAIL | 8/14 | 6 | PASS, 14/14 exact | 14 |
| Personal | PASS | 5/5 | 0 | PASS, 5/5 exact | 5 |
| Multilingual | FAIL, missing relation evidence | 6/6 supplied | 0 | REJECTED, 3 evidence-free relations | 0 |
| **Total** | **1/4 accepted** | **23/34 supplied** | **11** | **3/4 accepted** | **28, versus 5 originally** |

The six already-correct multilingual citations do not make its batch acceptable;
no derived output is emitted for that batch. Its three missing relation citations
remain missing, source is retained, no items publish and desired/applied scope
versions both stay zero. No valid sibling is published separately. For accepted
batches the native worker, descriptor/text retrieval, canonical hydration and
foreign-owner denial pass; replaying the derived checkpoint returns identical IDs.
All test-owned databases/graph namespaces are cleaned by the harness; exports persist.

[Original baseline report](qh8-mistral-evaluation.md) remains the historical live
measurement. Original tokens/cost/latency are not new replay consumption. This
follow-up makes **zero Mistral requests**, leaves the original 7/8 ledger unchanged
and reports no newly observed API token usage or charge. Offline validation timing
must not be presented as model latency or evidence of better model comprehension.

## Semantic anomalies unchanged by locator resolution

| Dimension / original candidate | Remaining anomaly | Why deterministic quote resolution cannot repair it |
| --- | --- | --- |
| Conditionality — multilingual item-5 | `discount_applied=true` asserts an applied discount despite a hypothetical source | Exact matching validates evidence location, not entailment or property meaning |
| Omission — multilingual item-4 | No-order-approved is only in its evidence quote, absent from extracted claim text/properties | Adding the missing proposition would be new interpretation, not locator repair |
| Decision/proposal — evolving-2 | Adopted trial text is labeled `counter-proposal` | Open vocabulary is allowed; changing this assignment requires semantic review |
| Attribution — evolving relation-1 | “Jo rejects Mina's proposal” overstates a collective choice of an alternative as a personal rejection | Speaker identification does not establish decision actor, agency or rejection |
| Temporal linkage — evolving temporal-1/2/3 | Literal dates are attached to timestamp entities, not the proposal/decision/suspension assertions | Quote matching cannot decide factual/validity intervals or attach events semantically |

Work relation-1's statement/goal endpoints for a team/panel claim also need semantic
usefulness review; universal endpoints allow them structurally. Personal preserves
uncertain attendance/future weather-dependent intent; an asserted descriptor does
not confirm those events. This follow-up adds no new semantic assessment claims to
the provisional reference. Acceptance rises from 25% to 75% because locators now
satisfy the contract; semantic errors persist even in the newly accepted evolving
batch. No hallucination/precision percentage or production reliability is inferred.

## json_schema: analysis only, provider unchanged

The official [chat endpoint documentation](https://docs.mistral.ai/api/endpoint/chat)
distinguishes JSON mode from schema-constrained output. Its
[custom structured-output guide](https://docs.mistral.ai/studio/conversations/structured-output/custom)
describes supplying a schema. Documentation review is not an executed provider test;
no request/schema compatibility experiment was performed for `mistral-small-2603`.

A future provider-output schema should require `local_id`, `shape`, `text` and
nonempty `evidence` for **every shape**, including relation. Each evidence object
requires source revision, exact quote and the currently agreed offset fields.
A relation branch additionally requires its source/target local references and
predicate. Descriptors retain open string meanings and existing assignment certainty;
owner, confirmation and canonical-profile fields must remain untrusted/forbidden.
The essential shared fragment is illustrative, not a deployed complete schema:

```json
{
  "type": "object",
  "required": ["local_id", "shape", "text", "evidence"],
  "properties": {
    "evidence": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["source_revision_id", "start", "end", "quote"],
        "properties": {
          "source_revision_id": {"type": "string", "minLength": 1},
          "start": {"type": "integer", "minimum": 0},
          "end": {"type": "integer", "minimum": 1},
          "quote": {"type": "string", "minLength": 1}
        },
        "additionalProperties": false
      }
    }
  }
}
```

A complete future schema needs explicit common fields plus shape-specific branches,
not a relation branch accidentally omitting the shared evidence requirement.
Schema enforcement could prevent absent evidence fields **if the chosen model and
schema are supported and a complete generation succeeds**. This is an inference
from the documented format constraints, not measured quality improvement. It cannot
prove quote equality, uniqueness, ownership, semantic entailment, actor attribution,
conditionality or completeness. Backend validation/resolution still applies.
Truncation/refusal/invalid output remains failure; no automatic retry follows.

Keep provider output schemas separate from the registered limited `qh-schema-1`
SQL content profile. No dynamic registration, new mandatory meaning type, SDK/dependency
or provider configuration change follows. A future trusted adapter configuration
can select a provider output schema while reusing LLMProvider generation; no Core
signature or submission API is added here. The live adapter still sends
`response_format={"type":"json_object"}` and its instruction string is unchanged.

## Granular validation/staging: separate evolution

Candidate diagnostics can explain each rejection without publishing partial results.
A future staging model would need explicit owner authorization, visibility, lifecycle,
immutable raw/derived lineage, dependency handling for relations and an intentional
promotion transaction. Whether candidate state is persisted, where and with which
retention/approval semantics requires separate design approval. No staging table,
new state machine or partial canonical publication is introduced here. Do not silently
reinterpret a batch failure as success or drop unsupported relations to pass validation.

## Proposed next Jira work — not created or modified

| Proposal | Scope / acceptance to agree before implementation |
| --- | --- |
| External proposal ingress and provenance | Specify backend application input, authenticated actor/scope, explicit submit/write policy, declared receipt versus verified source support, replay/conflict handling; then implement MCP transport against an approved public boundary without DB/backend imports or compulsory second inference |
| Semantic extraction quality and independent benchmark | Human-review the provisional reference and proposition-level claims; cover hypothetical/applied discount, omitted non-approval, proposal/decision and collective/individual agency; keep semantics separate from locator acceptance |
| Provider structured-output contract | Build complete shape-specific schema with mandatory relation evidence and offline/mock regressions; separately authorize any later bounded live comparison, verifying exact model/schema support without silently changing the baseline |
| Temporal assertions and event linkage | Specify assertion/event references, past/future/conditional meaning, unknown bounds and acquisition-versus-fact/validity time; no inferred dates or rewritten historical revisions |
| Candidate diagnostics and governed staging | Review lifecycle/permissions/dependency/retention choices; preserve whole-batch publication until an explicit contract change is approved |

QH-8's previously verified offline Done criteria and Jira status are not reopened
or changed automatically. These are proposals without fabricated Jira keys/status.

## Executed verification and reproduction

Exact executable source/OCI revision: `1446a26e9821470f8619c08d3dba40e0662034ed`,
image `qh8-citations:1446a26e9821470f8619c08d3dba40e0662034ed`, immutable ID
`sha256:67bcad2b7160102652878e009bda29bc25d1e5484bb5878b21387d7d442b8a82`.
Built from Git archive; the existing development/test image copies the sealed
synthetic captures for hermetic tests. No credentials enter the build context.
Later documentation/derived-archive changes have no executable/configuration drift.

| Criterion | Result / actual command evidence |
| --- | --- |
| Approved architecture/two inputs | PASS: architecture, dated ADR 0003 amendment, ADR 0004 and Product Contract clarification; no implemented external input or permission |
| Original baseline | PASS: sealed capture manifest hashes and Git tree comparison against 5a604f6; original reference/dataset/provider/Core/SQL/MCP/infra unchanged |
| Resolver and strict guards | PASS: Docker network-disabled unit/Core/architecture checks initially 117 passed, 1.05 s; final targeted citations/native harness checks 28 passed, 27.39 s |
| Full exact-image integration | PASS: `python -u /workspace/scripts/run_qh30_integration.py`, **364 passed, zero skips, 431.85 s**, no source mount/key, real dedicated SQL/Neo4j, HTTP mock/replay only |
| Manual four-case original and derived replay | PASS: exact image, no source mount/key; both commands exited 0, actual results 1/4 then 3/4 valid, 11 corrected spans; rejected batch zero items/progress |
| Repeated derived checkpoint | PASS: same IDs, no new provider replay; worker, exact canonical hydration, descriptor/text retrieval and foreign-owner denial pass for all three accepted batches |
| Independent artifact audit | PASS: `python3 docs/evidence/qh8-citation-resolution-20261016/audit.py`; verifies immutable originals and locator-only changes, hashes and proposed states |
| Privacy and scope preservation | PASS: configured-secret guard; before/after original worktree/ledger, persistent container/configuration hashes; no persistent target or paid-call authorization used |
| Lint/links/whitespace | PASS: Ruff, local Markdown file links and Git diff checks |
| New live extraction/json_schema compatibility | NOT TESTED by design: no inference requested or provider changed |
| External submission, candidate staging, hosted model | NOT IMPLEMENTED; future tickets only |

The existing Starlette/AnyIO deprecation warning is unchanged and non-blocking.
Targeted counts overlap the full suite and are not summed into a larger result.

The exact full-suite command (dedicated test credentials only):

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -w /workspace/apps/api --entrypoint python \
  qh8-citations:1446a26e9821470f8619c08d3dba40e0662034ed \
  -u /workspace/scripts/run_qh30_integration.py
```

The manual replay used a new protected `frozen-input/` with verbatim raw captures
and original synthetic scope manifest, never the ledger. An equivalent manifest
can be prepared from the committed `source.json` scope IDs, input/reference hashes
and a fresh synthetic owner, as the automated native replay test does. No private
original owner/secret or label is required for inference: there is no inference.

```text
# Inside the exact image, with only the protected artifact directory mounted:
python /workspace/scripts/evaluate_qh8_mistral.py --replay-from /evidence/frozen-input --out /evidence/before-replay
python /workspace/scripts/evaluate_qh8_mistral.py --replay-from /evidence/frozen-input --out /evidence/derived-replay --resolve-citations
# --resolve-citations with live mode fails before provider construction or output creation.
```

[Derived archive and audit](evidence/qh8-citation-resolution-20261016/README.md),
[metrics](evidence/qh8-citation-resolution-20261016/metrics.json),
[original capture manifest](evidence/qh8-mistral-20261016/manifest.json).
These are executed offline results, not independently validated semantic improvements.
