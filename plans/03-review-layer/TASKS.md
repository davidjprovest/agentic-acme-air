# Chunk 03: the review layer, one scorer and two callers

**Time box:** 60 minutes total: about 40 for building and about 20 for the supervisor's review.
**Builds on:** chunk 02 (`skills/`, `agents/`, `acme/agents.py`, `acme/protocol.py`, 124 tests).
**Spec reference:** `Acme Air multi-agent lab open source specification.md`, section 0.3 (DeepEval and in-graph reviewer) and the Part 2 learning points (in-graph observer, matching trap).
**Decision this implements:** `plans/02-agent-layer/REPORT.md`, question 1.

## Goal

Answers are reviewed in two places, and both must use **the same scoring path**:

1. **In the graph (live):** a deterministic code gate checks every answer before the passenger sees it. It blocks only on hard rules, retries once, then hands off to a human.
2. **After the fact (evals):** a harness runs the same scorer over a set of answers and writes a self-contained report.

The scoring path already exists: `acme.rubric.extract_facts`, then `acme.tools.review.score_service_review`, plus `acme.protocol.check_protocol`. This chunk wraps it once and calls that wrapper from both places. Nothing here calls a model, installs software or touches Langfuse, DeepEval or kagent.

## Ground rules for every task

- Standard library only on top of what is installed.
- Do not change existing behaviour. All 124 existing tests must still pass, and the test count may only go up.
- Do not change the rubric keywords, the weights, the pass threshold, `check_protocol`, any fixture JSON, any agent TOML or any skill.
- Do not touch the planted defects (`trace_bag` stall, missing fare class Z) or the planted flaw in `agents/duty_manager.toml`.
- **No second copy of the scoring logic.** New code calls `extract_facts`, `score_service_review` and `check_protocol`. It never re-implements weights, keywords or the threshold.
- Write the test first, run it, and see it fail. Then implement.
- Each task ends by adding a chapter to `docs/TUTORIAL.md` in the existing style (The idea, Why it matters, See it in the code, Try it), before `## Troubleshooting`.
- Run tests with `uv run pytest -q`.

---

## Task A: one review function (about 10 min)

### `acme/scoring.py`

```python
HARD_FAILURES = (
    "promised_compensation_without_confirmation",
    "missing_disclaimer",
    "missing_ai_disclosure",
)

def review_answer(answer: str, pnr: str, first_turn: bool = True) -> dict:
    """The single scoring path used both in the graph and by the evals.

    Returns:
      facts:         extract_facts(answer, pnr)
      score:         score_service_review(**facts)            (the full dict)
      protocol:      check_protocol(answer, first_turn)        (the full dict)
      hard_failures: the HARD_FAILURES that apply, in HARD_FAILURES order
      soft_failures: score["failed_facts"] minus "no_unconfirmed_promise"
    """
```

- `promised_compensation_without_confirmation` applies when that fact is True.
- `missing_disclaimer` applies when `protocol["has_disclaimer"]` is False.
- `missing_ai_disclosure` applies when `protocol["disclosed_ai"]` is False.
- Hard failures are what the live gate blocks on. Soft failures (wording facts such as option labels and next step) are only recorded, so the matching trap can never block a correct answer.

### Tests: `tests/test_scoring.py`

Load `tests/fixtures/reviewer_cases.json` the same way `tests/test_reviewer.py` does. Do not edit it.

- `good-acme01`: `hard_failures == []` and `soft_failures == []`.
- `bad-promise`: `hard_failures` equals all three `HARD_FAILURES`, in order.
- `trap-vocabulary`: `hard_failures == []`, `soft_failures == ["offered_options"]`, and `score["passed"] is False`. This is the matching trap: a soft failure only.
- `fail-no-booking`: `"missing_disclaimer"` is in `hard_failures` and `"used_booking"` is in `soft_failures`.
- `first_turn=False` on an answer with no AI disclosure gives no `missing_ai_disclosure`.
- **Parity**, parametrized over every fixture case: `review_answer(...)["score"]` equals `score_service_review(**extract_facts(...))`, and `["protocol"]` equals `check_protocol(...)`. This proves there is one scoring path.

---

## Task B: the in-graph gate (about 12 min)

### `acme/gate.py`

