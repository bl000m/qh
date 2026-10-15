# QH-7 — offline observability correction

The 8B experiment remains stopped. This change performs **zero external API
requests** and does not change QH Core, public contracts, extraction prompts,
models, canonical persistence or QH-8 responsibilities.

## Where the original cause disappeared

The fourth response followed this path in Graphiti 0.30.2:

1. The synthetic transport received HTTP 200, read the response, checked usage and
   finish_reason, and saved usage. It discarded the chat content after returning
   the response to the SDK.
2. The OpenAI SDK decoded the completion envelope; Graphiti's
   OpenAIGenericClient read message.content, stripped code fences and called
   json.loads. HTTP 200 does not establish JSON/schema/semantic validity.
3. The QH NoRetryClient validated the parsed response against the Pydantic response
   model, then called ExtractionSession.validate. Generic entity reference,
   episode reference and typed-time checks ran **before** the fixture observer.
4. Only that observer saved a parsed extraction observation. None was recorded
   for request 4. Thus a downstream persisted relation cannot be inferred; the
   evidenced failure boundary is before completion of this observer path.
5. Factory failure handling stored only a failure string. Quality handling used
   `raise ... from None`; session.check could later raise another error after an
   optional Graphiti stage swallowed the initial exception. The adapter also used
   `raise ContextEngineError(...) from None`, hiding the original traceback chain.
6. The smoke runner stored only the outer exception's class, while disabling logs.
   Together these decisions lost both response content and usable failure cause.

The saved ledger, stdout and local graph audit cannot establish whether the
fourth response failed JSON parsing, schema validation, generic consistency or
another upstream operation. There is no retained fourth content or original
request hash. No evidence identifies Neo4j as the cause. Local B has its derived
episode but no entity/relation records, consistent with an interrupted ingestion.
The missing response is **not reconstructed or invented**. Tests below inject
representative failures; they are not replays of that lost response.

## Implemented diagnostics

Adapter-local FailureDiagnostic contains category, phase and explicit cause-chain
exception types. It never serializes exception messages, tracebacks, credentials,
headers, SDK request objects or arbitrary exception attributes. Categories:

- llm_parsing: JSON decoding within the LLM stage.
- llm_schema: Pydantic response validation within the LLM stage.
- qh_consistency: generic integrity checks or declared smoke fixture assertions.
- neo4j_persistence: Neo4j/driver exceptions, including episode save and errors
  propagated through Graphiti; driver setup has its own phase.
- graphiti_internal: remaining Graphiti/adapter operations; an unknown failure
  inside the LLM client is separately labelled llm_internal rather than guessing
  that it is a schema error.

Typed Neo4j causes are recognized through explicit exception chains. A generic
upstream exception which discards its own typed cause cannot be asserted to be a
Neo4j failure; it stays internal/unknown. JSON errors outside an LLM stage are
not misclassified as provider parsing errors.

ContextEngineError keeps a safe diagnostic and explicit original cause, in memory.
ExtractionSession keeps the first failure cause across swallowed optional-stage
errors, preventing later provider requests or a successful result. Fixture/quality
errors preserve their own cause and extraction phase. No new production logger,
API error payload or public error contract is introduced.

Detailed recording is opt-in only in the dedicated synthetic smoke runner:

- Whitelisted chat request fields (model/messages/response_format/temperature/
  max_tokens) with extraction phase, enabling exact future prompt/schema replay.
- Received completion content and finish_reason, saved **before** SDK parsing,
  Pydantic validation or QH checks; malformed envelope text is retained for this
  synthetic-only transport when necessary. No request/response headers.
- Technical reference_time, explicit ingestion status and stage, separate from
  semantic dates and HTTP success. The final checkpoint retains the classified
  error and chain types. Ledger files are created with mode 0600.

Capture defaults off. Only the fixed synthetic B runner enables it. It must never
be enabled for real/private sources; no factory/startup/CI path enables capture.
The provider guard still enforces request/budget limits and no retries/parallel
sends. Production has only metadata/in-memory causes; content recording remains
in test tooling. Failed/partial derived data are not repaired or deleted.

## Executed offline checks

Docker backend pytest: tests/test_context_diagnostics.py,
tests/test_extraction_quality.py, tests/test_graphiti_context.py,
tests/test_architecture.py, tests/test_contracts.py. The real pinned SDK/client is
used with httpx.MockTransport and mocked persistence; no test sends real HTTP.
Regressions cover HTTP 200 with malformed JSON/schema/inconsistent endpoints,
errors swallowed by optional stages, internal Graphiti failures, Neo4j failures
at episode save and inside Graphiti, safe metadata, disabled content capture by
default and explicit failed ingestion status. Prior saved-real-3B payload tests
are reused. All categories retain their causes; HTTP success never implies
successful ingestion. Ruff, whitespace and credential/index checks also apply.

## Prepared minimal repetition — not authorized, not executed

`prepare_qh7_b8_segment.py` is an exclusively offline tool: every SDK HTTP send
uses MockTransport, no CLI option can enable live HTTP. It combines the saved 8B
entity list with the retained synthetic episode/reference_time and Graphiti 0.30.2
prompt/schema to prepare a **candidate** edge-extraction request. No embeddings,
entity extraction, database writes or search are needed for this isolated stage.
Its mock `{edges: []}` reply only permits request serialization; it is not a model
result and never an accepted smoke fact.

Executed preparation using copies of docs/evidence/qh7-b8-smoke.json and
qh7-b8-local-audit.json inside the existing backend container, with output
/tmp/qh7-b8-edge-offline-request.json (also copied to the host /tmp). SHA256:
`c92113f29045e1d48231b3a80898ec4a1d248ca4162aeb945e328658931879cf`.
The original request hash is absent, so byte identity cannot be proven. The
candidate uses saved entities, source and technical timestamp, not fabricated
missing model output.

Proposed future authorization: **one** POST
https://api.mistral.ai/v1/chat/completions, model ministral-8b-2512, max output
16384 tokens, synthetic B edge extraction only; no retries, embeddings or other
requests. Expected cost around **0.0003 USD** using the prior segment's usage as
an example; conservative pre-send estimate **0.0037443 USD**, proposed ceiling
**0.004 USD**, at the already recorded 0.15 USD/M input/output tariff. These are
estimates, not invoice amounts; tariff assumptions must be checked before any
future live send if they change. This document grants no authorization.

The future bounded runner should load the prepared request, use the same
synthetic transport capture and one-request/budget guard, validate the response
schema and QH/fixture consistency against the saved entities, and stop before any
other call. A successful isolated segment would not establish complete ingestion,
retrieval, provenance or two-space isolation. A changed/missing source or checkpoint
must stop the preparation. New authorization is required for that real repetition.
