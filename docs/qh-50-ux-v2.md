# QH-50 — UX V2 implementation record

2026-10-19. One owner-authorized initiative in three increments, one branch/PR
and one final complete campaign. QH-45 merged in `393a91daac9281d7f8918f5b6819f33d6ea91aba`
and Jira is DONE. No new inference is part of this work.

[ADR 0008](adr/0008-personal-organization-and-owner-review.md) records the explicitly
approved metadata and review contracts. QH-43 supplies the visual baseline;
QH-46 review is bounded by that approval; QH-47/48 advanced engines remain future.

## Verification plan

Increment 1: focused frontend contracts, typecheck/build and new browser assertions
for manual scroll, source-panel focus and compact session management.
Increment 2: immediate isolated SQL/API ownership, persistence and concurrency
checks for organization; no automatic demo memberships.
Increment 3: immediate isolated canonical review, replay, race, provenance,
current pointer and outbox tests. No persistent demo review writes.
At integration: one full native/SQL/graph/browser/OIDC/outage/restore campaign,
then repeat only failed or affected checks. Results will be recorded when executed.

Implementation is IN PROGRESS. No merge or Jira closure is authorized.

Increment 1 focused execution: Docker `npm run build:web` and `npm run typecheck`
PASS; two human-provenance/descriptor tests PASS. Browser interaction assertions
and the full campaign remain pending; these checks do not establish final readiness.
