---
name: jira-ticket-workflow
description: Implement or verify a QH Jira ticket using Atlassian MCP, Docker-first development and evidence against its acceptance criteria. Use for ticket-scoped repository work; never update Jira automatically.
---

# Jira ticket workflow

1. Read the requested ticket through Atlassian MCP, including description,
   acceptance criteria, status, links and relevant comments. Resolve the
   accessible site before using its cloud ID. Record the ticket URL and exact
   Done criteria; ask for missing requirements only if they block the work.
2. Read repository `AGENTS.md` and `docs/architecture.md`. Inspect files and
   ticket dependencies; verify actual implementation and Docker availability.
   Verify Git/baseline and follow AGENTS.md's versioning policy; a missing
   baseline needs a reviewed proposal and approval before the first commit.
   Do not infer completion from ticket status or the presence of files.
3. Define the changes needed for this ticket. Preserve the user's architecture
   decisions and leave unrelated/future tickets unimplemented. Identify
   independent commit units when appropriate, without forcing a fixed number.
4. Implement incrementally and run relevant checks through Docker Compose.
   Install dependencies only in containers using committed lockfiles. Use the
   README/Makefile commands. Run targeted checks before each coherent local
   commit, review/stage only its files or hunks, and reference the Jira key.
   Ticket implementation authorization permits local commits under AGENTS.md;
   do not defer all commits to ticket completion. Run full checks at integration
   or when justified, not after every small edit. Apply its reasoning guidance.
   If Docker is blocked, record the precise cause and continue independent
   work; do not install global Mac runtimes/packages or silently substitute
   host execution for container validation.
5. Produce a checklist for every acceptance criterion: PASS (executed and
   satisfied), FAIL (executed and failed, or a definite missing requirement),
   or NOT TESTED (not executed). Include command, observed result and evidence.
   A static check is evidence only for a static requirement. Never treat an
   unexecuted build, health check or MCP exchange as passing.
6. Summarize changed files, repeatable commands, residual work and blockers,
   plus each local commit's hash, message, purpose and executed checks.
   Prepare a Jira-ready summary if useful, but do not post it or change Jira
   automatically. No remote push, force push, destructive reset or Jira write
   without the explicit authorization required by AGENTS.md.

Keep credentials out of logs, tracked files and build contexts. Preserve data
volumes. Final delivery must make the ticket's Done verdict and its limits clear.
