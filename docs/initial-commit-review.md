# Initial baseline commit — approved and created

Commit: `e91a01b` — `chore(QH-1): consolidate Docker-first QH scaffold`

The user reviewed and committed the prepared QH-1/QH-3 baseline. It contains
43 files and excludes subsequent QH-2 changes. No baseline approval is pending.
The preceding preparation used tree `d057c643508855803058d152c7bd393008a3cf71`.

## Checks performed before preparation

- Git initialized on main; exclusions cover local env files, credentials,
  database storage, dependencies and temporary output. .env.example is tracked.
- Candidate files checked for local password values/private keys without
  printing sensitive content. .env was excluded from the index.
- Baseline make verify passed: all five containers healthy, frontend build and
  type checks, and eight automated tests.
- Actual DB network configuration checked: internal qh_data network, no host
  port bindings and both databases attached only to qh_data.

QH-6 commit `3abeeca` subsequently added the permanent incremental local commit
policy. QH-2 follows that policy; see [its verification](verification-qh-2.md).
Review history with git log and individual changes with git show. No push,
force push, destructive reset or Jira update was performed by these tasks.
