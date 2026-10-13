# Backend adapters

The future GraphitiAdapter lives in this Python backend, not in a separate
container or TypeScript package. Graphiti is a Python library dependency of
this adapter. Its port and implementation are deferred to the relevant tickets.

Adapters will depend on QH Core contracts. Core must never import adapters,
FastAPI, Graphiti, MCP or LLM provider SDKs. No Graphiti dependency or dummy
adapter is installed by this scaffold.
