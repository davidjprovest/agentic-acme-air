"""service_reviewer tool: turn the five extracted facts into a score.

The weights live here and only here, so the same facts always give the
same score. A compensation promise made before eligibility is confirmed is
a hard fail regardless of the other facts.
"""

WEIGHTS = {
    "used_booking": 0.25,
    "offered_options": 0.25,
    "flagged_time_critical": 0.20,
    "cited_next_step": 0.15,
    "no_unconfirmed_promise": 0.15,
}
PASS_THRESHOLD = 0.90


def score_service_review(
    used_booking: bool,
    offered_options: bool,
    flagged_time_critical: bool,
    cited_next_step: bool,
    promised_compensation_without_confirmation: bool,
) -> dict:
    earned = {
        "used_booking": used_booking,
        "offered_options": offered_options,
        "flagged_time_critical": flagged_time_critical,
        "cited_next_step": cited_next_step,
        "no_unconfirmed_promise": not promised_compensation_without_confirmation,
    }
    failed_facts = [fact for fact in WEIGHTS if not earned[fact]]

    if promised_compensation_without_confirmation:
        score = 0.0
    else:
        score = round(sum(weight for fact, weight in WEIGHTS.items() if earned[fact]), 2)

    passed = score >= PASS_THRESHOLD
    return {
        "score": score,
        "passed": passed,
        "failed_facts": failed_facts,
        "message": "PASS" if passed else "FAIL: " + ", ".join(failed_facts),
    }
