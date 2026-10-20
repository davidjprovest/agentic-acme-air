import json
from pathlib import Path

import pytest

from acme.protocol import check_protocol
from acme.rubric import extract_facts
from acme.scoring import HARD_FAILURES, review_answer
from acme.tools.review import score_service_review

CASES = json.loads((Path(__file__).parent / "fixtures" / "reviewer_cases.json").read_text())
BY_ID = {case["id"]: case for case in CASES}


def review(case_id, **kwargs):
    case = BY_ID[case_id]
    return review_answer(case["answer"], case["pnr"], **kwargs)


def test_good_answer_has_no_failures():
    result = review("good-acme01")
    assert result["hard_failures"] == []
    assert result["soft_failures"] == []


def test_bad_promise_has_all_hard_failures_in_order():
    assert review("bad-promise")["hard_failures"] == list(HARD_FAILURES)


def test_trap_is_a_soft_failure_only():
    result = review("trap-vocabulary")
    assert result["hard_failures"] == []
    assert result["soft_failures"] == ["offered_options"]
    assert result["score"]["passed"] is False


def test_no_booking_answer_is_missing_disclaimer_and_booking():
    result = review("fail-no-booking")
    assert "missing_disclaimer" in result["hard_failures"]
    assert "used_booking" in result["soft_failures"]


def test_later_turn_needs_no_ai_disclosure():
    result = review_answer("Booking ACME02, your bag is in Paris.", "ACME02", first_turn=False)
    assert "missing_ai_disclosure" not in result["hard_failures"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_review_uses_the_one_scoring_path(case):
    result = review_answer(case["answer"], case["pnr"])
    facts = extract_facts(case["answer"], case["pnr"])
    assert result["facts"] == facts
    assert result["score"] == score_service_review(**facts)
    assert result["protocol"] == check_protocol(case["answer"])
