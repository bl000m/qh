# QH-9 — authenticated Context Space metadata REST

2026-10-17 · [QH-9](https://contextlab.atlassian.net/browse/QH-9), manually set to
En cours · baseline `d61608deea7de86bfb528768df7ba8fee2c7cb05` · checkout
`/home/ubuntu/qh`, branch `feat/QH-9-context-spaces`. Candidate implementation,
**not deployed, not DONE**. Merge and Jira status changes require owner review.

## Contract and implemented path

Authenticated user → FastAPI → Core ContextService contract / `ManagedContextService`
→ existing PolicyService → existing PostgreSQL `context_spaces`/`users` tables.
OIDC QH-5 still verifies signature, issuer, audience, expiry and general access,
then resolves issuer/subject to an active internal QH identity. Request bodies,
query parameters, headers and untrusted token identity aliases cannot set an owner.
There is no second authenticator, policy or canonical store, and no migration.

| Method/path | Request | Response |
| --- | --- | --- |
| `POST /context-spaces` | `{"name":"Space A"}` | 201, metadata and relative Location header; owner comes only from authenticated identity, ID is server-generated, status starts active |
| `GET /context-spaces` | Optional `limit` 1–100 (default 20), `after_id` UUID | 200, `{"items":[...],"next_after_id":null}`; owned active Spaces only, ordered by UUID with keyset pagination |
| `GET /context-spaces/{context_id}` | UUID, no extra query parameters | 200, authorized metadata |
| `PATCH /context-spaces/{context_id}` | `{"name":"New name"}` | 200, renamed metadata; original ID/owner/creation time preserved |

Metadata fields are `id`, `owner_id`, `name`, `status`, `created_at`, `updated_at`.
Names must be strings with 1–256 Unicode characters, not whitespace-only or NUL;
valid spelling/whitespace is otherwise preserved. Duplicate names are allowed.
Extra body fields (including owner, ID, status, description) and unsupported or
duplicated query parameters reject with 422. Invalid UUIDs reject with 422.
There is no description column in the approved schema; no new field is invented.
Metadata renames use last committed write semantics, not item revision publication.

Missing/invalid tokens return 401; the existing general OAuth gate returns 403
before resource access. Missing and foreign UUIDs both yield the same 404
`Context space not found`, without disclosing existence or owner. Storage or owner
lookup unavailability yields a generic 503; driver/connection details are not sent.
No `/access` endpoint or Understanding retrieval route is added.

## Policy, storage and composition

The same OwnerPolicyService gains narrowly scoped `CREATE_CONTEXT`, `LIST_CONTEXTS`
and `UPDATE_CONTEXT` actions. Create/list apply only to the authenticated subject's
own namespace, without a caller-supplied target owner/scope. Read/rename resolve
ownership through the existing read-only security adapter before metadata reads
or writes. Other previously unsupported actions still fail closed.

Listing first authorizes LIST_CONTEXTS, selects only owned active IDs, then checks
READ_CONTEXT before hydrating each returned Space. A stale/denied ID rejects the
page; no partial response is returned. At most 100 entries are returned, with one
extra ID for pagination. This bounded implementation uses per-entry policy/read
calls; it makes no indexed multi-user sharing or large-list performance claim.
Current resource policy is owner-only: shared grants remain future work.

The PostgreSQL repository uses parameterized queries, active-user checks and
owner/status predicates on all reads/updates. These predicates fence policy/DB
race windows; they do not replace PolicyService. Create inserts only for the
active authenticated user. Each operation owns a short transaction and connection;
no request changes ownership, schema, sources, understanding revisions or outbox.

Bootstrap supplies the concrete repository and application use case through
ApplicationServices, sharing the exact same policy instance with SecurityBindings.
Unimplemented projection/chat services stay unbound; no production fake is installed.
Space management works with the native graph runtime disabled and requires no
Neo4j access. The existing Core `retrieve` signature remains reserved for QH-10;
this implementation explicitly leaves understanding retrieval unimplemented.

## Deletion and lifecycle boundary

No DELETE route, archive/status mutation, ownership transfer or cascading removal
is implemented. DELETE on a Space path returns 405. A lifecycle/retention decision
must precede any deletion behavior. Tests seed inactive users/Spaces directly in
their disposable databases to verify denial; that is not a public archive API.
QH-10 retrieval, QH-11/12 UI, QH-13/39 chat/extraction, sharing and MCP are outside
this increment. The VPS remains on `c723d32`, schema 0005; Demo A deployment belongs
to the separately authorized QH-12 window, not this PR.

## Verification and Definition of Done

Actual Jira criterion:

> Un utente vede solo spazi propri o esplicitamente autorizzati; CRUD REST da API verificato con identità OIDC reale o fixture equivalenti. Riutilizzo del controllo owner QH-5 dimostrato, senza endpoint /context-spaces/{id}/access separato.

| Criterion | Result / delivery classification |
| --- | --- |
| Authenticated create/list/open, owner from identity only | PASS — implemented/tested on real HTTP routes, same OwnerPolicyService and PostgreSQL repository |
| Alice creates A → lists A → opens A; Bob denied | PASS — signed-token HTTP tests and real SQL integration on 0002/0005; uniform denial and empty foreign list |
| Metadata update, invalid input and injection resistance | PASS — rename only, owner/status/ID overposting denied; SQL injection-looking name stored literally |
| Persisted identity and reopening | PASS — close/recreate application/service/repository, reopen exact ID and values through HTTP; direct SQL comparison |
| Isolation and authentication regression | PASS — unknown/foreign IDs, inactive users/Spaces, malicious headers/claims/query parameters, stale permission fence and generic storage failures |
| Core/DI and existing evidence integrity | PASS — framework-free boundary checks, same policy binding, QH-33 frozen files preserved; see audit evidence |
| Reviewed merge and Jira closure | PENDING — not authorized by implementation request; technical delivery only |
| Destructive deletion/lifecycle, shared grants and later Demo A features | OUT OF SCOPE — no implementation or hidden fallback |

The JWKS response in QH-9 HTTP/SQL tests is a fixture; RSA signatures, token claims,
issuer/subject mapping and all owner/metadata SQL are real. Existing OIDC regression
and hosted Keycloak tests remain separate evidence, not a newly invented login flow.
Application reopening is tested; no VPS/container restart is performed.

Executable/OCI revision `2f8386aa2efb8d74e30ceb589ab4abc1a6d45c76`, image
`qh9-context-spaces:2f8386aa2efb8d74e30ceb589ab4abc1a6d45c76`, immutable ID
`sha256:7f5de34d7194d15646291fb6963c0ac20c8ede3974f4999bc79c6f7406a8460b`.
Built from Git archive; no ignored files or credentials in build context.

- Targeted Docker HTTP/Core/OIDC/policy/architecture checks: **145 passed**, 5.42 s.
- PostgreSQL-only acceptance in the final image: **8 passed**, 11.22 s; unique databases on the existing
  dedicated test server, schemas 0002 and 0005; only test-created databases removed.
- Ruff PASS; frozen v1/v2 audit PASS. The historical architecture test is hash-pinned
  by QH-33: new context boundary checks reuse its helper from a separate test file,
  preserving the original file and all frozen manifests/annotations/ledgers.
- Full strict integration at the preceding executable `c8a9c09`: **441 passed,
  zero skips**, 457.97 s, exact image without source mounts. The later `2f8386a`
  cleanup adds only guaranteed connection close and its failure regression;
  all 145 targeted tests plus eight SQL cases above pass in that final image.
  Final head CI results are recorded on the associated PR after actual execution;
  targeted counts overlap integration and must not be summed.
- The transaction helper now always closes its connection even if commit fails,
  following the existing CanonicalRepository pattern. The new regression checks
  connection release and sanitized error propagation, without touching a live DB.

Full isolated execution, using only dedicated credentials:

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  -w /workspace/apps/api --entrypoint python \
  qh9-context-spaces:2f8386aa2efb8d74e30ceb589ab4abc1a6d45c76 \
  -u /workspace/scripts/run_qh30_integration.py
```

Existing Starlette/AnyIO deprecation warning remains non-blocking. No dependency
or lockfile changes, new infrastructure, paid calls, persistent migration or VPS
service replacement. Test success alone does not make QH-9 DONE; stop for review.