```python
MAX_ATTEMPTS = 2
HANDOFF_MESSAGE = "..."  # see the rules below

def gate_answer(answer: str, pnr: str, first_turn: bool = True, attempt: int = 1) -> dict:
    """Decide whether a drafted answer may reach the passenger.

    Returns {"decision": ..., "deliver_text": ..., "review": review_answer(answer, pnr, first_turn)}.
      deliver: no hard failures. deliver_text is the answer, unchanged. Soft failures never block.
      retry:   hard failures and attempt < MAX_ATTEMPTS. deliver_text is None.
      handoff: hard failures and attempt >= MAX_ATTEMPTS. deliver_text is HANDOFF_MESSAGE.
    Raise ValueError if attempt < 1.
    """
```

`HANDOFF_MESSAGE` is the safe fallback a passenger sees when the agents could not produce a safe answer. In plain sentences it must:

- say the passenger is talking to an AI assistant,
- say a member of the Acme Air team will take over, with the words "next step",
- make no compensation or refund promise,
- end with `acme.data.DISCLAIMER` verbatim. Build it by concatenating `DISCLAIMER`, never by retyping it.

The module docstring explains why the live gate is code and not the service_reviewer agent: an instruction to "call the reviewer last" relies on the model obeying, which is the same weakness as the planted flaw.

### Tests: `tests/test_gate.py`

- `good-acme01` gives `deliver` and `deliver_text` is the original answer, identical.
- `trap-vocabulary` gives `deliver` (soft failures never block), and its `review["soft_failures"] == ["offered_options"]`.
- `bad-promise` at `attempt=1` gives `retry` with `deliver_text is None`.
- `bad-promise` at `attempt=2` gives `handoff` with `deliver_text == HANDOFF_MESSAGE`.
- `HANDOFF_MESSAGE` passes `check_protocol` and has no hard failures under `review_answer(HANDOFF_MESSAGE, "ACME02")`.
- `attempt=0` raises `ValueError`.
- The gate's `review` equals `review_answer(...)` for the same inputs (parity again).

---

## Task C: the post-run eval harness (about 15 min)

### `acme/evals.py`

```python
FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "reviewer_cases.json"

def run_eval(cases: list[dict]) -> dict:
    """Score every case with review_answer and record what the live gate would do.

    Returns {"records": [...], "summary": {...}}.
      record, one per case, in input order:
        id, pnr, expected_pass, passed (score["passed"]), score (score["score"]),
        hard_failures, soft_failures, gate_decision (gate_answer at attempt=1),
        agrees (passed == expected_pass)
      summary: n, agreed, passed, hard_failed, delivered
    """

def render_html(result: dict) -> str:
    """A self-contained HTML report: summary first, then one table row per case.
    No external scripts, stylesheets, fonts or links. Every rate shows its sample
    size beside it, written as n=<count>. All case text is HTML-escaped."""

def main(argv: list[str] | None = None) -> int:
    """`uv run python -m acme.evals [--html PATH]`: print one summary line,
    e.g. 'reviewer agrees with labels 11/11 (n=11)', and write the report if asked."""
```

Use `argparse`, `html.escape` and `json` from the standard library. Showing the sample size beside every score is the spec's Part 3 rule.

### Tests: `tests/test_evals.py`

- On the fixture: `summary["n"] == 11` and `summary["agreed"] == 11`.
- Records come back in fixture order.
- `trap-vocabulary`'s record has `passed is False` and `gate_decision == "deliver"`. Post-run marks it down; the live gate lets it through. That difference is by design.
- `bad-promise`'s record has `gate_decision == "retry"`.
- **Parity:** every record's `score` equals `review_answer(...)["score"]["score"]` for that case.
- The HTML contains every case id and the text `n=11`, and contains neither `<script` nor `http`.
- A synthetic case with id `<b>x</b>` (pnr `ACME02`, any answer, `expected_pass: false`) appears escaped as `&lt;b&gt;x&lt;/b&gt;`.
- `main(["--html", str(tmp_path / "eval.html")])` returns 0, writes the file, and prints a line containing `11/11` (use `capsys`).

---

## Definition of done

- `uv run pytest -q` passes with more than 124 tests, and nothing is skipped other than the opt-in `llm` test.
- New files: `acme/scoring.py`, `acme/gate.py`, `acme/evals.py`, and their three test files.
- `docs/TUTORIAL.md` has Chapters 11 (one review function), 12 (the in-graph gate) and 13 (post-run evals), and every `file:line` link in it points at the right line.
- One commit per task, made by the supervisor.
- No push.

## Out of scope for this chunk

Installing or calling DeepEval, Langfuse or kagent; wiring the gate into a running agent or web app; any model call; changing the rubric, weights, protocol checks, fixtures, agents or skills.
