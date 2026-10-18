# Demo A — three synthetic Spaces and the next UX increment

2026-10-17. Owner-requested planning addendum to QH-13 / [PR #14](https://github.com/bl000m/qh/pull/14).
**Persistent import NOT EXECUTED; no write or paid-call authorization.** No UI
redesign, merge, Jira transition or new ticket is performed by this addendum.
The [Product Contract amendment](product/QH_PRODUCT_CONTRACT.md#demo-a-experience--owner-amendment-2026-10-17)
records product direction; [ADR 0006](adr/0006-scoped-contextual-chat.md) and the
[QH-13 report](qh-13-contextual-chat.md) describe implemented chat and verification.

## Execution follow-through — 2026-10-18

The owner subsequently authorized this exact synthetic import. It has now been
[executed and verified](qh-13-demo-a-execution.md); the three Alice-owned Spaces
are retained. The sections below preserve the planning checkpoint approved at
`d90647a`, including its then-unexecuted status. UX ticket [QH-43](https://contextlab.atlassian.net/browse/QH-43)
is created but not started. Mistral/merge/DONE gates remain closed.

## Dataset and observable scope

Use the three cases in [qh8_conversations.json](../apps/api/tests/fixtures/qh8_conversations.json),
one conversation per **new**, explicitly synthetic Alice-owned Space:

| Fixture / proposed display name | Useful demo content | Boundaries |
| --- | --- | --- |
| project / Demo — Projet pilote (synthétique) | Pilot choice, possible benefit, measurement question, reversible pause, Alex entity and stated_by relation | Team Cedar is mentioned, not a separate fixture entity; no invented event interval |
| health / Demo — Bien-être (synthétique) | Gentle walk, tentative rest, recording question, pause in training, Alex and stated_by | Entirely synthetic; not a diagnosis. Reported tiredness is in the source but not independently extracted as a claim |
| personal / Demo — Organisation personnelle (synthétique) | Dinner choice, tentative benefit, attendance question, pause in planning, Alex and stated_by | Preference is not a personality trait; no invented attendees |

Each has three original turns, four generic items, one entity and one relation.
All six revisions remain `proposed`, with no confirmed-current pointer or validation
actor. Descriptor assignment `asserted` does not confirm content; `expected_effect`
is tentative. Domain strings are fixture metadata, **not a Domain model**.
Each source and item initially has **one** revision: revision detail/history is
navigable, but this seed does not demonstrate successive versions. Do not fabricate
history to make the demo appear richer. `stated_by` records reported speech, not
sole decision authority. This is a scripted fixture, not measured LLM extraction.

The four [unseen conversations](../apps/api/tests/fixtures/mistral_unseen_conversations.json)
(work/evolving/personal/multilingual) remain evaluation/stress material. Their
[frozen Mistral captures](qh8-mistral-evaluation.md) and
[QH-32 derived replay](qh8-citation-followup.md) include unresolved semantic errors
and a rejected batch with missing relation evidence. Do not seed them as if they
were accepted understanding, copy historical rows, change their owners or repair
their semantics silently. The richer `personal` case is distinct from this seed's
`personal` fixture.

## Import plan — authorization required before the first persistent write

This is an operator procedure to prepare, not an existing turnkey seed command.
Do not point an integration-test harness at the persistent database.

1. **Read-only preflight.** Resolve Alice through existing OIDC → internal QH
   identity, verify active ownership/policy, schema 0005, the three exact registered
   generic profiles and existing worker/graph readiness. No user ID from a request
   payload. Inventory all existing rows/owners, outbox/state, container IDs/mounts,
   private config hashes and current ledger hashes. Preserve everything, including
   empty Alice Spaces and other owners' historical smoke data. Present this plan
   and obtain explicit approval covering the exact three-Space synthetic import.
2. **Fresh recovery evidence before canonical writes.** After authorization, take
   a protected logical backup of the actual database then present, verify archive
   readability and rehearse restore on an approved disposable target using existing
   test infrastructure. The older hot-reload backup predates later data and is not
   a current backup. Retain mode-600 dump/receipts, mode-700 archive directory,
   schema/registry/canonical/outbox hashes and runtime config/mount identities outside
   Git/build contexts. Backup/restore commands must never print credentials.
3. **Create once, journal, freeze targets.** Through existing authenticated
   ContextService create exactly three new Spaces. Save each returned UUID and
   owner/creation receipt durably before proceeding; bind the manifest to Alice's
   resolved identity and exact fixture hashes. An operator lock prevents concurrent
   runs. Name/domain are not unique identities and must never select a Space alone.
   The API uses random UUIDs and has **no idempotency-key contract**. On a timeout
   or crash with an uncertain create result, stop, compare before/after inventory
   and reconcile the exact owned creation receipt; do not blindly repeat POST.
   Ambiguity requires owner/operator resolution. A rerun with complete receipts
   reuses those Spaces and never creates new ones. There is no exactly-once creation
   guarantee across an unrecorded response; fail-closed reconciliation is required.
4. **Freeze canonical import manifest.** With those receipts, calculate all IDs
   below and source/request/output/checkpoint hashes **offline**, inspect content,
   then confirm the authorized manifest still matches the planned payload. If it
   differs materially, STOP AND ASK again. Import each verbatim conversation via
   `UnderstandingExtractor.import_conversation` and the Alice-bound
   CanonicalRepository. The source commits before interpretation; its original
   acquisition timestamp and turn locators remain intact, distinct from import time.
5. **Derive and publish each complete batch.** Use `FixtureUnderstandingProvider`
   (no network), freeze its original checkpoint, then explicitly invoke QH-32
   `resolve_citations` with a distinct extraction key. Missing/ambiguous/foreign
   evidence rejects the full batch. Preserve original plus derived checkpoint/audit;
   publish only the validated derived checkpoint via `UnderstandingExtractor.publish`
   → CanonicalRepository. Three atomic six-revision batches, **not a cross-Space
   transaction**. No partial sibling publication, registration, confirmation or
   new persistence system. The existing writer uses `origin_kind=ai`; the retained
   operator manifest must explicitly record scripted fixture origin, not real
   Mistral generation. Do not add arbitrary unapproved provenance fields.
6. **Existing worker and acceptance.** Let the running worker apply ordinary
   durable outbox intents, without replacing it, rebuilding unrelated scopes or
   invoking extraction again. Require exact expected IDs, canonical hydration and
   source quotes, proposed states and no pending/failed intents in the new scopes.
   Perform the Alice/Bob checks below and retain the completed manifest/checkpoints.

### ID/fingerprint contract and resume rules

| Field | Binding / deterministic rule |
| --- | --- |
| Seed receipt key | `demo-a-three-spaces-v1`, fixture case, real internal Alice ID, created Space UUID; protected durable receipt |
| Space UUID | Returned by existing create API; **not assigned yet**. Never use simulation UUIDs as persistent targets |
| Source UUID | `uuid5(UUID(space_id), "conversation:" + conversation.id)` |
| Source revision UUID | `uuid5(UUID(source_id), "revision:1")` |
| Original extraction key | `demo-a-fixture-v1-original` |
| Derived extraction key | `demo-a-fixture-v1-resolved` |
| Extraction namespace | `uuid5(UUID(source_revision_id), derived_extraction_key)` |
| Item / revision UUID | `uuid5(namespace, "item:" + local_id)` / `uuid5(namespace, "revision:" + local_id)` |
| Local IDs in each batch | `choice`, `possibility`, `question`, `pause`, `participant`, `relation` |
| Source fingerprint | Existing `UnderstandingExtractor.source_hash`: canonical JSON of id/source_id/context_space_id/revision_no/content/origin, SHA-256 |
| Other fingerprints | Raw fixture-file SHA-256; existing `digest` of each conversation/items/output/checkpoint; existing `request_hash` of provider request; exact receipt IDs and resolver audit |

[Offline rehearsal](evidence/qh13-demo-plan-20261017/README.md) records actual
fixture hashes and reproducible **simulation** IDs/fingerprints, not Alice IDs or
approved persistent targets. Real source/output hashes depend on the returned
Space UUIDs; materialize and retain them before source/proposal publication.
Exact source/checkpoint replay must preserve IDs and bytes; the repository rejects
conflicting immutable content. Changed fixture/key/content is **not** a retry: stop
instead of inventing fresh IDs to evade a conflict. The Space phase remains the
journal/reconciliation boundary described above, not a promised API feature.

### Expected persistent deltas on a first successful import

| Canonical table / effect | Per Space | Total for three |
| --- | ---: | ---: |
| context_spaces / context_projection_state | 1 / 1 | 3 / 3 |
| sources / source_revisions | 1 / 1 | 3 / 3 |
| understanding_items / understanding_item_revisions | 6 / 6 | 18 / 18 |
| item_revision_types / item_revision_provenance | 6 / 6 | 18 / 18 |
| relation_revision_details | 1 | 3 |
| projection_outbox revision intents | 6 | 18 |
| New confirmed/current-pointer events, users, OIDC links, registry definitions | 0 | 0 |

Trigger-created projection state starts at desired/applied 0/0. Source-only import
creates no revision intent; batch publication makes desired 6, and successful
worker acknowledgement makes applied 6. Worker delivery/leases update existing
outbox/state rows and derived Neo4j assertions; graph node/edge totals are adapter
implementation details, not additional canonical facts. Exact successful replay
adds zero sources/revisions/intents. Compare **deltas**, not hard-coded global totals;
other legitimate activity may change a live baseline.

**Failure/rollback controls:** failed source transaction adds nothing; failed batch
adds none of its six proposals, but an already committed source/Space remains.
If an earlier Space succeeded, retain it while investigating the next failure.
Stop further seed operations on mismatch, lost receipt, graph failure or unexpected
writes; retain sources/checkpoints and any durable intents. Do not delete synthetic
rows, clear queues, disable triggers, rewind ledger counters, replace owners, reset
graph epochs or restore an old dump over newer data. Resume identical verified
transactions only after diagnosis; any destructive repair/restore needs separate
approval. Backups are recovery evidence, not automatic rollback authorization.

## Offline result and browser acceptance

Executed with network disabled, no secrets/SQL/graph, using the existing QH-8
extractor, QH-32 resolver, Context Builder and mock. All three batches validate:
**18 proposed revisions, zero citation changes**, identical checkpoint replay IDs.
With deterministic simulation UUID ordering, a 32-character creation-time placeholder
and the initial question, each Space provides **5/6** revisions to chat (partial):
project 6,975 context bytes / 8,904 input bound; health 7,010 / 8,939;
personal 7,119 / 9,048. These are **bytes/allowance, not API tokens or cost**.
The mock cites only three excerpts. These simulation selections can change with
real UUID order, creation timestamps and dialogue length. No production hydration,
worker, persistence idempotence or Alice/Bob proof is claimed by this memory test.
Existing isolated SQL/Neo4j/OIDC/Chromium evidence remains in the QH-13 report.

This is already a useful limitation: even six small revisions can exceed the
8,000-byte context budget because provenance is included. The project mock answer
in this rehearsal quotes a hypothesis, a pause and Alex for a question about
**decisions**. It does not understand or rank the question. Do not advertise this
as correct natural-language answering; the demo establishes scope, explicit opt-in,
extractive references and no canonical write. All six remain separately browsable.
Retrieval scans at most two pages of ten per selected view, maximum forty records;
whole records are excluded to fit, with explicit partial coverage. No substring
query is presented as semantic search, and no cap is raised by this plan.

After approved import, verify from the Mac with existing private port forwarding:

1. Forward VPS loopback **5173, 8000 and 8080** to the same Mac ports. Open
   `http://localhost:5173`, log in as Alice through existing Keycloak Code+PKCE.
   Use `Mon environnement` to find the three named demo Spaces. Current login can
   restore a requested route; the always-dashboard landing below is future work.
2. Open each Space, select proposed understanding and inspect all six records,
   descriptors/certainty, the Alex entity, exact relation anchors, literal source
   spans and revision 1. Current-confirmed is correctly empty. Check all paginated
   records; absence in a chat excerpt is not absence from the Space.
3. Open **Discuter avec ce contexte**. With opt-in off, expect no usable context /
   insufficient response and no generation for these proposed-only Spaces. Check
   **Inclure explicitement les propositions non confirmées**, then ask
   `Quelles décisions avons-nous prises ?`. Expect labelled mock excerpts and
   expandable declared sources/all provided revisions, possibly partial coverage.
   Follow-up remains in the selected Space; changing opt-in/Space clears dialogue.
4. Record complete `provided_revisions`/declared reference IDs and verify they all
   belong to that Space. Check canonical counts/current pointers before/after:
   chat must write nothing. Do not infer semantic support merely from ID membership.
5. Log out, log in as Bob: none of Alice's three Spaces appears in his owned list;
   direct URLs, browse, exact revision and chat requests return uniform 404, before
   any provider invocation. Alice/Bob denial is already tested in isolation;
   **these newly seeded persistent targets are NOT TESTED until import approval**.

If graph understanding is unavailable, show the existing error and stop; do not
fall back to unverified SQL, create another Docker stack or modify realm/ports.

## Next UX/branding increment — proposed ticket, NOT created

Suggested title: **Demo A — environment landing, chat-first Space and QH branding**.
Priority: P1 demo usability. Owner confirmation of this scope is required before
creating a Jira ticket or implementing it; no key is assigned. No redesign in PR #14.

- After successful login, land on `Mon environnement`; preserve state/verifier PKCE,
  token-in-memory, issuer/callback validation and separate owner authorization.
- Refine the existing multi-Space overview. Design toward `Mon environnement → Domaine →
  Context Space`, but ship no fake Domain grouping, Domain table/API or sharing.
- Make chat the primary in-Space action; place the existing understanding overview,
  open descriptors, items/entities/relations, provenance and history under an
  accessible expandable **Explorer la compréhension**. Keep data discoverable
  without first knowing a search query. Preserve state labels and proposal opt-in.
- Apply owner-supplied logo, white/black/red and restrained glass/iridescent visuals
  to the existing client. Test keyboard navigation, contrast, narrow layouts and
  readable loading/empty/error states. No decorative effect may obscure state.
- Prepare a coherent Keycloak login theme using supported presentation mechanisms,
  preserving hosted OIDC login. Activating/replacing IdP theme assets is a separate
  authorized runtime operation; no realm, password or authentication redesign.

Verifiable acceptance: login landing checked after fresh login/reload; Alice sees
only owned Spaces; chat primary and exploration operable by keyboard; explicit
unconfirmed choice/reset and canonical citations unchanged; supplied visual assets
traceable/licensed; TypeScript/build/accessibility/browser/OIDC regressions pass.
Keycloak visual preparation and actual theme activation must be reported separately.
No Domain backend, interactive validation/editing, advanced graph UI, generated
synthesis, QH-39 ingestion or live model inference belongs to this small increment.

**Asset hand-off:** owner transfers originals to ignored, build-excluded
`/home/ubuntu/qh/.local-archive/branding/incoming/` (create only for that hand-off),
using VS Code remote file transfer or SCP. No asset package is assumed present.
Prefer original **SVG logo** with viewBox and vector paths, plus transparent PNG
at 1,024–2,048 px, light/dark variants and icon/favicon variants if available.
Include the reference presentation PDF/PPTX, screenshots, exact palette, spacing/
logo rules, font names and redistribution licences (WOFF2 only if licensed), and
original glass-sphere artwork in PNG/WebP/AVIF with transparency where intended.
Do not send passwords or private .env files with artwork. After owner approval and
asset review, only approved public web assets move to `apps/web/public/brand/`;
source presentations remain private unless publication is explicitly authorized.
Missing assets do not authorize an invented replacement logo.

## Separate gates and next capabilities

| Capability | Current boundary |
| --- | --- |
| QH-13 | Implemented ephemeral scoped chat, bounded Context Builder, replaceable LLMProvider, mock and canonical references; no understanding write |
| Demo seed | Planned owner-authorized internal fixture publication through existing Engine/repository/worker; NOT EXECUTED, no conversational acquisition UI |
| QH-39 | Future authorized conversation → original source revision → extraction → proposed understanding; existing Engine only, no automatic confirmation |
| Real Mistral trial | NOT EXECUTED; separate transmission/spending consent and private backend activation required |

For a real trial, first approve an exact manifest of **only the three synthetic
owned scope UUIDs**, source/context/dialogue disclosure, provider endpoint
`https://api.mistral.ai/v1/chat/completions`, model `mistral-small-2603`, purpose,
expiry and payload inspection. No historical owners, real health/personal data or
other Spaces. Verify current model availability, prices and a conservative EUR/USD
ceiling at that time; today's document does not assert current prices.
The prepared adapter allows at most **8 attempts**, input bound **12,000**, requested
output **1,000 tokens**, **USD 0.20 sublimit** and **EUR 5 maximum** (including a
conservative exchange/charge allowance); use the stricter limit. Confirm that the
verified cost envelope fits both before enabling it. These are caps/estimates,
not observed usage or charges. A three-Space first pass would use three requests;
extra calls require an explicitly approved allocation within the same ceiling.

Use a new purpose-marked QH-13 ledger and private approval files, preserve the
QH-8 ledger/captures unchanged, count failed attempts/reservations, no automatic
retry or parallel trial. Stop on HTTP 429/provider error and retain only sanitized
status/relevant headers; do not reset budgets or expose keys. Current Compose does
not forward live provider settings: any future scoped configuration/mount activation
requires separate runtime approval. Key presence alone is never consent.
A local model remains a future LLMProvider adapter, not a reason to change chat,
retrieval or canonical architecture now.
