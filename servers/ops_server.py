"""acme-ops MCP server: duty manager and rebooking tools."""

from mcp.server.fastmcp import FastMCP

from acme.tools import ops

mcp = FastMCP("acme-ops")


@mcp.tool()
def get_booking(pnr: str) -> dict:
    """Retrieve a booking by its six-character PNR (for example ACME01).
    Use first, before reasoning about any passenger case: passengers,
    segments, fare class, checked bags, loyalty id, pet in cabin, and
    whether the case is time-critical. Errors if the PNR does not exist;
    never invent booking data."""
    return ops.get_booking(pnr)


@mcp.tool()
def get_flight_status(flight_no: str) -> dict:
    """Current status of one flight (for example AC245): scheduled,
    landed, arrived or cancelled, and whether it is long-haul.
    Use for: flight status, cancellations, delays, is my flight on time."""
    return ops.get_flight_status(flight_no)


@mcp.tool()
def search_alternative_flights(origin: str, destination: str) -> list[dict]:
    """Alternative flights between two airport codes (for example FRA to
    HEL), earliest first, with seats available and any connection point.
    Use for: cancellations, missed connections, disruption, rebooking.
    Returns an empty list when there are no alternatives."""
    return ops.search_alternative_flights(origin, destination)


if __name__ == "__main__":
    mcp.run()
