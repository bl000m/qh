# ADR 0009 — Explicit selected-conversation enrichment

Date: 2026-10-19. Status: bounded implementation of the owner's QH-39 Demo B
block 1 request. Refines [ADR 0004](0004-unified-understanding-engine.md), reuses
[ADR 0008](0008-personal-organization-and-owner-review.md) owner review, and preserves
[ADR 0007](0007-scoped-provider-sessions.md) chat disclosure/session boundaries.
No new engine, schema, service, canonical taxonomy or paid-call authorization.

## Decision and rationale

The explicit `Enrichir ce contexte` operation owns selection/persistence consent;
answering remains ephemeral. The application checks the existing owner-only
`PROPOSE_UPDATE` action before private reads or provider work. It also uses
READ_CONTEXT inside the existing extractor and graph-verified history navigation.
READ_CONTEXT and CHAT alone do not authorize this write or external extraction.

A selected segment has one stable Source identity derived from Space,
browser-conversation UUID and operation UUID, and an immutable first SourceRevision.
Selecting another segment creates another source snapshot, grouped by the declared
conversation UUID in metadata. This keeps exact selected text reconstructible
without pretending the entire transient conversation was saved or overwriting an
older source. Extending the same source through arbitrary client revision numbers
was rejected: it would require another concurrency/selection contract. No revision
number is accepted from the browser.

Turn IDs, exact text, declared roles and browser-captured timestamps are retained.
QH authenticates `submitted_by` and supplies acquisition time; it does not attest
browser timestamps, that a submitted assistant response came from a named model,
or that every user-role assertion was independently authored/verified by that user.
Assistant dialogue is explicitly unverified and never relabelled as human evidence.
Factual time, source acquisition time and human validation remain separate.

The source intake keeps QH-8’s text/locator representation; the original QH-8
extractor file and request construction stay byte-identical to the sealed QH-33
baseline. A request-local prepared-source/revision buffer feeds its existing
`extract` and `publish` methods without committing a source first. This is transient
working input, not a second persistence system or candidate staging lifecycle. The QH-39 path prepares an unsaved selected source, calls the same
LLMProvider port, applies QH-32 exact/unique citation resolution and the unchanged
whole-batch validator, then publishes source and all proposals through the existing
CanonicalRepository transaction/outbox. A failed provider/429/timeout, locator,
sibling or SQL constraint leaves no source or partial proposal batch. An exact
successful empty result may retain the explicitly authorized source with zero
Understanding revisions and an honest UI result. The historical QH-8 source-first
internal import and three-turn minimum are preserved; no invented padding turns.

## Provider boundary

The runtime binds only `LiteralSegmentProvider`, a no-network control implementing
LLMProvider. It copies each selected user utterance literally into a generic item
proposal, without classifying meaning, splitting propositions, inferring entities,
or claiming semantic comprehension. Selected assistant turns may be source context
but do not become proposals in this control. This is explicitly labelled in the UI.
Fixture/replay providers can produce structured entities/relations through the same
engine; integration tests cover that port separately. No mock label is presented as
a real extraction inference.

Reusing the existing chat Mistral grant would send a different payload/purpose and
is rejected. QH-45 availability, credentials, receipt, ledger and budget stay intact.
External extraction requires a separate reviewed exact-payload disclosure/cost gate;
it is **not implemented or activated** by this increment. No external call occurs
in startup, tests, CI or the enrichment endpoint. Hosting another model later changes
the adapter and its approved disclosure configuration, not the canonical pipeline.

## Replay, freshness and governance

The operation UUID binds the exact selected payload fingerprint. Same-ID/same-input
replay returns the original source/proposal IDs from canonical rows, even after a
new service/session or owner review. Same-ID/changed input conflicts. The client
retains IDs for repeated identical selections in the temporary conversation; the
server serializes publication by source key and handles competing publications
without duplicate rows. New explicit operation IDs are new submissions, not semantic
deduplication (QH-47). A process-local busy gate bounds concurrent generation; the
SQL lock/immutable receipt is the durable publication authority.

Policy and graph checks precede processing and are repeated before publication.
SQL rechecks owner and locks projection state; a non-ready projection fails closed.
There is no transaction held across generation, graph bypass or direct graph write.
The existing worker projects revisions; pending projection is reported as unavailable
by existing retrieval rather than replaced by a SQL-only fallback.

Every generated revision remains AI-origin `proposed`, with no validator or current
pointer. QH-46 owner actions remain the only explicit confirmation/correction/refusal
path. After enrichment, existing chat snapshot grants are revoked locally/server-side
and require a new preview/consent; no extraction consent is treated as chat consent.
No conversation archive, session redesign, automatic reconciliation, ranking,
projection sharing or MCP submission is added.

## Consequences and limits

One scoped POST `/context-spaces/{id}/enrichments`, strict owner-free input, one
source and bounded 1–8 turns (4,096 code points each, 20,000 serialized UTF-8 bytes).
No source/revision owner, profile, validation state, revision counter or canonical
ID can be supplied. Output is an exact canonical receipt, not a semantic score.
The original sources, frozen Mistral outputs and ledgers stay immutable. Tests use
only disposable data. No seed, persistent migration or demo proposal review occurs.

The UI distinguishes chatting, explicitly retaining selected source/proposals, and
reviewing a proposal. It reuses the existing canonical explorer/detail/review instead
of an administration screen. A refresh/re-authentication erases unsaved dialogue but
retains the authorized canonical source and proposed revisions. Richer extraction
quality and real external inference are unverified; QH-33/QH-38 defects remain open.
