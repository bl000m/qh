# QH-54 — Understanding and direct-intake evidence

Actual Chromium screenshots use synthetic data in disposable PostgreSQL/Neo4j/
Keycloak projects. No live canonical test writes, paid inference, root `.env`,
published test ports or persistent demo seed. The underlying source, author,
acquisition timestamps, immutable revisions and policy checks are real application
behavior; provider extraction fixtures are explicitly synthetic, isolated adapters.

The [reference catalogue](reference-catalog.json) identifies the two supplied
1672 × 941 images by content, dimensions and SHA-256. Private originals remain in
the original incoming archive. Native-width side-by-side pairs (3344 × 981) and
hash manifests are retained under the protected task archive's comparison directory;
this preserves references without republishing the incoming private pack.

| View / observable outcome | Screenshot |
| --- | --- |
| Main list/detail, personal savings goal | [Desktop](understanding-list-desktop.png) / [Mobile](understanding-list-mobile.png) |
| Complementary overview, no invented categories or links | [Desktop](understanding-overview-desktop.png) / [Mobile](understanding-overview-mobile.png) |
| Single final persistence action, no self-checkbox | [Manual intake](manual-intake.png) |
| Discreet success with editor closed | [Saved feedback](saved-feedback.png) |
| Literal content retrieved after refresh and SSO | [Restored](restored-after-refresh.png) |
| Synthetic AI requires explicit human review | [Pending interpretation](ai-interpretation-pending.png) |
| Additional overview with actual stored relation/anchors | [Explicit relation](overview-explicit-relations.png) |

Actual dimensions, SHA-256 and capture composition/image identities are recorded in
[captures.json](captures.json). [Persistence receipt](persistence-evidence.json)
contains only whitelisted observed outcomes, without identifiers, source text or authentication. Full synthetic receipts remain private.
The savings goal stays canonical `proposed`; its UI label **Ajouté par vous**
expresses recorded personal origin, not confirmation or a truth certificate.
A correction creates a new human proposal. Synthetic AI remains **À vérifier**
until the real QH-46 review endpoint creates an immutable confirmed revision.

Visual review checked the original orb, white/gray surfaces, rounded card scale,
list/detail proportions, typography, secondary history and responsive navigation.
Differences from the illustrations are intentional: actual dates, provenance and
states; no financial types inferred from text; no fabricated counts or relation
nodes. The overview is simpler when stored relations are absent. Counts explicitly
refer to the loaded page, with additional-page controls. Advanced graph work belongs
to QH-51/QH-47. No visual pixel-identity or generated semantic-quality claim.

## Reproduce the targeted checks

```sh
sudo -n docker build -f apps/web/Dockerfile.browser -t qh54-browser:review .
sudo -n docker build -f apps/web/Dockerfile.dev -t qh54-web:review .
sudo -n docker run --rm --network none --entrypoint npm qh54-browser:review \
  --workspace @qh/web run lint
sudo -n docker run --rm --network none --entrypoint npm qh54-browser:review \
  --workspace @qh/web test -- --grep 'QH-54 origin|QH-54 groups'
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh53-api:review --browser-image qh54-browser:review \
  --frontend-image qh54-web:review --understanding --chat-sessions \
  --browser-grep 'context-understanding.browser|understanding.browser.spec|browse.browser.spec|chat.browser.spec|ux.browser.spec|v2.browser.spec|maquette.browser.spec|enrichment.browser.spec' \
  --focused-browser-only --output /tmp/new-empty-qh54-targeted-evidence
```

The existing backend image is reused because production backend code, requirements,
API contracts and migrations are unchanged. The current isolated preparation script
provides a dedicated synthetic interpretation Space to avoid mutating shared chat/
review fixtures. Normal product-mode checks additionally use `--product-mode` with
`QH-52 product|QH-53 complete|QH-53 consent|QH-54 direct|QH-54 synthetic|QH-54 manual`.
The hosted browser job includes those checks, actual graph outage, SQL restore and
Neo4j rebuild; focused local runs do not establish that complete acceptance gate.

During development, retained local failures exposed graph-publication timing in
rapid synthetic intake, a test that reopened retained Sources as if it were
Éléments, old test navigation behind a modal, incorrect CSS-zoom simulation and
an exact-label locator including the prefilled textarea value. Corrections use
bounded authorized GET readiness between separate writes, explicit navigation/
closing, an accessible textbox locator and a halved CSS viewport (836 × 470),
representing the layout available at 200% desktop zoom. No write retry, forced
click, backend safety relaxation or automatic AI confirmation was introduced.
The empty-workspace add action closes the workspace before opening its editor;
a separate failed/zero-item receipt test prevents false success.

The [criterion report](../../qh-54-context-understanding.md) distinguishes technical
acceptance from owner review, merge and Jira closure. Physical Mac/OS keyboard and
owner visual acceptance remain **NOT TESTED**. Exact final hosted CI result is
recorded on the unmerged delivery PR, bound to its final HEAD.

## Executed local results

| Check / retained private log | Observed result and limit |
| --- | --- |
| `origin-source-current.log` | PASS, 3 origin/ownership/literal-citation/descriptor guards |
| `lint-review.log` | PASS, application and test TypeScript |
| `product-fourth.log` | 6 PASS / 1 test-locator FAIL, plus 1 PASS real rotation/replay/revocation protocol check; all existing QH-52/QH-53 product checks passed |
| `regressions-final.log` | 28 PASS / 7 initial FAIL across 35 scoped browser checks; all 3 new QH-54 scenarios passed |
| `regressions-corrected.log` | PASS, all 7 affected cases; scoped legacy selectors, native modal timing and sufficient time for four Space visits / three real publication cycles |
| Capture audit | PASS, 9 PNG dimensions/SHA-256; running frontend source hash equals captured source hash (36 files) |
| Preservation | PASS, protected configuration/realm/authorization/ledger and original container identities/configuration; schema0006, canonical content unchanged; live opening metadata exception documented in the criterion report |

These are targeted development results, not a claim that a local complete CI suite
ran. The final hosted campaign is performed once after all local corrections and
publication, with its exact commit, jobs and verdict attached to the delivery PR.
No paid provider generation or physical Mac test is included.
