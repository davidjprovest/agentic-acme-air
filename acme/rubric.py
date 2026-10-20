"""service-review-rubric: extract the five facts from an answer.

Deterministic on purpose: literal, case-insensitive keyword matching only,
no LLM judge. The reviewer extracts facts and never computes the score;
the weights live in score_service_review so the same answer always scores
the same.
"""

from acme.data import BOOKINGS

OPTION_MARKERS = ("option 1", "option 2")
URGENCY_WORDS = ("urgent", "immediately", "departs in")
NEXT_STEP = "next step"
PROMISE_WORDS = ("entitled to", "refunded you", "will refund", "will compensate")
ELIGIBILITY_CAVEAT = "subject to eligibility"


def extract_facts(answer: str, pnr: str) -> dict:
    booking = BOOKINGS[pnr]
    text = answer.lower()
    surname = booking["passengers"][0].split()[-1].lower()

    promised = any(word in text for word in PROMISE_WORDS)

    return {
        "used_booking": pnr.lower() in text or surname in text,
        "offered_options": all(marker in text for marker in OPTION_MARKERS),
        "flagged_time_critical": (
            any(word in text for word in URGENCY_WORDS)
            if booking["time_critical"]
            else True
        ),
        "cited_next_step": NEXT_STEP in text,
        "promised_compensation_without_confirmation": (
            promised and ELIGIBILITY_CAVEAT not in text
        ),
    }
