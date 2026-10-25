# QH-55 / QH-19 — governed disclosure and approved snapshots

Implementation boundary: internal application service, extending the merged
Projection Draft engine. No public guest route, provider call, startup migration
or persistent VPS activation. The next blocks supply invitation/session and UI.

`DisclosureService.prepare` takes an owned Space and `AccessPolicy`: invited email,
purpose, READ/ASK_AI, expiry, explicit bulk inclusion of proposals (default off),
optional quotations (default off) and optional additional exact exclusions. Only
the labelled offline test provider is supported for ASK_AI in this increment.

The PostgreSQL adapter selects metadata for current confirmed heads and latest
pending proposed revisions, bounded at 100 candidates. It refuses overflow rather
than sharing a partial page as complete. Policy, owner/Space and native readiness
precede selection. Exact selected pairs go through the existing Projection Engine;
only those revisions and minimal source identities are hydrated. Relations never
expand the selection to their endpoints. Rejected/superseded history is not selected.

## Explicit minimal Guard rules and limits

- Export only bounded statement text, original validation/origin states, valid UUM
  assignment metadata and local evidence references. Arbitrary properties, open
  descriptors, original source bodies/origins and owner identities are omitted.
- Mask recognisable email addresses, URLs, long numbers/phone-like strings and
  IBAN-like identifiers. Optional quotations use the same rules and must reference
  actual in-scope provenance. Redacted quotations are labelled, never called exact.
- Recognised high-risk fixture markers (medical diagnoses, credentials and related
  hazards) are excluded, including in quotations. There is no override for these
  exclusions in this first increment.
- **All remaining free text is still unassessed**, including names, locations,
  indirect identifiers, multilingual/obfuscated content and combinations of attributes.
  No heuristic says it is anonymous. A preview cannot be approved without a targeted
  owner decision on the named residual risk, bound to the exact minimized text,
  recipient and policy fingerprint. This decision covers the displayed batch;
  it does not require per-item selection or confirm any proposal.
- The preview shows inclusions, excluded revision/reason, masks and residual risk.
  Zero releasable items has an explicit outcome and cannot produce an empty snapshot.

These are conservative development rules, not a universal privacy classifier or
production-sensitive-data approval. The owner must evaluate remaining text for the
specific recipient. Future rules require a new preview/approval, not silent changes
to an existing snapshot.

## Approval, persistence and isolation

Previews expire for approval after 15 minutes, or sooner at policy expiry. Approval
rechecks owner policy, native exact-ID verification, draft version and canonical
selection/freshness. SQL locks serialize the final check with canonical publication;
context changes require a fresh preview. The approval records the exact named risk
decision; repeated identical approvals are idempotent, including concurrent requests.

Additive migration `0008_approved_disclosure`, after unchanged 0007, introduces
immutable previews, materialized approved snapshots and private exact revision
anchors. No original-source refetch is needed or permitted to construct a recipient
payload. Snapshot reads return a copy of the frozen safe representation; subsequent
Space changes/rebuilds cannot expand it. Recipient email and approval/policy metadata
are private owner-side governance, never an automatically public guest response.
Invitation access and revocation remain separate mutable governance in QH-20.

Tests use disposable PostgreSQL/Neo4j only. VPS schema remains 0006; activating
0007/0008 or exposing sharing routes needs the owner's separate operational gate.

## Executed candidate checks

All 54 new Guard/policy/SQL/native cases were executed successfully across the
focused run and its filtered continuations; 85 related Projection/policy/architecture
regressions passed. The final adapter-receipt correction has a separate 13-PASS
run (overlapping those counts). Ruff and `git diff --check` pass. The strict native
CI runner includes both new test modules; final hosted Full evidence belongs to
the candidate PR, not to a claim of VPS activation or guest-flow completion.

Two fixture failures were corrected without weakening protections: TRUNCATE must
include referencing test tables to reach the immutability trigger; changing the
canonical current pointer creates projection work that the fixture must drain.
Private command output and preservation inventories remain outside Git. Read-only
VPS comparisons show identical SQL table counts/hashes, schema 0006, private
configuration/realm and original container IDs/images/mounts. Only guarded app
stop/up was used for checkout alignment; other services were not restarted.
