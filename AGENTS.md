# AGENTS

QH is a modular, sovereign context platform. Read `docs/architecture.md` before
changing module boundaries.

## Architecture and dependency direction

- `apps/web`: React + TypeScript + Vite. TypeScript is strict and extends the
  root configuration. The browser communicates with public API contracts.
- `apps/api`: Python + FastAPI. FastAPI is an inbound adapter, not QH Core.
- `services/mcp-server`: independent Python adapter using the official `mcp`
  SDK. It must not import backend implementation files or access databases.
- Future QH Core is Python, independent of FastAPI, Graphiti, MCP and LLM SDKs.
  Inbound adapters and outbound adapter implementations depend on Core ports;
  Core never imports them. Assemble dependencies at the application boundary.
- Graphiti is a Python library integrated through a replaceable adapter inside
  the backend. Never create a Graphiti microservice or TypeScript adapter.
- `packages/shared`: public wire schemas/types, not Python domain interfaces.
- `infra/docker`: exactly five Compose services: frontend, backend, mcp,
  neo4j and postgres. Keep infrastructure separate from application code.
- Document new module responsibilities and adapter contracts. Do not implement
  business logic before module boundaries and contracts are established.

## Ticket workflow

- Read the Jira ticket, acceptance criteria and dependencies through Atlassian
  MCP before implementation. If unavailable, report the blocker; do not invent
  ticket requirements.
- Inspect the repository and scope changes to the requested ticket. Use
  `.agents/skills/jira-ticket-workflow/SKILL.md` for ticket-based work.
- Verify the Definition of Done with actual execution evidence. Report each
  criterion as PASS, FAIL or NOT TESTED, with commands and observed results.
- Never claim tests passed if they were not executed. Distinguish static review
  from build, runtime, protocol and persistence checks.
- Never automatically change Jira status. Any Jira write requires explicit
  user authorization; status changes require user approval.

## Docker-first development

- Prefer Docker Compose for running services, installing dependencies and tests.
  The host only needs Docker with Compose v2; Python 3 is optional for generating
  a local `.env`. Use the root Makefile and README commands.
- Do not install runtimes or packages globally on macOS without authorization.
  If Docker is unavailable, identify the executable/daemon/permission blocker
  and mark affected checks NOT TESTED. Do not replace container tests with
  claims based on source inspection.
- Install Node dependencies with `npm ci` in the frontend image. Install Python
  dependencies from hash-locked `requirements.lock` files in their images.
  Commit manifests and regenerated lockfiles together; rebuild after changes.
- Use bind mounts for source hot reload; do not mount host dependency directories.
- Keep database ports unpublished and database containers on the internal data
  network. Application ports bind to loopback for this local POC.
- Keep credentials in ignored `.env` files and configuration keys in
  `.env.example`. Never commit secrets or include them in image build contexts.
- Do not delete database volumes or reset local data without explicit approval.
