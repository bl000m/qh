---
name: jira-ticket-workflow
description: Implement or verify a QH Jira ticket with relevant product context and risk-proportionate evidence. Never update Jira automatically.
---

# Jira ticket workflow — MVP Fast Track

Follow the current [AGENTS.md](../../../AGENTS.md); do not duplicate its safety,
checkout, architecture, test or reporting rules here.

1. Read the ticket, acceptance criteria, dependencies and pertinent comments through
   Atlassian MCP. If unavailable, report it; never invent ticket requirements.
   For owner-requested non-ticket maintenance, use the approved mandate without
   creating a ticket. Read only relevant Product Contract/ADR/code sections.
2. Inspect the active checkout/PR and prior evidence. Identify the smallest change
   and classify its actual risk A/B/C; resolve only genuinely missing decisions.
3. Implement incrementally through existing code/services. Apply DRY/KISS/YAGNI/SRP
   in the touched code, without unrelated refactors or new architectural paperwork.
4. Run the checks appropriate to the risk and changed behavior. Reuse unchanged
   passing evidence; distinguish executed, reused, failed and not-run checks.
5. Review the diff/exclusions, commit coherent verified work and publish the task PR
   when authorized. Use PR Fast during draft development and Full for the final
   candidate or earlier when risk requires it; no paid API calls in tests/CI.
6. Report the outcome, evidence, material limitations and Git/PR state briefly.
   Acceptance criteria remain binding; publication is not merge or product acceptance.
   No automatic Jira write/status change, new ticket or merge.
