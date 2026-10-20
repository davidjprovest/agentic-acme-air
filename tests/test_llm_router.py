import json
import os
import time
from pathlib import Path

import pytest

from acme.llm_router import VALID_DESKS, build_system_prompt, parse_desk, route_with_llm
from acme.routing import ESCALATION_TABLE, route_by_keywords

FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((FIXTURES / "routing_cases.json").read_text())
PARAPHRASES = json.loads((FIXTURES / "routing_paraphrase_cases.json").read_text())


# Offline: no model needed, always run.

def test_prompt_names_every_desk_and_keyword():
    prompt = build_system_prompt()
    for desk, keywords in ESCALATION_TABLE:
        assert desk in prompt
        for keyword in keywords:
            assert keyword in prompt
    assert "duty_manager" in prompt


def test_parse_valid_desk():
    assert parse_desk('{"desk": "baggage"}') == "baggage"


def test_parse_tolerates_case_and_spaces():
    assert parse_desk('{"desk": " Baggage "}') == "baggage"


def test_parse_finds_json_inside_fences_and_chatter():
    assert parse_desk('Sure!\n```json\n{"desk": "fares"}\n```') == "fares"


def test_parse_unknown_desk_is_invalid_not_guessed():
    assert parse_desk('{"desk": "lost_property"}') == "invalid"


def test_parse_junk_is_invalid():
    assert parse_desk("I think baggage") == "invalid"


def test_valid_desks_match_the_table():
    assert VALID_DESKS == {desk for desk, _ in ESCALATION_TABLE} | {"duty_manager"}


def test_keyword_router_misses_every_paraphrase():
    # Recorded limitation, like the reviewer's matching trap: passengers who
    # avoid the exact keywords fall through to duty_manager. If this starts
    # failing, someone added keywords; re-measure both routers.
    hits = [c["id"] for c in PARAPHRASES if route_by_keywords(c["question"]) in c["accepted"]]
    assert hits == []


# Live: calls local Ollama. Run with ACME_LLM=1.

def compare(cases, label):
    llm_hits = keyword_hits = 0
    started = time.perf_counter()
    print(f"\n{label}")
    for case in cases:
        llm_desk = route_with_llm(case["question"])
        keyword_desk = route_by_keywords(case["question"])
        llm_hits += llm_desk in case["accepted"]
        keyword_hits += keyword_desk in case["accepted"]
        marker = "ok " if llm_desk in case["accepted"] else "MISS"
        print(f"{marker} {case['id']:<26} llm={llm_desk:<20} keyword={keyword_desk:<20} accepted={case['accepted']}")
    elapsed = time.perf_counter() - started
    total = len(cases)
    print(f"LLM {llm_hits}/{total}   keyword {keyword_hits}/{total}   ({elapsed / total:.1f}s per LLM question, n={total})")
    return llm_hits / total


@pytest.mark.llm
@pytest.mark.skipif(os.environ.get("ACME_LLM") != "1", reason="set ACME_LLM=1 to call Ollama")
def test_llm_router_against_keyword_baseline():
    assert compare(CASES, "Keyword-friendly cases") >= 0.6
    assert compare(PARAPHRASES, "Paraphrase cases") >= 0.6
