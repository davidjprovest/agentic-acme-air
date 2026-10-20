import json
import os
import time
from pathlib import Path

import pytest

from acme.llm_router import VALID_DESKS, build_system_prompt, parse_desk, route_with_llm
from acme.routing import ESCALATION_TABLE, route_by_keywords

CASES = json.loads((Path(__file__).parent / "fixtures" / "routing_cases.json").read_text())


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


def test_parse_unknown_desk_is_invalid_not_guessed():
    assert parse_desk('{"desk": "lost_property"}') == "invalid"


def test_parse_junk_is_invalid():
    assert parse_desk("I think baggage") == "invalid"


def test_valid_desks_match_the_table():
    assert VALID_DESKS == {desk for desk, _ in ESCALATION_TABLE} | {"duty_manager"}


# Live: calls local Ollama. Run with ACME_LLM=1.

@pytest.mark.llm
@pytest.mark.skipif(os.environ.get("ACME_LLM") != "1", reason="set ACME_LLM=1 to call Ollama")
def test_llm_router_against_keyword_baseline():
    llm_hits = keyword_hits = 0
    started = time.perf_counter()
    for case in CASES:
        llm_desk = route_with_llm(case["question"])
        keyword_desk = route_by_keywords(case["question"])
        llm_hits += llm_desk in case["accepted"]
        keyword_hits += keyword_desk in case["accepted"]
        marker = "ok " if llm_desk in case["accepted"] else "MISS"
        print(f"{marker} {case['id']:<24} llm={llm_desk:<20} keyword={keyword_desk:<20} accepted={case['accepted']}")
    elapsed = time.perf_counter() - started
    total = len(CASES)
    print(f"\nLLM accuracy:     {llm_hits}/{total}")
    print(f"keyword accuracy: {keyword_hits}/{total}")
    print(f"LLM time: {elapsed:.1f}s total, {elapsed / total:.1f}s per question")
    assert llm_hits / total >= 0.6
