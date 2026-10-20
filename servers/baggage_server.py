"""acme-baggage MCP server: bag tracing."""

from mcp.server.fastmcp import FastMCP

from acme.tools import baggage

mcp = FastMCP("acme-baggage")


@mcp.tool()
def trace_bag(file_reference: str) -> dict:
    """Trace a delayed, damaged or lost bag by its file reference (for
    example ARNAC10234): where the bag is, which flight it is forwarded on,
    and the delivery estimate. Use for: bag, baggage, luggage, suitcase,
    bag not arrived. Slow by design (legacy system, about 4.5 seconds)."""
    return baggage.trace_bag(file_reference)


if __name__ == "__main__":
    mcp.run()
