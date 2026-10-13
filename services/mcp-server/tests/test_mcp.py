import asyncio
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def test_health() -> None:
    base_url = os.environ.get("MCP_TEST_URL", "http://127.0.0.1:3001")
    response = httpx.get(f"{base_url}/health", timeout=10)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "qh-mcp-server"}


def test_client_can_invoke_tool() -> None:
    async def exchange() -> None:
        base_url = os.environ.get("MCP_TEST_URL", "http://127.0.0.1:3001")
        async with streamablehttp_client(f"{base_url}/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "QH scaffold"
                tools = await session.list_tools()
                assert "scaffold_ping" in {tool.name for tool in tools.tools}
                result = await session.call_tool("scaffold_ping", {"message": "smoke"})
                assert not result.isError
                assert any(getattr(block, "text", None) == "qh: smoke" for block in result.content)

    asyncio.run(asyncio.wait_for(exchange(), timeout=20))
