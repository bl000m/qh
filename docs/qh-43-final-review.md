# QH-43 — final technical review

Later owner correction: [central artwork, capsules and primary chat](qh-43-hero-checkpoint.md).
Earlier screenshots/readiness below are dated checkpoints, not acceptance of this iteration.

2026-10-18. [PR #15](https://github.com/bl000m/qh/pull/15), branch
`feat/QH-43-demo-a-ux-branding`, sole checkout `/home/ubuntu/qh`.
The owner accepts the branding direction and requests final verification, with no
additional variants or redesign. This record supplements the immutable
[selected-identity checkpoint](qh-43-branding-checkpoint.md) and earlier UX evidence.
No merge, Jira transition or persistent Keycloak activation is authorized here.

## Delta and evidence

Client/theme executable sources and all selected graphic assets are unchanged from
`6305b5ba291ab3bb283f2b8d6e703c8961973835`. The only test changes enable French in
**the disposable realm copy** and request browser locale `fr-FR`, then assert inherited French labels/language, real
Code+PKCE completion and original logo/bubble proportions. No source change to
`infra/keycloak/qh-realm.json`, authentication, API, Core, provider or database.

The temporary preview changes exactly `loginTheme`, `internationalizationEnabled`,
`supportedLocales` and `defaultLocale`; original clients, credentials/placeholders,
issuer, redirect and PKCE configuration remain intact. Neither this test nor the
source theme changes the VPS realm. Previous English preview captures remain
unchanged historical evidence.

[French login captures and executed receipts](evidence/qh43-final-review-20261018/README.md)
complement the earlier complete 48-case browser run, four-job green hosted CI on
`6305b5b`, and live Alice/Bob evidence; unchanged results are reused rather than
presented as new executions.

## Acceptance mapping against the actual Jira ticket

The ticket was read through Atlassian MCP on 2026-10-18, including its acceptance
criteria and dependency list; no comments or linked issues were present. Its Jira
status remains **À faire**, an administrative discrepancy recorded without an
unauthorized write. QH-13 is already merged/closed; ticket wording about the old
PR #14 dependency is historical, not a new blocker.

| Jira criterion | Classification / result | Evidence and limit |
| --- | --- | --- |
| Real login/reload → Mon environnement; token/logout/isolation regressions | Implemented and tested — PASS | Existing full browser/OIDC checks and live Alice/Bob checkpoint; final French test and latest hosted CI supplement them |
| Owned Spaces only, no invented Domain/sharing API | Implemented and tested — PASS | Three retained synthetic Spaces, six Bob 404s, native policy checks; no backend or schema delta |
| Primary chat; explicit proposals; ephemeral dialogue reset; labelled mock; no Understanding publication | Implemented and tested — PASS | Existing browser chat/reset/consent/warning and canonical preservation checks; no new model behavior claimed |
| Accessible expandable understanding with complete canonical details/history | Implemented and tested — PASS | Existing keyboard/focus, browse, source and exact-anchor/history regressions |
| Selected original graphics, traceability, desktop/mobile readability | Implemented and tested — PASS | Unchanged asset manifest, same frontend/theme bytes, whole-mark icon; dimension/proportion and 320px/200% text checks. Owner authorization covers this product preview/integration, not a general artwork licence |
| Coherent inherited login, unchanged OIDC; isolated browser verification | Implemented and tested — PASS | Actual French Keycloak 26.4.7 preview and successful Code+PKCE; upstream form/templates/scripts remain inherited |
| TypeScript/lint/build and relevant browser/OIDC regressions | Implemented and tested — PASS | Commands/receipts in the final evidence archive; all four latest PR checks must be green before hand-off |
| Owner final PR review, authorized merge and Jira closure | Not completed — pending owner decision | PR preparation is READY FOR REVIEW, not DONE; no merge or Jira write |

## Residual limits: blockers versus future work

**Technical blockers:** none if the final required CI jobs remain green. Owner
review/merge authorization and Jira closure remain required workflow gates, not
technical defects. Jira's stale À faire state is disclosed; it is not silently
changed by this verification.

**Accepted POC limits:** ephemeral token/dialogue session, explicit proposal opt-in,
mandatory canonical-state warnings and bounded non-ranked retrieval remain as in
QH-13. Mock is extractive and does not understand questions. Valid canonical
references do not prove semantic support; no new paid-model quality claim follows.
The approved raster mark is faithfully cropped from the owner's presentation;
there is no fabricated SVG. A future original vector master could improve scaling,
but is not required to reopen the closed selection. Small favicons necessarily
lose fine detail through downsampling; the entire mark remains present.

**Prepared, not activated:** Keycloak theme sources and isolated French rendering.
VPS activation requires separate explicit permission; no production-theme result
is claimed. Accessibility checks cover keyboard, focus, tested contrast and
320px/enlarged-text reflow, not a comprehensive WCAG certification.

**Future capabilities, excluded from QH-43:** Domains, sharing/projections,
interactive editing/human confirmation, advanced graph navigation, generated
synthesis, conversational ingestion (QH-39), selective external Context Delta
(QH-44), persistent chat and public Mistral sessions. None is started here.

## Preservation and hand-off

Read-only before/after checks cover all fourteen canonical tables, all six runtime
container identities/configurations/start times, private `.env`, readonly realm
import, both closed Mistral ledgers and all seven original branding references.
Detailed owner/database inventories remain private; public evidence contains only
verification receipts and synthetic screenshots. Existing ports and hot reload
remain unchanged. No import, database write, provider call, migration, deployment,
realm change or container restart is part of this final verification.

The next action is the owner's final review of PR #15 and a separate decision on
merge/Jira closure. No other ticket starts automatically.
