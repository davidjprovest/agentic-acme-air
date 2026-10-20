"""Escalation table and keyword routing baseline.

The table maps topics to the owning desk. Order matters: the first desk
with a matching keyword wins, so customer_relations is checked first
(complaints often mention cancellations too). This deterministic router is
the baseline an LLM router is measured against.
"""

import re

ESCALATION_TABLE = [
    ("customer_relations", ["compensation", "complaint", "refund", "lawyer", "legal", "press", "enforcement"]),
    ("fares", ["fare", "fee", "date change", "pet"]),
    ("loyalty", ["points", "tier", "gold", "upgrade"]),
    ("baggage", ["bag", "luggage", "suitcase"]),
    ("rebooking", ["cancel", "missed connection", "rebook", "disrupt"]),
]

FALLBACK_DESK = "duty_manager"


def route_by_keywords(question: str) -> str:
    # Leading word boundary only: "bag" matches "bags", "press" skips "express".
    for desk, keywords in ESCALATION_TABLE:
        for keyword in keywords:
            if re.search(r"\b" + re.escape(keyword), question, re.IGNORECASE):
                return desk
    return FALLBACK_DESK
