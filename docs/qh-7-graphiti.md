# QH-7 Graphiti adapter

Graphiti 0.30.2 is pinned with a hash-locked dependency set. It runs as a Python
library inside the backend, using the existing Neo4j 5.26 service. Core's
`ContextEngine.search` contract is unchanged. No REST/MCP/client operation is
added; production startup does not instantiate the adapter. PostgreSQL is never
read or written by this adapter; canonical ingestion remains QH-8.

## Responsibilities and derived provenance

`adapters/context/graphiti.py` translates Graphiti edge results to QH
`ContextSearchHit` values. `group_id` is a deterministic UUID5 namespace of the
Context Space ID, with explicit nonempty search scope. It is a technical partition,
never authentication or authorization. Backend callers must authorize the entire
scope before adapter access and external disclosure. No production endpoint exposes
these adapter operations or bypasses the existing policy boundary.

`ingest_source` is an adapter-only test/integration entry point, not a new Core
port or canonical ingestion workflow. It accepts existing QH source/revision IDs,
text and an aware reference time. UUID5 of the space/source/revision tuple identifies
the derived episode; its versioned `source_description` encodes those IDs.
Graphiti 0.30.2 interprets an explicit `add_episode(uuid=...)` as a lookup of an
existing episode. The adapter therefore creates the derived `EpisodicNode` first
when missing, using the public Graphiti node API. Existing episodes must match
scope, source descriptor, text, type and reference time; conflicting inputs fail
before provider access and never overwrite that episode. A denied extraction
can leave this synthetic/derived episode without extracted entities or edges. This
is disposable semantic state, not a canonical mapping table or trusted proof of
ownership. QH-8 still owns source persistence and canonical episode mapping.
Prior episodes are explicitly empty for this single-source integration; it does
not promise multi-source contextual ingestion or duplicate-ingestion idempotence.

Retrieval reads episode descriptors from Neo4j, so provenance survives adapter
reconstruction. Edges and all cited episodes must match the requested partition
and deterministic descriptor identity. Missing, foreign or malformed provenance
fails the entire retrieval closed. Results carry source revision refs and no
confirmed Understanding Item revision. Search uses a private copy of the edge
hybrid cosine/BM25 recipe with local RRF; paid reranking is disabled. No deletion,
canonical validation, Understanding Items, projections or sharing is implemented.

## Provider compatibility and model selection

Mistral Cloud is the approved initial provider. The factory explicitly supplies
all Graphiti clients; it cannot silently fall back to OpenAI. Provider SDKs and
configuration remain outside Core. Replacing the provider changes this assembly,
not Core's port or return types.

Pinned-source review and an offline HTTP contract test cover:

- `OpenAIGenericClient` chat completions with JSON Schema response format;
- `OpenAIEmbedder` using `mistral-embed` and its 1024 dimensions;
- no OpenAI-specific `dimensions` request parameter; single-text arrays and floats;
- disabled SDK retry (`max_retries=0`), overridden Graphiti retry, no paid reranker;
- telemetry disabled before Graphiti construction;
- Neo4j driver constructed outside a running loop to avoid implicit index writes;
  schema initialization occurs only through the explicit `initialize()` operation.

`mistral-small-latest` is an extraction candidate for compatibility testing, not
a final model decision or a verified live extraction result. `MISTRAL_LLM_MODEL`
has no default and must be chosen explicitly. Alias revisions may change; record
the actual model in the per-request review before live verification. The pinned
Graphiti generic client sends the configured main model for extraction; its
small-model setting is deliberately the same model. `mistral-embed` is the initial
embedding configuration. Schema quality and actual semantic behavior remain to
be verified through individually authorized real requests before final selection.

References checked during implementation: [Graphiti provider configuration](https://help.getzep.com/graphiti/configuration/llm-configuration),
[pinned generic client](https://github.com/getzep/graphiti/blob/v0.30.2/graphiti_core/llm_client/openai_generic_client.py),
[pinned embedder](https://github.com/getzep/graphiti/blob/v0.30.2/graphiti_core/embedder/openai.py),
[Mistral structured outputs](https://docs.mistral.ai/studio/conversations/structured-output/custom),
[Mistral embedding API](https://docs.mistral.ai/api/endpoint/embeddings),
[1024-dimensional text embeddings](https://docs.mistral.ai/resources/cookbooks/mistral-embeddings-embeddings).
Documentation compatibility is separate from a successful real-provider smoke.

## Cost authorization and manual smoke

`billing.py` gates every HTTP attempt. Default authorization denies all calls.
Only configured Mistral HTTPS POST endpoints/models are allowed. Redirects,
streaming, provider retries and paid reranking are disabled. Each approval covers
one request body only and is consumed even on failure. Embedding batch operations
are split into serial single-text requests; each needs its own approval, and the
HTTP boundary rejects arrays with multiple inputs. No permit is cached;
concurrent Graphiti requests wait for separate approval prompts.

The manual terminal prompt displays provider, endpoint, model, extraction/embedding
purpose, payload hash/size, maximum output tokens where available, and cost status.
The current estimate is explicitly unavailable: exact input tokenization and a
verified tariff for the selected model are not configured. Before an agent executes
a real request it must also present any calculable estimate to the owner in chat
and wait for explicit authorization for that single request. Terminal confirmation
must never be entered by the agent without that authorization. A smoke invocation
can generate many calls; invocation approval does not authorize those calls.

The actual API key belongs exclusively in the ignored local VPS `.env`. Never
paste it into the conversation, pass it as a command argument, print environment
or expanded Compose configuration, or commit it. Example files contain only an
empty placeholder. Optional Compose environment forwarding is for explicit manual
runs and causes no startup request. Existing containers need not be replaced.

After separately reviewing model compatibility and setting the local `.env`, build
the backend image with `make build` (or build only backend). The explicit manual
entry point is `make smoke-graphiti`. It requires a terminal; it is not part of
startup, `test`, `verify`, `verify-running` or CI. Do not invoke it automatically.
For agent-assisted execution retain the interactive process, show each pending
request to the owner, then enter its unique `ALLOW` token only after the matching
explicit authorization. A refusal/error stops the smoke; no automatic retry.
The synthetic UUID-named scope is printed and retained for inspection. No existing
data or volumes are deleted. Partial derived state can remain after a stopped run.

The manual smoke creates indexes without deleting existing ones, ingests a harmless
synthetic source, searches through `ContextEngine`, checks source revision provenance
and searches a different empty space. Real semantic extraction and embedding
calls are required for the ticket's live Done criterion, so mocks cannot complete it.

See [executed verification and remaining Done criterion](verification-qh-7.md).
