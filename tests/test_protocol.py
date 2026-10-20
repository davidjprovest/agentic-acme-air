import json
from pathlib import Path

import pytest

from acme.data import DISCLAIMER
from acme.protocol import check_protocol

CASES = json.loads((Path(__file__).parent / "fixtures" / "reviewer_cases.json").read_text())
BY_ID = {case["id"]: case for case in CASES}


def test_good_case_passes_both_checks():
    result = check_protocol(BY_ID["good-acme01"]["answer"])
    assert result == {"disclosed_ai": True, "has_disclaimer": True, "passed": True}


def test_bad_promise_fails_both_checks():
    result = check_protocol(BY_ID["bad-promise"]["answer"])
    assert result["disclosed_ai"] is False
    assert result["has_disclaimer"] is False
    assert result["passed"] is False


def test_fail_no_booking_lacks_disclaimer():
    assert check_protocol(BY_ID["fail-no-booking"]["answer"])["has_disclaimer"] is False


def test_later_turn_needs_no_disclosure():
    result = check_protocol("Your gate is B12. " + DISCLAIMER, first_turn=False)
    assert result["disclosed_ai"] is True
    assert result["passed"] is True


def test_disclosure_match_ignores_case():
    assert check_protocol("I am an AI ASSISTANT. " + DISCLAIMER)["disclosed_ai"] is True


def test_disclaimer_with_altered_capitals_fails():
    answer = "I am an AI assistant. " + DISCLAIMER.upper()
    assert check_protocol(answer)["has_disclaimer"] is False


@pytest.mark.parametrize(
    "case", [c for c in CASES if c["expected_pass"]], ids=lambda c: c["id"]
)
def test_every_good_case_passes_protocol(case):
    assert check_protocol(case["answer"])["passed"] is True
