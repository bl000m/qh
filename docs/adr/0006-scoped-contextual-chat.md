# ADR 0006 — Scoped ephemeral contextual chat

Date: 2026-10-17. Status: owner-approved minimal QH-13 contract. Implementation and
verification are separate in [QH-13](../qh-13-contextual-chat.md). Preserves
[ADR 0003](0003-native-context-engine.md), [ADR 0004](0004-unified-understanding-engine.md)
and [ADR 0005](0005-browse-first-context-understanding.md). No canonical migration,
conversation store, new service or understanding publication.

## Decision and rationale

The owner explicitly approved a separate CHAT operation for the authenticated
owner of exactly one Space. READ_CONTEXT remains insufficient permission for
chat/disclosure; the existing PolicyService evaluates CHAT before retrieval,
immediately before generation and before returning an answer. Existing browse
calls still enforce READ_CONTEXT and graph/canonical integrity. Foreign/missing
Spaces return the same 404. The backend, never the browser, retrieves canonical
context. Public ingress is POST `/context-spaces/{context_id}/chat`.

Confirmed-current is the default. Proposals require explicit `include_proposed`
and retain their unconfirmed state; canonical history/rejected content is excluded.
Dialogue is ephemeral browser memory and is untrusted, not a canonical evidence
source. Changing Space, opt-in, logout or closing the chat clears it. No chat answer
changes understanding or confirmation; acquisition remains QH-39.

ChatService uses the existing ContextService browse, pure Context Builder and QH-2
LLMProvider. Initial retrieval scans at most two UUID-keyset pages of ten per
selected view. It is deterministic bounded enumeration, not semantic search.
No text selector, ontology, agent framework or second Context Engine. Budget-excluded
records are omitted whole with explicit partial coverage. Selection is re-read
before/after generation, with policy rechecks; changed data/graph trust discards
output. No transaction spans provider work. This is not a frozen cross-call snapshot.

The default provider is a labelled deterministic extractive mock. Mistral is a
backend-only explicit configuration with private authorization, scope, expiry,
separate existing ledger, pricing/exchange ceiling and no retry. Key presence
alone grants nothing; no live inference is authorized by this ADR. A local model
only requires another LLMProvider adapter, preserving the service/builder/engine.

## Alternatives and consequences

- Reusing READ_CONTEXT for sending data would collapse read/disclosure authority;
  rejected under ADR 0004. Broad/multi-Space chat is outside the approved scope.
- Semantic/vector ranking and an agent framework add unneeded responsibilities;
  deferred. Bounded scans can miss relevant records; coverage and insufficiency
  must be visible, and no exhaustive-answer claim follows.
- Server-side conversation persistence adds lifecycle/privacy obligations;
  deferred to separately approved work. The current browser dialogue has explicit
  size/turn limits and disappears on reload/logout/navigation.
- Arbitrary model-generated source cards would permit invented provenance;
  rejected. The backend resolves exact declared revision IDs only from the provided
  set, reusing canonical DTOs. Membership is verified, semantic entailment is not.

## Security and limits

System instructions delimit canonical content and dialogue as untrusted data;
no tools, dynamic source commands, URLs or writes are executed. JSON output is
strictly checked, including reference membership; React renders plain text.
These controls reduce attack surface, not a claim of robust prompt-injection
resistance or factual fidelity for an untested live model. An answer with valid
references can still be semantically wrong. Model training knowledge cannot be
mechanically proved absent from prose; the mock establishes only extractive behavior.

Only available authorized canonical content, relations, time and source metadata
are sent; the unavailable source body is not invented. Mistral pricing and a real
smoke need separate authorization and current verification. No human review,
persistent demo import, live semantic quality or generalized model reliability is
attested. Interactive validation, editing, conversation-to-understanding and local
model hosting remain future tickets.

## Implementation clarification — 2026-10-18

The owner requested lossless compaction after the populated Demo A review.
[The correction report](../qh-13-review-corrections.md) documents the internal
provider-message encoding `qh.chat.context/1`, exact canonical round-trip and
source collision/scope guards. Shared source records and identical administrative
metadata are factored out; canonical/public contracts, validation state, relation
anchors, quotes, authorization and caps are unchanged. Full duplicated records
were the alternative; they omitted one of six fixture revisions under the same
byte cap. No semantic summarization or inference is used to fit the budget.

The mock heading now explicitly describes demonstration excerpts without question
understanding. A separate sealed manifest proposes language-following-question
wording for the future real-provider test; the current French instruction stays
active pending specific owner approval. These are implementation clarification
and an unexecuted proposal, not a new canonical model or disclosure permission.

## Executed bounded provider check — 2026-10-18

The owner later approved the sealed candidate and a specific three-question
synthetic experiment. [One actual inference](../qh-13-mistral-chat-experiment.md)
was rejected by the unchanged strict decoder for item IDs used as revision IDs;
the remaining inferences were not run. Temporary language/provider binding was
process-private in the existing backend, public browser chat remained mock, no
architectural or public/canonical contract change. This scoped consent does not
authorize further calls, arbitrary questions or an interactive live-provider window.
