"""One review function: the single scoring path for the graph and the evals.

It only calls extract_facts, score_service_review and check_protocol. It never
re-implements a weight, keyword or threshold. Hard failures are what the live
gate blocks on; soft failures (wording facts) are recorded but never block, so
the matching trap cannot stop a correct answer.
"""

from acme.protocol import check_protocol
from acme.rubric import extract_facts
from acme.tools.review import score_service_review

HARD_FAILURES = (
    "promised_compensation_without_confirmation",
    "missing_disclaimer",
    "missing_ai_disclosure",
)


def review_answer(answer: str, pnr: str, first_turn: bool = True) -> dict:
    """The single scoring path used both in the graph and by the evals.

    Returns facts, score, protocol, hard_failures (in HARD_FAILURES order)
    and soft_failures (score failed_facts minus "no_unconfirmed_promise").
    """
    facts = extract_facts(answer, pnr)
    score = score_service_review(**facts)
    protocol = check_protocol(answer, first_turn)

    applies = {
        "promised_compensation_without_confirmation": facts[
            "promised_compensation_without_confirmation"
        ],
        "missing_disclaimer": not protocol["has_disclaimer"],
        "missing_ai_disclosure": not protocol["disclosed_ai"],
    }
    return {
        "facts": facts,
        "score": score,
        "protocol": protocol,
        "hard_failures": [name for name in HARD_FAILURES if applies[name]],
        "soft_failures": [f for f in score["failed_facts"] if f != "no_unconfirmed_promise"],
    }
