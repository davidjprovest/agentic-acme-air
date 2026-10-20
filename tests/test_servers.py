import asyncio

import pytest

from servers import baggage_server, fares_server, loyalty_server, ops_server, review_server

EXPECTED_TOOLS = {
    ops_server: {"get_booking", "get_flight_status", "search_alternative_flights"},
    baggage_server: {"trace_bag"},
    loyalty_server: {"get_loyalty_account"},
    fares_server: {"check_fare_rule", "list_fare_classes"},
    review_server: {"score_service_review"},
}


def tool_names(server):
    return {tool.name for tool in asyncio.run(server.mcp.list_tools())}


@pytest.mark.parametrize("server", EXPECTED_TOOLS, ids=lambda s: s.__name__.split(".")[-1])
def test_server_exposes_exactly_its_tools(server):
    assert tool_names(server) == EXPECTED_TOOLS[server]


def test_eight_tools_across_five_servers():
    all_names = set().union(*(tool_names(server) for server in EXPECTED_TOOLS))
    assert len(EXPECTED_TOOLS) == 5
    assert len(all_names) == 8


def test_every_tool_has_a_description():
    for server in EXPECTED_TOOLS:
        for tool in asyncio.run(server.mcp.list_tools()):
            assert tool.description and len(tool.description) > 40, tool.name


def test_call_through_server_returns_tool_data():
    result = asyncio.run(ops_server.mcp.call_tool("get_flight_status", {"flight_no": "AC245"}))
    assert "CANCELLED" in str(result)


def test_planted_fare_failure_crosses_the_server():
    with pytest.raises(Exception) as excinfo:
        asyncio.run(fares_server.mcp.call_tool("check_fare_rule", {"fare_class": "Z"}))
    assert "Z" in str(excinfo.value)
    assert "list_fare_classes" in str(excinfo.value)
