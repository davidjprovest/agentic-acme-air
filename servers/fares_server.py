"""acme-fares MCP server: fare rules and fare classes."""

from mcp.server.fastmcp import FastMCP

from acme.tools import fares

mcp = FastMCP("acme-fares")


@mcp.tool()
def check_fare_rule(fare_class: str) -> dict:
    """Fare rules for one fare class (for example B): change fee in EUR,
    whether it is refundable, and the pet-in-cabin fee. Use for: fare
    rules, change fees, date changes, refundability, pets in cabin.
    Errors if the class is not in the fare table; then call
    list_fare_classes and report the missing class, never invent a rule."""
    return fares.check_fare_rule(fare_class)


@mcp.tool()
def list_fare_classes() -> list[str]:
    """List every valid fare class code. Use when a fare class is unknown,
    rejected by check_fare_rule, or the passenger asks which classes exist."""
    return fares.list_fare_classes()


if __name__ == "__main__":
    mcp.run()
