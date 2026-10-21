
from mcp.server.fastmcp import FastMCP

from app.tools.investigation import investigate_incident
from app.tools.metrics import get_service_metrics
from app.rag.retriever import search_runbook

import os

mcp = FastMCP(
    "OpsPilot",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", os.getenv("MCP_PORT", "8000"))),
    streamable_http_path="/mcp",
)

@mcp.tool()
def investigate_service(service: str) -> dict:
    """Investigate an incident using service metrics, logs, deployments, and runbooks."""
    return investigate_incident(service)


@mcp.tool()
def get_metrics(service: str) -> dict:
    """Retrieve observability metrics for a service."""
    return get_service_metrics(service)


@mcp.tool()
def find_runbook_guidance(
    service: str,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """Search the service runbook for relevant troubleshooting guidance."""
    return search_runbook(service, query, top_k)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
