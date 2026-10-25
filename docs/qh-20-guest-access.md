# QH-20 — verified-mailbox snapshot invitations

Demo B Block 2 follows merged [PR #26](https://github.com/bl000m/qh/pull/26),
`cfd7c0e`. It reuses the immutable materialized snapshot and its already approved
recipient, rights and expiry. It does not create a QH user, Space membership or
write permission. Mailbox control is not civil identity.

## Boundaries and ordinary flow

- `app/projections/guest_service.py` owns invitation, explicit code request,
  verification, session, frozen snapshot read and revocation. Source retrieval,
  semantic extraction and provider calls are absent.
- `PostgresGuestRepository` owns durable attempt/send counters, atomic one-use
  consumption, session/invitation binding and minimal audit timestamps.
- The existing central `PolicyService` handles distinct READ_SNAPSHOT/ASK_SNAPSHOT
  actions from fresh verified-session facts. Owner OIDC remains mandatory for
  invitation creation/list/revocation; guest proofs cannot authorize Space access.
- `SecureGuestProofs` generates 256-bit URL-safe tokens and eight-digit random
  codes. Domain-separated token hashes are stored; OTP verifiers use HMAC-SHA256
  with a private injected key of at least 32 bytes, not a brute-forceable plain
  code hash. No raw code/token/email in application logs.
- `SandboxSMTPMailer` connects only to the local capture mailbox. It has no
  external SMTP provider, relay, delivery retry or startup send.

The owner receives the invitation token once, only after OIDC/owner checks. The
UI must put it in the invitation URL **fragment**, not path/query/logs. The guest
posts token and email as bounded JSON. Unknown link, wrong email, cooldown, send
limit and delivery failure return the same generic receipt and opaque challenge
shape. No context, private preview or email is returned before verification.

Only a correct, delivered and unused code creates a short-lived guest session.
The response carries a Secure/HttpOnly/SameSite=Strict `__Host-qh_guest` cookie,
Path=/ and no Domain; the token is never returned in guest JSON. The mailbox
verification label is explicit. Each read rechecks owner/Space activity, invitation,
session, expiry, revocation, exact snapshot and READ/ASK_AI through central policy.
Only the stored safe snapshot payload can be hydrated, after those checks and
under locks; original Sources, canonical IDs and live graph retrieval are absent.
Logout revokes that session; owner invitation revocation invalidates all its
existing sessions. Snapshot/history is not rewritten.

## Technical limits

| Control | Limit |
| --- | --- |
| Code validity | 5 minutes, bounded by invitation expiry |
| Code failures | 5 per challenge; 10 cumulative per invitation, not reset by resend |
| Delivery | 60-second cooldown; at most 3 sends per invitation; explicit requests only |
| Peer throttling | Durable 60-second windows: 10 code requests / 30 verification requests |
| Session | At most 30 minutes, bounded by approved invitation expiry |
| Approval policy | Recipient/rights/expiry copied from immutable approved snapshot; no guest-selected provider or mutation |
| Owner listing | Up to 100 invitations with explicit `has_more`, no fabricated global count |

Peer identifiers are keyed hashes of the actual request peer, never supplied email
or an untrusted forwarded header. Wrong-code counters commit before denial; a failed
authentication cannot roll them back. Delivery failures cannot produce valid codes
and do not retry. Resend invalidates older unused challenges. Database triggers
prevent rebinding/extension, counter reset, undoing consumption/revocation and silent
deletion of invitation/session history. Only expired ephemeral rate state is pruned.

## Transport and activation boundary

`create_app` mounts the invitation/guest routes **only** with an explicitly injected
guest service, existing owner security bindings and an exact HTTPS browser origin.
Production bootstrap supplies none of these guest bindings: no guest routes become
available on the VPS. Mutations require matching Origin, JSON and bounded input;
validation errors never echo submitted proofs or addresses. All responses are
no-store. The response-time floor reduces simple enumeration timing differences;
it does not promise perfect network timing indistinguishability.

Additive migration `0009_guest_invitations` follows unchanged 0007/0008. Four tables
store invitations, challenges, sessions and ephemeral rate limits. No new canonical
account or Keycloak configuration is introduced. All migrations remain isolated-only;
the persistent VPS stays at 0006. UI/browser QH-18/21/22 and QH-40 acceptance belong
to the next block after this PR is integrated.

## Real sandbox, not a client-injected code

The disposable SQL/native test project includes
[Mailpit v1.21.8](https://github.com/axllent/mailpit/releases/tag/v1.21.8), pinned by
image digest, quiet, with tmpfs storage and no host ports or configured relay.
Tests send through SMTP, then read the delivered message through its
[mailbox API](https://mailpit.axllent.org/docs/api-v1/), and submit that code through
the real QH handler. No email goes to external addresses. The disposable project
and its mailbox are removed after the targeted checks. This proves SMTP/OTP/API
delivery and authentication; it does not certify the later complete browser UX.

## Executed checks and pending activation

Focused QH-20, central owner policy and architecture run: **105 PASS**. Additional
resend/concurrency/ASK-only/transport cases: **6 PASS**; final payload-scope checks:
**13 PASS**. These runs overlap; do not sum them. Ruff, shared DTO TypeScript and
Git whitespace checks pass. No manual rerun of the Block 1 tests was performed.
The mandatory final hosted Full run and merge result are recorded on the PR.
The dependency's existing Starlette/AnyIO deprecation warning is non-blocking;
no package upgrade or unrelated change is part of this increment.

Read-only VPS inventories before/after match for every public SQL table hash/count,
private configuration/realm and original container ID/image/mount. Schema is still
0006 and the real API OpenAPI has no guest/invitation routes. Only guarded app
stop/up was used for checkout alignment; infrastructure was not restarted.

Future VPS activation requires a separate approved operation: fresh complete SQL
backup and isolated restore verification, exact 0006→0007→0008→0009 application plan,
reviewed guest bindings/HTTPS origin, private stable verifier key and local capture
mailbox. App-only rollback disables those bindings and preserves immutable history,
consumption counters and revocations. A database restore must not resurrect consumed
codes or revoked invitations/sessions; restored guest access must be invalidated
before reopening. No downgrade, backup restore or persistent activation is executed
or authorized by this candidate.
