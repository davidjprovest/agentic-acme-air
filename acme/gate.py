"""The in-graph gate: a code check between a drafted answer and the passenger.

Why code and not the service_reviewer agent: an instruction to "call the
reviewer last" relies on the model obeying it, which is the same weakness as
the planted flaw in agents/duty_manager.toml. Code runs every time.

The gate calls review_answer, the one scoring path shared with the evals. It
blocks only on hard failures; soft failures (wording) never block.
"""

from acme.data import DISCLAIMER
from acme.scoring import review_answer

MAX_ATTEMPTS = 2

HANDOFF_MESSAGE = (
    "You are talking to an AI assistant, and I could not prepare a safe answer "
    "for you. A member of the Acme Air team will take over your case. "
    "The next step is that they contact you directly about your booking. "
    + DISCLAIMER
)


def gate_answer(answer: str, pnr: str, first_turn: bool = True, attempt: int = 1) -> dict:
    """Decide whether a drafted answer may reach the passenger.

    deliver: no hard failures; deliver_text is the answer, unchanged.
    retry:   hard failures and attempt < MAX_ATTEMPTS; deliver_text is None.
    handoff: hard failures and attempt >= MAX_ATTEMPTS; deliver_text is
             HANDOFF_MESSAGE.
    """
    if attempt < 1:
        raise ValueError("attempt must be 1 or more")
    review = review_answer(answer, pnr, first_turn)
    if not review["hard_failures"]:
        decision, deliver_text = "deliver", answer
    elif attempt < MAX_ATTEMPTS:
        decision, deliver_text = "retry", None
    else:
        decision, deliver_text = "handoff", HANDOFF_MESSAGE
    return {"decision": decision, "deliver_text": deliver_text, "review": review}
