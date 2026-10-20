"""Protocol checks: spec rules 6 and 7, beside the five-fact rubric.

Deterministic and literal, like acme/rubric.py. Kept separate because the
rubric has exactly five facts. Rule 6 (AI disclosure) is a legal requirement
(EU AI Act Article 50), so it gets its own named check.
"""

from acme.data import DISCLAIMER

AI_DISCLOSURES = ("ai assistant", "virtual assistant", "talking to an ai", "chatting with an ai")


def check_protocol(answer: str, first_turn: bool = True) -> dict:
    """Spec rules 6 and 7, checked literally and case-insensitively.

    disclosed_ai: on the first turn the answer contains one of AI_DISCLOSURES;
    True on later turns.
    has_disclaimer: acme.data.DISCLAIMER appears verbatim (case-sensitive).
    passed: both True.
    """
    lowered = answer.lower()
    disclosed_ai = (not first_turn) or any(phrase in lowered for phrase in AI_DISCLOSURES)
    has_disclaimer = DISCLAIMER in answer
    return {
        "disclosed_ai": disclosed_ai,
        "has_disclaimer": has_disclaimer,
        "passed": disclosed_ai and has_disclaimer,
    }
