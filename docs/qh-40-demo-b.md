# Demo B — owner sharing and verified guest experience

QH-18/QH-21/QH-22 complete the browser consumer of the merged QH-55/QH-19
disclosure engine and QH-20 mailbox authentication. The owner's 25 October sprint
mandate authorizes this grouped increment. PostgreSQL is canonical, Neo4j derived;
no persistent VPS activation is included.

## Implemented path

`SharingControl` configures invited email, purpose, READ/ASK_AI and expiry. Scope
is automatic, proposals excluded by default, quotations optional. The actual safe
preview shows exclusions, masks, proposed/confirmed labels and the named residual
free-text/reidentification risk. One targeted owner disclosure approval precedes
snapshot materialization and invitation creation; it never confirms knowledge.
There is no mandatory item checklist or public bearer-link option.

`GuestPage` clears the invitation fragment from the address bar, exposes no private
content before delivered-code verification, and resumes through the secure HttpOnly
cookie. Every API request rechecks policy, rights, snapshot binding and expiry/revoke.
Open pages poll every three seconds to remove stale displayed content; server-side
revocation applies immediately to subsequent requests. Revocation cannot retract
bytes already read or copied. Guests have no Space or canonical write permissions.

`app/api/sharing.py` delegates preview/approval to the existing `DisclosureService`.
`adapters/sharing.py` assembles existing projection, policy and guest services at
the application boundary. An explicit HTTPS factory binding and reviewed schema
0009 are required; default bootstrap and frontend flags leave sharing disabled.
The original owner OIDC path is unchanged; guests are not new QH accounts.

`GuestSnapshotChat` passes only the frozen minimized payload and the explicit
question to `OfflineSnapshotProvider`. No graph/source retrieval or paid transport
is available. Output admits exact snapshot aliases only, then renders literal safe
excerpts and rechecks access after generation. Both UIs state that this is a local
simulation, not an answer-generating inference or a semantic quality guarantee.

## Verification and limits

Risk C (sharing/security). The final focused browser scenario is **1 PASS** (1.2m),
with confirmed and proposed content, masked contact/quotations and an excluded
clinical canary. The owner desktop and guest 375px screenshots were inspected.
The earlier proposal-only run also passed; the mixed-state fixture was added to
close acceptance coverage. No application workaround was needed. Its initial
fixture review correctly refused an unready graph; fixture setup now drains the
real derived projection before the ordinary canonical review operation.
Implemented/tested rows below refer to isolated checks, not VPS activation.

| Criteria | Evidence / verdict |
| --- | --- |
| PASS — Owner editor, actual preview, explicit proposal inclusion and targeted risk decision | `sharing.browser.spec.ts`; real signed OIDC/API tests in `test_sharing_pipeline.py` |
| PASS — Delivered OTP, no link-only access, wrong email/code, cookie resume | Browser Alice → Mailpit UI → Clément; SMTP delivery and secure API, no injected code or terminal user step |
| PASS — Confirmed/proposed distinction; excluded clinical canary, masked contact and quotations | Exact synthetic UUM fixture; owner and guest assertions and mobile screenshot |
| PASS — Guest READ/ASK scope, no writes, unauthorized provider/aliases, adversarial question | New API/browser checks; provider spy sees exactly the minimized snapshot, not original sources |
| PASS — Revoke/expiry on open sessions and revoke during generation | Real-clock browser checks and isolated SQL/API tests; no retry/fallback |
| Reused PASS — One-use/expired OTP, durable abuse limits, cross-invitation/Space isolation, snapshot immutability and stale graph | Reused merged Block 1/2 evidence and required native integration suite; no redundant local campaign |
| New backend/policy/architecture checks | 80 PASS; `test_sharing_pipeline.py test_architecture.py test_owner_policy.py` in dedicated SQL/Neo4j/mailbox project |
| Output privacy | 2 PASS, `tests/quality/test_browser_harness.py`; verifier key, fragment, OTP, email and OIDC output redaction |
| Build/types and source lint | Packaged browser build/TypeScript and Ruff PASS |
| Final Full Verification / review / merge | Recorded on the final candidate's GitHub run and PR; technical evidence alone is not merge or Jira closure |
| Persistent activation, external email, real guest inference | NOT TESTED / out of this mandate; no production routes, paid call or external email |

The complete local browser command is:

```sh
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh-demo3-api:candidate --browser-image qh-demo3-browser:candidate \
  --frontend-image qh-demo3-web:candidate --understanding --chat-sessions \
  --product-mode --uum-mode --sharing-mode --browser-grep 'Demo B:' \
  --output /tmp/qh40-final2-20261025
```

The harness uses self-signed localhost HTTPS, a temporary realm copy with an HTTPS
callback, and a pinned SMTP capture mailbox, all on its own network with no published
ports or persistent volumes. The original realm/configuration is not edited. QH-52
rotation and historical graph outage/restore browser profiles remain separate Full
CI gates, not claims made by this focused sharing profile. Images contain synthetic
fixtures only. Private execution records/screenshots are retained in
`.local-archive/qh40-20261025/` and are not runtime configuration.

## Prepared VPS activation — approval still required

A complete live SQL archive and globals backup were read without modifying data,
stored 0600 outside Git and restored into a private tmpfs PostgreSQL. All 15 public
table fingerprints matched the pre-task inventory. Upgrading that restored copy
from 0006 through unchanged 0007, 0008 and 0009 preserved every original table
except Alembic's expected version row and added nine empty tables. No upgrade or
restore ran on the VPS database. The archive SHA-256 is
`82b7f958f3c3b64f3a3dd48648c1e024424d07af829f5bef360c5d45c2fa13e2`;
private archive/verification: `pre-activation-0006.dump` and
`backup-verification.private.json` in the execution directory above.

Before any future activation:

1. Agree the transport/OIDC binding. Sharing requires an exact HTTPS browser origin;
   the existing development realm's HTTP callback is insufficient for the tested
   HTTPS owner flow. The test-only callback is not a VPS authorization. A persistent
   callback/ingress change or a different reviewed transport arrangement needs the
   owner's specific approval. Never deploy the test-only factory or self-signed
   test credentials as production configuration.
2. Select the reviewed code/artifact, stable private verifier key, explicit factory
   settings, same-origin cookie/proxy trust and local mailbox delivery configuration.
   Public endpoints and real third-party email remain excluded until authorized.
3. Stop only frontend/backend with guarded `dev-stop`; take a fresh complete backup
   and repeat isolated restoration if live state has changed. Present that backup,
   exact 0006→0009 target, selected bindings, downtime and rollback for approval.
4. Only after approval, apply the exact target using a separately reviewed operation,
   start the two apps with guarded commands, then check owner/guest access, no-link
   disclosure, masks, immutable payloads, expiry/revoke and preserved accounting.

Normal rollback disables the sharing bindings/flag and returns only the two apps
to the compatible source/artifact, retaining schema 0009 and immutable sharing
history/counters/revocations. It is not a destructive migration downgrade. If a full
database restore becomes necessary, keep sharing closed and invalidate restored
guest access before reopening so consumed codes/revoked sessions cannot revive;
preserve economic ledgers independently. Neo4j is rebuildable from canonical state;
no graph schema migration or infrastructure/Keycloak replacement is proposed here.
