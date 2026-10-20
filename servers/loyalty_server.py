"""acme-loyalty MCP server: loyalty accounts."""

from mcp.server.fastmcp import FastMCP

from acme.tools import loyalty

mcp = FastMCP("acme-loyalty")


@mcp.tool()
def get_loyalty_account(loyalty_id: str) -> dict:
    """Loyalty account by id (for example LY3003): tier, points balance
    and the points cost of a long-haul upgrade. Use for: points, tier
    status, gold, upgrades. Errors if the account does not exist."""
    return loyalty.get_loyalty_account(loyalty_id)


if __name__ == "__main__":
    mcp.run()
