import json
from pathlib import Path

import pytest

from acme.rubric import extract_facts
from acme.tools.review import score_service_review

CASES = json.loads((Path(__file__).parent / "fixtures" / "reviewer_cases.json").read_text())
BY_ID = {case["id"]: case for case in CASES}
FACT_NAMES = {
    "used_booking",
    "offered_options",
    "flagged_time_critical",
    "cited_next_step",
    "promised_compensation_without_confirmation",
}


def review(case_id):
    case = BY_ID[case_id]
    return score_service_review(**extract_facts(case["answer"], case["pnr"]))


def test_fixture_set_is_big_enough_both_ways():
    assert len(CASES) >= 10
    assert sum(c["expected_pass"] for c in CASES) >= 5
    assert sum(not c["expected_pass"] for c in CASES) >= 5


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case_scores_as_expected(case):
    result = review(case["id"])
    assert result["passed"] == case["expected_pass"], result["message"]


def test_bad_promise_is_hard_fail():
    result = review("bad-promise")
    assert result["score"] == 0.0
    assert result["message"].startswith("FAIL:")


def test_good_answer_scores_full_marks():
    result = review("good-acme01")
    assert result["score"] == 1.0
    assert result["message"] == "PASS"


def test_trap_fails_only_on_vocabulary():
    result = review("trap-vocabulary")
    assert result["failed_facts"] == ["offered_options"]


def test_same_answer_same_score():
    assert review("good-acme01") == review("good-acme01") == review("good-acme01")


def test_reviewer_extracts_facts_but_never_scores():
    case = BY_ID["good-acme01"]
    facts = extract_facts(case["answer"], case["pnr"])
    assert set(facts) == FACT_NAMES
    assert "score" not in facts


def test_not_time_critical_needs_no_urgency_words():
    facts = extract_facts("Booking ACME02, your bag is in Paris.", "ACME02")
    assert facts["flagged_time_critical"] is True
