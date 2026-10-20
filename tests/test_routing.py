import json
from pathlib import Path

import pytest

from acme.routing import route_by_keywords

CASES = json.loads((Path(__file__).parent / "fixtures" / "routing_cases.json").read_text())


def test_routing_set_is_big_enough():
    assert len(CASES) >= 10


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_routes_to_an_accepted_desk(case):
    assert route_by_keywords(case["question"]) in case["accepted"]


def test_no_match_falls_back_to_duty_manager():
    assert route_by_keywords("hello") == "duty_manager"


def test_keywords_match_whole_word_starts():
    assert route_by_keywords("express train") == "duty_manager"
