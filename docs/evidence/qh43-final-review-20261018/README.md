# QH-43 — final French login and review evidence

2026-10-18. [Final acceptance mapping and residual limits](../../qh-43-final-review.md).
This supplements, without modifying, the sealed
[original branded checkpoint](../qh43-branding-checkpoint-20261018/README.md).
No additional branding variants or application features are introduced.

## Actual isolated French rendering

| Surface | Desktop | Mobile |
| --- | --- | --- |
| Keycloak 26.4.7, inherited QH theme, French | [1280px](screenshots/keycloak-fr-desktop.png) | [390px](screenshots/keycloak-fr-mobile.png) |
| Same unchanged approved welcome assets | [1280px](screenshots/welcome-desktop.png) | [390px](screenshots/welcome-mobile.png) |

These are Chromium captures of the actual disposable realm, not a mock login,
private owner dashboard or evidence of theme activation on the VPS. Captures occur
before entering generated test credentials. No new graphic assets are created.
Existing environment/Space captures remain in the earlier archive.

French is enabled **only in a temporary public-fixture copy** with theme `qh`,
supported locales `fr/en` and default `fr`. The French test requests `fr-FR` in
Chromium: browser language takes precedence over the realm default. It asserts
`html lang=fr`, the inherited heading “Connectez-vous à votre compte”, password
label “Mot de passe”, button “Connexion”, selected logo background with `contain`,
320px/200%-text reflow and successful real Code+PKCE → Mon environnement.

## Executed checks and their limits

| Executed final check | Observed result |
| --- | --- |
| Targeted Chromium asset/French login checks | 2 passed, zero skips, 15.3 s |
| Existing real OIDC/owner regression | 1 passed, 1 deselected, 13.34 s |
| Real graph outage | 3 passed, 7.3 s |
| Disposable SQL restore/native rebuild | All canonical tables equal |
| Restored-ID browser | 1 passed, 17.6 s |
| Build/TypeScript, Ruff, immutable asset/previous archives | PASS |
| Fresh VPS read-only preservation | PASS; six runtime containers healthy |

The [results receipt](results.json) records image identities and harness outcomes.
The targeted run selects the two changed checks: approved mark/bubble dimensions,
proportions/favicon load, and French inherited login. The harness still executes
its existing real OIDC/owner regression, graph outage and SQL restore/native graph
rebuild/browser gates. TypeScript/build run before browser tests. These overlap
prior coverage and must not be summed as a larger suite.

Two preliminary attempts are retained privately: the first correctly revealed the
browser's English preference; the next reached French but exposed a new test's
incorrect input-value assertion on Keycloak's button. The final assertion checks
its accessible button name. No application/template fix or skipped assertion was
used to turn these diagnostics green.

Unchanged selected graphics are checked against the original asset manifest:
logo 876×768; original bubble proportionally downsampled to 400×300; whole-mark
64×64 favicon PNG; exact PNG inside the theme ICO; frontend/theme copies identical.
The originals/derivatives remain unchanged, with no new crop, vector reconstruction,
rotation, alternate logo or redistribution of the deck/mockups. Visual inspection
of actual desktop/mobile captures complements dimension/proportion checks.

Fresh read-only before/after inventory verifies all fourteen QH tables, six runtime
container identities/configurations/start times, private configuration, readonly
realm import, two closed Mistral ledgers and seven original reference files.
Inventories remain private. The public receipt reports equality only. No provider
request, canonical write, deployment, persistent realm change or runtime restart.

Reproduce with the existing Docker-only harness, a fresh directory, and candidate
images built from the reviewed tree:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:final-french \
  --understanding --qh-login-theme \
  --browser-grep 'source-only QH login theme|selected original mark' \
  --output /tmp/qh43-final-french-fresh
python3 docs/evidence/qh43-final-review-20261018/audit.py
```

The complete hosted browser job uses **no filter**; quality, native-integration and
unthemed OIDC jobs remain required. Check the PR's exact HEAD and all four jobs for
final readiness; a prior green commit is not proof for a later commit. PR review,
merge, Jira closure and VPS theme activation remain separate owner decisions.
