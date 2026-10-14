"""Manual, interactive real-provider smoke. Excluded from tests, startup and CI."""

import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4

from adapters.context.billing import approve_in_terminal
from adapters.context.factory import create_graphiti_engine
from app.core.models import ContextId, ContextQuery, SourceId, SourceRevisionId, SourceRevisionRef


async def main():
    if not sys.stdin.isatty():
        raise RuntimeError("Real smoke requires an interactive terminal and per-request approval")
    adapter, sdk = await create_graphiti_engine(approval=approve_in_terminal)
    marker = uuid4().hex
    space = ContextId("qh7-smoke-" + marker)
    other = ContextId("qh7-empty-" + marker)
    source = SourceRevisionRef(source_id=SourceId("qh7-source-" + marker),
                               revision_id=SourceRevisionId("qh7-revision-" + marker))
    try:
        await adapter.initialize()
        await adapter.ingest_source(context_id=space, source=source,
            text="Ada founded Cedar Observatory in Lyon. Cedar Observatory studies comets.",
            reference_time=datetime.now(timezone.utc))
        result = await adapter.search(ContextQuery(text="Who founded the observatory?", context_ids=(space,)))
        assert result.hits and any(source in hit.provenance for hit in result.hits)
        isolated = await adapter.search(ContextQuery(text="Who founded the observatory?", context_ids=(other,)))
        assert not isolated.hits
        print("PASS: real semantic retrieval, source provenance and separate space scope")
    finally:
        await adapter.close()
        await sdk.close()
        print("Synthetic graph scope retained:", space, "(no data deleted)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        # Library/provider errors may contain request content: no traceback here.
        print("Smoke stopped or failed; no automatic retry", file=sys.stderr)
        sys.exit(1)
