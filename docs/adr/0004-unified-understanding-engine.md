# ADR 0004 — One QH Understanding Engine, two proposal inputs

Date: 2026-10-16
Status: architecture decision explicitly approved by the owner in the QH-8
post-Mistral follow-up request; implementation scope limited as stated below.
Refines [ADR 0003](0003-native-context-engine.md), preserving its PostgreSQL authority,
immutable identity/revision/provenance, governance and replaceable graph principles.
Does not supersede ADR 0001 dependency direction or ADR 0002 identity/authorization.

## Decision and responsibilities

QH owns one provider-agnostic Understanding Engine in the existing backend. It owns
validation, conservative reconciliation and canonical publication of understanding
proposals in a Context Space. LLM output and external-client output are inputs to
that engine, never independent canonical knowledge stores. No new service is needed.

Two input modes converge on the same authorization, validation, immutable revisions,
provenance, human governance and PostgreSQL transaction/outbox path:

1. **QH client extraction.** QH retains the conversation/source revision and calls
   the existing outbound `LLMProvider.generate` to extract proposals. The current
   experimental adapter uses Mistral API. A future open-weight model hosted in QH
   infrastructure can implement the same port; no local model is installed here.
2. **External client proposals through MCP.** ChatGPT, Claude or another compatible
   authorized client may submit structured proposals directly. QH need not receive
   its full conversation or perform a second inference. This is an inbound proposal
   submission use case, distinct from outbound `LLMProvider`. The future independent
   MCP adapter must use an approved backend boundary, never import backend source
   or access databases. No MCP tool, HTTP route or submission implementation is added.

`app/understanding` remains the owner of the current QH-8 use case and deterministic
citation/local-reference resolution. Core ports, CanonicalRepository, PolicyService,
registered generic profiles and the native worker/retrieval path are reused.
“Reconciliation” includes today's conservative local references/idempotent replay;
semantic identity merging, contradiction adjudication and confirmation are future
reviewed work, not implemented capabilities or automatic decisions.

## Provenance and authorization

| Input evidence | Meaning QH may establish | Limit |
| --- | --- | --- |
| Original source revision available to QH and authorized | Exact source/turn/Unicode locator is verifiable | A literal quote does not prove entailment, truth, authorship claims or human confirmation |
| External provider/client declares an assertion without available original evidence | QH can record that an authenticated client submitted a declaration | It cannot claim to verify the original conversation or manufacture source quotes/offsets |

An authenticated submission identity, declared model/provider and acquisition time
must remain distinct from an assertion's subject, factual event time and evidence
strength. Provider names/model labels supplied by a client are declarations unless
separately attested. “Source-backed” and “external declared” are provenance concepts,
not automatic SQL registry types, new tables or implemented enum values in this PR.
An external quote can be checked only if its original revision is independently
available and authorized; its declared origin is not erased by successful matching.

The current QH-8 source-backed contract still requires exact evidence on every
candidate, including relations. It does **not** accept an evidence-free external
proposal as a shortcut. The future submission input must define its receipt/evidence
representation and authorization before implementation; it must preserve this
provenance distinction without pretending unavailable evidence was verified.

Current READ_CONTEXT is an additional owner-read gate, not permission to write,
submit, disclose to an LLM or act across spaces. Explicit operation authorization
must precede protected reads, processing and disclosure. MCP grants no extra rights;
external clients cannot select owner, canonical IDs, trusted schema, validation
actor/state or confirmed-current pointer. Every accepted AI proposal remains
`proposed`. Only the existing explicitly authorized human-validation workflow may
create a confirmed revision; this PR adds no such workflow.

## Future inbound application contract — documentary only

An inbound proposal-submission interface would be owned by `app/understanding`,
with authenticated QH actor, explicit target Context Space, client submission key,
provider-neutral candidate envelope and declared provenance/optional references to
available evidence. Trusted adapter context supplies the actor; payload claims do
not grant authority. The application checks operation policy, source access, scope,
replay identity, provenance class and canonical invariants before publication.

Reuse item/entity/relation proposals and existing repository/policy contracts.
`LLMProvider` remains outbound generation and must not be used to impersonate an
external submitter or trigger compulsory re-extraction. This sketch is not a public
DTO, wire schema, new Core port, stable signature or implemented MCP/public API.
Receipt representation, public versioning, idempotency/conflict rules and permission
mapping are future ticket decisions; no unspecified persistence/permissions are
implemented in anticipation of them.

## Citation-resolution increment

The frozen 2026-10-16 Mistral outputs show good literal retention alongside eleven
wrong spans, three relation candidates without evidence and independent semantic
errors. Add an explicit, deterministic source-backed resolver before the unchanged
strict validator: locate exact nonempty quote occurrences within authorized original
turns, require uniqueness, derive Unicode code-point offsets and retain derivation
hashes/audit separately from untouched original output. Do not use approximate text,
provider offsets or semantic guesses to disambiguate; absent, ambiguous, foreign or
cross-turn evidence fails the complete batch. Revalidate derived checkpoints before
publication using a distinct extraction key; never rewrite original captures or
published revisions. No provider prompt/response-format change is needed.

QH-8 batch publication stays atomic. Diagnostic candidate review is not partial
canonical acceptance. Granular validation/staging can be studied separately but
must not publish valid siblings of a rejected candidate in this increment.

## Boundaries and consequences

No new service, hosted model, dependency, table, migration, public API/tool or new
permission is introduced. PostgreSQL remains canonical, Neo4j replaceable derived
state. Existing history/ADRs and frozen baselines remain intact. Replay and tests
use captured responses only, with no paid calls or persistent QH writes. Resolver
success certifies locators/contract compliance, not semantic accuracy or independent
validation of the assistant-authored provisional reference.
