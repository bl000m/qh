# QH-13 — model reference aliases and canonical proposal warnings

2026-10-18. Owner-requested follow-up to the
[first stopped real trial](qh-13-mistral-chat-experiment.md), same PR #14 / branch
`feat/QH-13-context-chat`. Executable unit
`47c1213149426c8a11228150883555d3e3cd5d7c`. No new inference, migration,
canonical write, deployment, service or public contract. Public provider stays mock.

## Decision and compatibility

Use a request-local reference protocol in the Context Builder/decoder. The existing
QH-2 `LLMProvider` still exchanges the same GenerationRequest/GenerationResult.
The REST response still returns complete canonical `references` and
`provided_revisions`, never aliases. Core, public DTOs, policy and repository are
unchanged. This is an internal model-facing format, documented in
[ADR 0006](adr/0006-scoped-contextual-chat.md#request-local-reference-protocol--2026-10-18).

The alternative was stronger UUID wording alone. It would preserve the old internal
format, but the first model had already returned stable item IDs despite the exact
revision-ID instruction. Explicit aliases reduce generation/copying of long IDs
and make the accepted namespace small and unambiguous. This is a technical reason
to test the protocol, **not measured evidence that Mistral now follows it**.

## Exact protocol

`qh.chat.context/2` preserves the lossless v1 source/common-metadata encoding and adds:

```json
{"allowed_reference_aliases":{"R1":"exact-revision-id-a","R2":"exact-revision-id-b"}}
```

Assign `R1…Rn` in ascending exact `revision_id` order over the **final transmitted
set only**, after whole-record budgeting. Retrieval order does not change that map
for the same set. No alias exists for an omitted record. It is a bijection, bounded
to 40 records. A changed set may change numbering; aliases are ephemeral, not
persistent identities and not portable between requests or Spaces. `R1` in another
request is resolved only against that other request, never a global map.

The model-facing output is strictly:

```json
{"answer":"Generated text","reference_aliases":["R1"],"insufficient_context":false}
```

The model may return distinct exact allowed keys only. No normalization, trimming,
case folding, regex recovery, UUID lookup or item-to-revision repair. Unknown,
duplicate, malformed, nonstring or wrong-kind references reject the whole answer.
Legacy `revision_ids` output is not accepted by the active decoder. An insufficient
answer may declare no references; a supported answer must declare at least one.

Before resolution, QH verifies the actual sent map/records against the trusted
canonical records retained for this exact request. Duplicate map JSON keys,
non-bijective targets, extra/missing aliases, source/record collisions and scope
mismatch fail closed. The model cannot supply a replacement map. UUIDs remain in
the full canonical records/source/relation anchors so their exact information can
be reconstructed; they are **not** permissible output references.

Canonical records are deep-copied into the bounded retained snapshot: frozen
dataclasses alone do not freeze nested content/origin dictionaries. This preserves
the sent records if a repository/test object mutates in memory. The existing saved
selection fingerprint and live pre/post policy/readiness checks still reject
changed context, including that mutation. No transaction spans generation.

The original v1 codec remains available for archived offline round-trip checks.
The mock now emits aliases through the same active decoder; the generic Mistral
adapter, authorization, input/output/request caps and no-retry behavior are unchanged.

## Epistemic information and UI

The system prompt now normally follows the latest question's language, as already
approved; French UI is unchanged. It explicitly requires unconfirmed qualification
when all support is `proposed`, and distinct attribution for mixed proposed/current
support. A confirmed hypothesis is still hypothetical; descriptor assignment
certainty is not validation or truth.

The UI does not rely on the model complying. After existing wire validation:

- If any verified **declared reference** is proposed, show **Cette réponse cite des
  propositions non confirmées. Elle ne constitue pas une validation de la compréhension.**
- If the nonempty **provided set** is entirely proposed, independently show **Tout
  le contexte fourni est proposé et non confirmé. Aucune révision confirmée courante
  n’a été transmise.** This also applies when the model declares no references or
  omits/contradicts that qualification in prose.
- Mixed supplied context with only confirmed-current citations does not trigger
  the cited-proposal warning. An empty supplied set does not vacuously trigger the
  all-proposed warning. These statements concern the supplied set, not every record
  in a partially retrieved Space.

Warnings derive from server-verified canonical DTOs, with no new REST field or
interpretation of answer text. The generated text remains visibly distinct; no
Understanding item, validation actor, confirmed pointer or historical record changes.

| Dimension | Authority and practical limit |
| --- | --- |
| Generated answer | Untrusted model text; no automatic canonical publication or confirmation |
| Model alias | Backend-assigned request-local shorthand; validates declared membership only |
| Revision identity | Exact immutable canonical `revision_id` from the transmitted set; public citations stay canonical |
| Provenance | Existing source identity, exact quote/offset and relation anchors remain unchanged; locator validity is not entailment |
| Validation state | Canonical proposed/confirmed-current flags, independent of model prose and descriptor certainty |
| Actual semantic support | Requires separate assessment of each claim against evidence; aliases/valid JSON/warnings do not prove it |

## Executed verification

| Criterion | Evidence / limitation |
| --- | --- |
| Exact aliases, multiple revisions/order, invalid/duplicate/malformed/colliding maps, budget exclusion and scope | PASS: offline chat regressions, **101 passed**, 0.87 s, Docker network disabled |
| Original Mistral failure | PASS: original capture bytes unchanged; old output rejected, and the same old item/revision UUIDs also rejected under the new alias field |
| Canonical provenance/relation/time/state and v1 archive | PASS: exact full round-trip, full canonical reference equality, retained v1 expansion; no output repair |
| Freshness mutation | Initial targeted failure exposed earlier decoder rejection; retained snapshot correction restores the existing ContextChanged path; full targeted run passed without weakening the test |
| UI warnings independent of generated prose | PASS: three targeted live-stack Playwright cases, **3 passed**, 39.4 s, actual Alice OIDC; non-mock prose is an HTTP stub, not an inference |
| Real Alice/Bob three-Space probes | PASS: retained six proposed records each, canonical sources/relations/history, mock follow-up, 12 Bob API 404 denials and absent/invalid token 401 |
| Ruff / strict TypeScript | PASS |
| Full isolated real SQL/Neo4j | PASS: strict runner **665 passed, zero skips**, 796.83 s; mock/replay only |
| Latest hosted browser/OIDC/quality CI | Verify the latest PR HEAD run; targeted counts overlap and must not be summed |
| New Mistral quality | NOT TESTED: no provider calls authorized/performed by this change |

The full isolated command reuses the existing dedicated test infrastructure:

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --mount type=bind,src=/home/ubuntu/qh,dst=/workspace,readonly \
  -w /workspace/apps/api --entrypoint python \
  qh12-api:d70626bbe50c070c428b02564d22dec42b3b22b0 \
  -u /workspace/scripts/run_qh30_integration.py
```

The existing Dockerfile additionally copies only the frozen synthetic first-trial
archive for the hermetic historical regression. No dependency or runtime image
replacement is performed on the VPS. The pre-existing Starlette/AnyIO deprecation
warning is unchanged and non-blocking. Full hosted browser checks include the mixed
confirmed/proposed fixture, with real OIDC and no live model.

[Machine-readable offline results](evidence/qh13-alias-offline-20261018/README.md)
retain the executed counts and preservation summary.

## Next proposed single inference — not authorized

[Independent manifest and audit](evidence/qh13-mistral-alias-gate-20261018/README.md):
one POST only, no model GET, only Projet pilote and the exact Italian question
**Di che cosa parla questo Context Space?**, same model and 1,000-output-token cap.
All six proposed records fit: **6,733 context bytes / 9,594 input bound**, not actual
API tokens. Proposed cap USD 0.01, conservative reservation USD 0.0024, within the
previous stricter envelopes. The new private ledger is blocked with zero calls,
historically linked to the closed 2/4 ledger; that original file is unchanged.
Its unused allowance is not reused. Model/prices were checked in public official
documentation only; no new authenticated metadata request or inference occurred.

Only a specific owner approval of the new sealed manifest can open that gate.
Recheck actual selection/source/payload/freshness/price hashes before any later
request; stop/reseal on drift. No retry or broad browser activation is implied.
PR #14 remains open for review, QH-13 is not DONE; QH-39/QH-43 are not started.

## Executed owner-authorized single inference — 2026-10-18

The owner subsequently approved this exact gate. The separate
[second-trial report](qh-13-mistral-alias-experiment.md) and
[capture archive](evidence/qh13-mistral-alias-trial-20261018/README.md) record one
POST, zero GETs/retries, six exact alias resolutions and QH 200. The Italian topic
answer still omits explicit proposed status; deterministic UI warnings remain
necessary. All state/records are unchanged, the dedicated ledger is closed 1/1,
and public chat remains mock. The sealed proposal above is preserved as history;
no further inference, merge or Jira DONE follows.
