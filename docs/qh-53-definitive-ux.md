# QH-53 — Approved product maquettes

Owner mandate2026-10-20, independent branch from main797b274; PR19 remains open
and unchanged18bac2c. This explicitly authorized UX increment follows QH52's
verified activation; its Mac acceptance/Jira closure remains separate.

## Scope and component contracts

All15 supplied PNGs were inspected by content. The six newest1672×941 references
show empty Discussion, Éléments, Modèle, Conseils, context settings and global
settings. Earlier home/domain/brand/login references preserve the existing brand;
projection/sharing controls and illustrative portrait/medical content are not
implemented features. The supplied PDF is historical narrative, not a feature gate.

The only tab order is Discussion → Éléments → Modèle → Conseils → Paramètres.
Header, breadcrumb and original QH orb are shared. Normalize model cards against
other tabs rather than copying their disproportionate scale. Keep conversation,
unsent text and provider consent in memory across tab switches; changing Space,
logout, invalid authorization or explicit new discussion retain existing cleanup.

React owns presentation only. Existing QhApi/PolicyService/native retrieval,
QH39 persistence and QH46 review contracts stay fixed; no migration, API, service,
paid inference, provider allowlist/budget or IdP/session change.

- Discussion: original orb, two empty-state actions and composer in document flow.
  Ajouter un élément opens the existing literal canonical intake for arbitrary
  user-authored content. Explorer focuses a normal editable question; unavailable
  provider gives a short explanation. No fabricated first assistant answer.
- Sending without a valid grant opens the existing exact-content authorization in
  an accessible modal. Fetching the preview is internal and never paid generation.
  Proposed inclusion remains affirmative, separate from external-disclosure consent.
  Actual provider generation needs a subsequent explicit Send; never auto-replay a
  pending message on consent. Snapshot/context changes still invalidate grants.
- Modèle: actual capability model/budget; no fake selector when only one model.
  Accounting/availability/revoke remain in an accessible secondary disclosure.
- Éléments: Sources, Compréhension and Détails; browse without asking a question,
  full provenance/history/review controls retained in their existing components.
- Mémoriser cette conversation appears only with selectable turns; preserves exactly
  the selected segment, source and unconfirmed proposals. Never claim whole-history
  persistence or semantic extraction. No duplicate disabled enrichment button.
- Conseils: three editable question starters, no automatic generation/recommendation.
  They return to Discussion and focus the draft; the owner explicitly sends it.
- Settings: owner name/description/domain endpoints reused with CAS and individual
  error acknowledgement. Global profile/account use authenticated information;
  French/light presentation are read-only facts, not invented preference controls.
  Unsupported deletion, notifications, language/theme switches remain absent.

## Verification and delivery

Targeted checks during implementation; actual browser on isolated native stack,
simulated provider HTTP only. Compare each screen side by side with the supplied
reference at1672×941; desktop/mobile/200%/keyboard and full empty/populated workflows.
One final hosted CI campaign after local integration readiness. Explicit PASS/FAIL/
NOT TESTED evidence and visual limitations before READY FOR REVIEW. No automatic
merge, Jira status transition or PR19 resolution. Screenshots must use synthetic
isolated data; no changes to the three persistent demo Spaces or ledgers.
