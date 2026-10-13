# Initial commit prepared — approval pending

Proposed message: `chore: bootstrap Docker-first QH monorepo`

The Git index contains the working QH-1 scaffold and five-service QH-3 Compose
base as they stood before QH-2 implementation. No commit has been created.
QH-2 changes stay in the working tree until the initial commit is approved.

## Preliminary checks (2026-10-13)

- Initialized this directory with `git init -b main` after confirming no Git repo.
- Expanded Git/build exclusions for credentials, private keys, local databases,
  dependency directories and temporary/test output. `.env.example` stays tracked.
- `git check-ignore` confirmed exclusions for `.env`, nested local env files,
  credentials, DB storage, dependencies and temporary files.
- Inspected all 42 pre-existing candidate files for local password values and
  private key material without printing secrets; no matches were found.
- Baseline `make verify` passed: three application image builds, five healthy
  services, frontend production build/type checks and eight automated tests.
- QH-3 runtime checks passed: internal data network, no database host port
  bindings, and both DB containers attached only to `qh_data`.
- No runtime was installed globally, no Docker resources were cleaned up, and
  no Jira issue was modified. Data persistence across restart remains untested.

## Review and approval

```bash
git diff --cached --stat
git diff --cached
git status --short
```

The initial commit requires the user's approval. Do not use `git add .` before
creating it: that would mix the subsequent QH-2 work into the staged baseline.
After approval, commit the existing index with the proposed message; then review
QH-2 separately. A later change to this preparation must be explicitly reviewed.
