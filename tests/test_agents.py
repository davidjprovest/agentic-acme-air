import asyncio
from pathlib import Path

import pytest

from acme.agents import REQUIRED_KEYS, load_agents
from acme.routing import ESCALATION_TABLE
from servers import baggage_server, fares_server, loyalty_server, ops_server, review_server

ROOT = Path(__file__).resolve().parent.parent
SERVERS = {s.mcp.name: s for s in (ops_server, baggage_server, loyalty_server, fares_server, review_server)}
DESKS = ["rebooking", "baggage", "loyalty", "fares", "customer_relations"]
EXPECTED_AGENTS = {"duty_manager", "service_reviewer", *DESKS}
EXPECTED_TOOLS = {
    "duty_manager": ["acme-ops/get_booking", "acme-ops/get_flight_status"],
    "rebooking": ["acme-ops/search_alternative_flights"],
    "baggage": ["acme-baggage/trace_bag"],
    "loyalty": ["acme-loyalty/get_loyalty_account"],
    "fares": ["acme-fares/check_fare_rule", "acme-fares/list_fare_classes"],
    "customer_relations": [],
    "service_reviewer": ["acme-review/score_service_review"],
}
PLANTED_SENTENCE = (
    "If you can answer the question yourself with your own tools, answer it directly instead of delegating."
)


@pytest.fixture(scope="module")
def agents():
    return load_agents()


def server_tools(server):
    return {tool.name for tool in asyncio.run(server.mcp.list_tools())}


def all_agent_tools(agents):
    return [entry for agent in agents.values() for entry in agent["tools"]]


def test_exactly_seven_agents(agents):
    assert set(agents) == EXPECTED_AGENTS
    assert len(agents) == 7


def test_every_agent_has_required_keys(agents):
    for name, agent in agents.items():
        assert REQUIRED_KEYS <= set(agent), name


def test_every_tool_exists_on_its_server(agents):
    for entry in all_agent_tools(agents):
        server_name, tool = entry.split("/")
        assert server_name in SERVERS, entry
        assert tool in server_tools(SERVERS[server_name]), entry


def test_every_tool_is_owned_exactly_once(agents):
    owned = all_agent_tools(agents)
    every_tool = {f"{name}/{tool}" for name, server in SERVERS.items() for tool in server_tools(server)}
    assert len(owned) == 8
    assert len(set(owned)) == 8
    assert set(owned) == every_tool


def test_ownership_matches_the_table(agents):
    for name, tools in EXPECTED_TOOLS.items():
        assert sorted(agents[name]["tools"]) == sorted(tools), name


def test_every_delegate_is_a_known_agent(agents):
    for name, agent in agents.items():
        for delegate in agent["delegates"]:
            assert delegate in agents, f"{name} -> {delegate}"


def test_duty_manager_delegates_to_exactly_the_five_desks(agents):
    assert sorted(agents["duty_manager"]["delegates"]) == sorted(DESKS)


def test_customer_relations_has_no_tools(agents):
    assert agents["customer_relations"]["tools"] == []


@pytest.mark.parametrize("desk,keywords", ESCALATION_TABLE, ids=[d for d, _ in ESCALATION_TABLE])
def test_description_is_a_routing_trigger(agents, desk, keywords):
    description = agents[desk]["description"].lower()
    found = [k for k in keywords if k.lower() in description]
    assert len(found) >= min(3, len(keywords)), f"{desk} description mentions only {found}"


def test_every_named_skill_exists(agents):
    for name, agent in agents.items():
        for skill in agent["skills"]:
            assert (ROOT / "skills" / skill / "SKILL.md").is_file(), f"{name}: {skill}"


def test_planted_flaw_sentence_is_present(agents):
    """Guards a planted lab flaw: participants find and remove this sentence in the lab.
    It must stay in the repo, so do not "fix" it and do not delete this test."""
    assert PLANTED_SENTENCE in agents["duty_manager"]["system_message"]


def test_fares_message_covers_missing_fare_class(agents):
    message = agents["fares"]["system_message"]
    assert "list_fare_classes" in message
    assert "invent" in message


def test_load_agents_rejects_missing_key(tmp_path):
    (tmp_path / "broken.toml").write_text('name = "broken"\n')
    with pytest.raises(ValueError, match="broken.toml"):
        load_agents(tmp_path)


def test_load_agents_rejects_name_not_matching_file_stem(tmp_path):
    body = 'name = "other"\ndescription = "d"\nskills = []\ntools = []\ndelegates = []\nsystem_message = "m"\n'
    (tmp_path / "mismatch.toml").write_text(body)
    with pytest.raises(ValueError, match="mismatch.toml"):
        load_agents(tmp_path)
