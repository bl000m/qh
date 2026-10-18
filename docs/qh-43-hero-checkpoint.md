# QH-43 — central artwork, Space capsules and primary chat

Later owner-authorized runtime change: [actual VPS QH/French login and rollback](qh-43-keycloak-activation.md).
Earlier source-only/unchanged-IdP statements below describe their dated checkpoints.

2026-10-18. Owner-requested correction on the existing
[PR #15](https://github.com/bl000m/qh/pull/15), branch
`feat/QH-43-demo-a-ux-branding`, sole checkout `/home/ubuntu/qh`.
No merge/Jira DONE. The earlier [final-review checkpoint](qh-43-final-review.md)
remains dated evidence, superseded for current presentation by this iteration.

## Product decisions and rationale

The [Product Contract amendment](product/QH_PRODUCT_CONTRACT.md#qh-43-herocapsule-iteration--owner-correction-2026-10-18)
records the owner's new direction, alternatives and limits. This changes approved
presentation, not the original logo choice or architecture in ADRs 0003–0006.

| Surface | Actual change | Reason / boundary |
| --- | --- | --- |
| Welcome | Full useful width, centered original bubble (480px image box desktop, up to 340px mobile), large centered heading/action | Replace the narrow card and empty side space; retain logo in global header. No new image/creative variant |
| Mon environnement | Central artwork (400px desktop / up to 300px mobile) with centered heading | Stronger personal environment identity; artwork is noninteractive, proportional and decorative |
| Space overview | Centered heading above a rounded capsule with original bubble and one keyboard-operable opening link | Context-object metaphor only, no Domain/sharing controls, graph state or inferred semantic labels |
| Overview captions | First ten grapheme clusters + `…` only if longer | Complete emoji/combining sequences, full `aria-label`/tooltip/metadata, full detail title. Identical short labels still navigate distinct UUIDs |
| In-Space chat | Full-width prominent panel, larger heading/composer and question/answer bubbles; metadata moved below chat/explorer | Question and conversation dominate; no decorative hero competes with chat. Existing warning and consent text remains visible |
| Proposals excluded | Explain that content exists but is unconfirmed, and name the exact unchecked inclusion control | Shown before asking and with an insufficient result; no automatic opt-in or model-prose interpretation |
| No active understanding | Distinct empty-understanding and history-only messages | Existing bounded authorized history lookup, only after both active views are empty. Errors stay errors; sources alone are not claimed absent |

The complete canonical name is not renamed or persisted differently. The bubble
is the same original asset, not a newly generated representation of each Space.
All selected image bytes, icon and source-only Keycloak theme remain unchanged.
The original 400×300 bubble is proportionally sized in CSS; no image is cropped,
redrawn, recolored or newly published. Raster scaling remains a POC limit.

## Availability versus chat behavior

Current/proposed checks remain the existing authorized `browse` calls. Only when
both are empty does the client request `view=history&limit=1` through the same API,
policy and graph freshness path. The result changes the explanation, never the
chat payload. No history is sent to LLMProvider, and no fallback bypasses graph
validation. A failed history check leaves chat unavailable, not labelled empty.
Availability is an observed bounded opening snapshot, not a guarantee against
later concurrent changes; each chat request keeps its existing backend checks.

The explicit proposal checkbox is still unchecked on entry and resets dialogue
on changes. An unanswered question with no allowed support still follows the
existing backend contract; it now has a clear human explanation rather than only
“insufficient”. Other insufficient results explain the limits of the supplied
context, without asserting the requested information does not exist elsewhere.
A Space with no retained understanding revisions gets an honest empty state and
guidance to return to Mon environnement; no unimplemented ingestion action is shown.

## Verification and review gate

[Desktop/mobile captures, executed checks and integrity receipt](evidence/qh43-hero-20261018/README.md)
cover welcome, environment, Space list and chat. Public screenshots use isolated
synthetic fixtures, never the private live owner dashboard. Prior archives,
reference annotations and paid-call ledgers remain untouched.

Required regressions cover grapheme-safe captions, collision/navigation/accessibility,
proposal explanation and unchanged opt-in, no-revision versus history-only states,
fail-closed history errors, mobile/200%-text, primary composer, canonical warnings,
explorer, OIDC/Alice–Bob and restored canonical provenance. Hosted CI must pass
all four jobs on the latest HEAD before technical readiness is reported.

## Acceptance checkpoint

| Requested outcome | Classification / execution verdict |
| --- | --- |
| Broad immersive welcome, central large original bubble | Implemented and tested — PASS: desktop/mobile captures, centered geometry and useful width |
| Prominent central environment bubble | Implemented and tested — PASS: responsive captures and actual image dimensions |
| Space bubbles, centered titles, ten characters plus ellipsis | Implemented and tested — PASS: Unicode/grapheme controls, full accessible names/tooltips, exact UUID links and keyboard navigation |
| Clearly primary chat; secondary explorer/technical detail | Implemented and tested — PASS: visible composer, mobile bounds, keyboard explorer and retained canonical details |
| Explain excluded proposals, truly absent understanding and retained history | Implemented and tested — PASS: real isolated fixtures, explicit unchecked opt-in, insufficient response explanation, history failures stay unavailable |
| Preserve warnings, scope, identity, data and approved assets | Implemented and tested — PASS: existing real browser/OIDC and before/after integrity receipts; VPS realm/theme remains unchanged |
| Latest CI and owner acceptance | Exact-HEAD CI is checked on the PR; owner's new visual review remains pending. No merge/Jira DONE |

Previous layout: [welcome/environment/Space](evidence/qh43-branding-checkpoint-20261018/README.md).
Current layout and evidence are linked above. Technical test results do not approve
the new UX on the owner's behalf.

No backend/Core/API/policy/schema change, persistent write, provider call,
Keycloak activation, container/configuration replacement or other ticket.
Owner review of this new visual checkpoint remains pending; merge and Jira DONE
are not performed.
