"""LLM routing experiment: ask a local model which desk owns a question.

Measured against the keyword baseline in acme.routing on the same
routing cases. Uses the Ollama HTTP API through the standard library, so
there are no extra dependencies. The model never answers the passenger:
it only names a desk, and anything that is not a known desk is reported
as "invalid" rather than guessed.
"""

import json
import urllib.request

from acme.routing import ESCALATION_TABLE, FALLBACK_DESK

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3.5:9b"
VALID_DESKS = {desk for desk, _ in ESCALATION_TABLE} | {FALLBACK_DESK}

DESK_TRIGGERS = {
    "customer_relations": "compensation, complaints, legal threats, refunds",
    "fares": "fare rules, change fees, fare classes, date changes, pets in cabin",
    "loyalty": "points, tier status, upgrades",
    "baggage": "delayed, damaged or lost bags",
    "rebooking": "cancellations, missed connections, disruption",
}


def build_system_prompt() -> str:
    lines = [
        "You route Acme Air passenger questions to the desk that owns them.",
        "Desks, checked in this order (the first that fits wins):",
    ]
    for desk, keywords in ESCALATION_TABLE:
        lines.append(f"- {desk}: {DESK_TRIGGERS[desk]}. Keywords: {', '.join(keywords)}.")
    lines.append(f"- {FALLBACK_DESK}: anything that fits no desk above, such as a greeting.")
    lines.append("Do not answer the question.")
    lines.append(f'Reply only with JSON: {{"desk": "<one of: {", ".join(sorted(VALID_DESKS))}>"}}')
    return "\n".join(lines)


def parse_desk(content: str) -> str:
    try:
        desk = str(json.loads(content).get("desk", "")).strip().lower()
    except (json.JSONDecodeError, AttributeError):
        return "invalid"
    return desk if desk in VALID_DESKS else "invalid"


def route_with_llm(question: str, model: str = DEFAULT_MODEL, timeout: float = 120) -> str:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": question},
        ],
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.load(response)
    return parse_desk(body["message"]["content"])
