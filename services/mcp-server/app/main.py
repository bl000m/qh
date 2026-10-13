from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    "QH scaffold",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["localhost:*", "127.0.0.1:*", "mcp:*"],
        allowed_origins=["http://localhost:*", "http://127.0.0.1:*"],
    ),
)


@mcp.tool()
def scaffold_ping(message: str = "ping") -> str:
    """Echo a message to verify MCP transport; no application behavior."""
    return f"qh: {message}"


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "qh-mcp-server"})


app = mcp.streamable_http_app()
