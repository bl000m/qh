---
name: jira-ticket-workflow
description: Analyze, implement or verify a QH Jira ticket using the Product Contract, approved ADRs, Atlassian MCP and Docker evidence. Use for ticket-scoped work; escalate unresolved domain decisions and never update Jira automatically.
---

# Jira ticket workflow

1. Read the ticket, dependencies and acceptance criteria through Atlassian MCP,
   including relevant comments/links. Resolve the accessible site before using
   its cloud ID. Record the URL and exact Done criteria.
2. Read `AGENTS.md` and relevant sections of the mandatory
   [Product Contract](../../../docs/product/QH_PRODUCT_CONTRACT.md). Do not infer
   domain meaning solely from table names, code or incomplete Jira descriptions.
3. Consult relevant approved ADRs in `docs/adr` and `docs/architecture.md`.
   Distinguish approved principles, V0.1 choices, open hypotheses and future work.
   ADR 0003 supersedes the Graphiti runtime choice; read the current QH-30
   deployment register and post-cutover record before treating old ticket
   category names as mandatory registered types. The single development checkout
   is `/home/ubuntu/qh` on one task branch. The owner's 2026-10-17 VPS POC decision
   enables frontend/backend source mounts and hot reload; MCP remains image-only.
   Read `docs/qh-development-stack.md`; stop frontend/backend via guarded `dev-stop`
   before any branch switch. Preserve readonly IdP configuration and private .env.
4. Develop only in `/home/ubuntu/qh`, following its Single Checkout Development
   Policy: one active branch/ticket/PR, previous task closed unless explicitly
   excepted, clean/saved files and safe processes/mounts, then fast-forward `main`
   before creating/selecting the task branch. The legacy worktree bootstrap is
   disabled. Preserve PR #5/#7 worktrees as paused transition exceptions; never
   bypass an attached-branch refusal or change runtime implicitly.
   Identify the delta against previous verification reports under AGENTS.md;
   inspect only relevant code, Git/baseline and Docker availability, with preflight
   proportional to risk. Repeat completed work only if changes invalidate it,
   regressions emerge or evidence is insufficient. Identify missing decisions,
   contradictions and architectural/privacy risks before defining the scope.
   Follow AGENTS.md's baseline/versioning policy; do not infer Done from files
   or ticket status.
5. Apply **STOP AND ASK** under AGENTS.md whenever its triggers apply. Present
   the missing decision, feasible alternatives, consequences, benefits/risks and
   a reasoned recommendation; wait for explicit approval for the affected part.
   Distinguish structural decisions from implementation details under AGENTS.md:
   unapproved domain/canonical data/authorization/architecture/public contract
   changes need approval; module layout, SQL/index details, tests and reversible
   refactoring within approved contracts are autonomous. Do not reopen approved
   decisions unless a concrete contradiction, new risk or technical constraint
   emerges; explain that specific issue. Continue independent, already-defined
   work without anticipating unresolved choices. QH-4's approved scope is in
   [ADR 0002](../../../docs/adr/0002-canonical-understanding-persistence.md).
6. Implement only after blocking decisions are resolved and the ticket work is
   authorized. Keep scope bounded, preserve approved dependencies and use Docker
   for execution, dependency installation and tests with committed lockfiles.
   Respect analysis-only or documentation-only requests. If Docker is blocked,
   report the cause; do not install global Mac packages or silently substitute
   host execution for container validation.
7. Split useful logical units and create incremental, verified local commits
   referencing the Jira key under AGENTS.md. Run pertinent checks before each
   commit and stage only its files/hunks. Use targeted checks during development
   and full verification at integration or when justified; follow its reasoning
   guidance. Preserve suspended and user-owned work.
8. Compare executed checks with every Done criterion: PASS (executed/satisfied),
   FAIL (executed/failed or definitely missing), NOT TESTED (not executed).
   Record commands and evidence; distinguish static, build, runtime, protocol and
   persistence results. Classify each criterion as implemented/tested,
   implemented/unverified, not implemented or out of scope. Never claim an
   unexecuted test passed or a tested draft model was approved. Correct safe
   in-scope technical failures autonomously with relevant regressions; report
   out-of-scope issues with priority and proposed solutions instead of adding scope.
   Use IN PROGRESS while implementing, READY FOR REVIEW for verified technical
   criteria and a published unmerged PR, and DONE only after every Jira acceptance
   criterion is verified, reviewed merge is confirmed and Jira is updated with
   explicit authorization. Never start the next task automatically.
9. Summarize modifications, repeatable commands, residual decisions/blockers and
   each local commit's hash, message, purpose and checks. Prepare a Jira-ready
   summary if useful, but do not post it automatically. No remote push, force
   push, destructive reset or Jira write without the authorization AGENTS.md
   requires; never automatically change Jira status.

Keep credentials out of logs, tracked files and build contexts. Preserve data
volumes. Final delivery must make the ticket's Done verdict and its limits clear.
