import json
from pathlib import Path

import pytest

from acme.gate import HANDOFF_MESSAGE, MAX_ATTEMPTS, gate_answer
from acme.protocol import check_protocol
from acme.scoring import review_answer

CASES = json.loads((Path(__file__).parent / "fixtures" / "reviewer_cases.json").read_text())
BY_ID = {case["id"]: case for case in CASES}


def gate(case_id, **kwargs):
    case = BY_ID[case_id]
    return gate_answer(case["answer"], case["pnr"], **kwargs)


def test_good_answer_is_delivered_unchanged():
    result = gate("good-acme01")
    assert result["decision"] == "deliver"
    assert result["deliver_text"] == BY_ID["good-acme01"]["answer"]


def test_soft_failures_never_block():
    result = gate("trap-vocabulary")
    assert result["decision"] == "deliver"
    assert result["review"]["soft_failures"] == ["offered_options"]


def test_hard_failure_first_attempt_retries():
    result = gate("bad-promise", attempt=1)
    assert result["decision"] == "retry"
    assert result["deliver_text"] is None


def test_hard_failure_last_attempt_hands_off():
    result = gate("bad-promise", attempt=MAX_ATTEMPTS)
    assert result["decision"] == "handoff"
    assert result["deliver_text"] == HANDOFF_MESSAGE


def test_handoff_message_is_safe():
    assert check_protocol(HANDOFF_MESSAGE)["passed"] is True
    assert review_answer(HANDOFF_MESSAGE, "ACME02")["hard_failures"] == []


def test_attempt_below_one_raises():
    with pytest.raises(ValueError):
        gate("good-acme01", attempt=0)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_gate_review_matches_review_answer(case):
    result = gate_answer(case["answer"], case["pnr"])
    assert result["review"] == review_answer(case["answer"], case["pnr"], True)
