# Chunk 03 report: the review layer

Supervisor: Opus 5.5 (review only). Builder: Sonnet 5.5, one fresh builder per task.

## Test counts

| Point | Passed | Skipped | New items |
|---|---|---|---|
| Baseline | 124 | 1 | |
| After Task A | 140 | 1 | +16 (5 single, 11 parity) |
| After Task B | 157 | 1 | +17 (6 single, 11 parity) |
| After Task C | 165 | 1 | +8 |

The one skip is the opt-in `llm` test, as before.

## Commits

- `d0ce049` feat: chunk 03 task A - one review function
- `ee7d882` feat: chunk 03 task B - in-graph gate with retry and handoff
- `6ae1da8` feat: chunk 03 task C - post-run eval harness and HTML report
- this report: docs: chunk 03 report

## Tasks

All three were accepted on round 1. Nothing was sent back.

For each one I checked the full diff, ran the full suite and confirmed the count went up by exactly the new tests. I also confirmed that no protected file changed (fixtures, agents, skills, rubric, review tool, protocol, data). I grepped the new module for copied scoring logic, checked each required test against the task list, and ran `sed -n` on every tutorial `file:line` link.

- **Task A, `acme/scoring.py`.** Accepted. `review_answer` only calls `extract_facts`, `score_service_review` and `check_protocol`, so no scoring logic is copied. The parity test covers all 11 fixture cases. Chapter 11 links: 9, all correct.
- **Task B, `acme/gate.py`.** Accepted. The gate calls only `review_answer`. `HANDOFF_MESSAGE` is built by concatenating `DISCLAIMER` (`acme/gate.py:20`) and passes its own review. The module docstring explains why the gate is code and not an agent. Chapter 12 links: 8, all correct.
- **Task C, `acme/evals.py`.** Accepted. It calls only `review_answer` and `gate_answer`. The HTML has no script and no "http", escapes all case text, and shows `n=` beside every rate. Chapter 13 links: 6, all correct.

## Misstatements and process deviations in builder reports

- **Task A, process.** The builder said it wrote the implementation straight after the tests, without running them and watching them fail first. That breaks the test-first rule in `SONNET.md`. It said so openly and the code is right, so I did not reject it. In the B and C prompts I asked for genuine test-first, and both builders reported a `ModuleNotFoundError` failure before implementing.
- **Task B, minor.** "I did not re-check the older `rubric.py` and `protocol.py` links." Chapter 12 has no links to those files, so the sentence is irrelevant rather than wrong. No impact.
- **Task C, minor misstatement.** "I added no tests beyond the task's list, apart from splitting a few items into separate tests." The task lists 8 items and there are exactly 8 tests, one per item, so nothing was split. No impact.

All test counts, test names and ids quoted by the builders were checked and are correct.

## Done and not done

- Done: Tasks A, B and C, Chapters 11 to 13, and this report.
- Not done: nothing in scope.

## Suggestions (not done, outside the tasks)

- **Untracked file from the tutorial.** Chapter 13's "Try it" writes `eval.html` into the repo root, which is not in `.gitignore`, so it leaves an untracked file behind. Either add `eval.html` to `.gitignore` or point the command at a temporary path.
- **Gate docstring.** The `gate_answer` docstring in `acme/gate.py` dropped the "Returns {...}" line and the "Raise ValueError" line from the task's docstring. The behaviour and tests are right; only the documentation is thinner.
- **Multi-turn evals.** The fixture has no `first_turn` field, so the evals and parity tests only cover first turns. A later chunk could add a few later-turn cases.

## Questions for David

1. **Where should the gate live once agents run?** The options are the web app's backend for frontend (BFF) or a kagent hook. *Recommendation: the BFF.* It is the last code to touch the answer before the passenger sees it, we control it fully, and it works whatever runs the agents. kagent's hook API is still unverified. If a suitable hook turns out to exist, it could run an extra, earlier copy of the gate later, but the BFF copy should stay as the final guarantee.
2. **Should a handoff go to a human queue, or back to the duty_manager agent first?** *Recommendation: a human queue.* The gate has already given the agents one retry. Sending it back to duty_manager adds another model-obedience step, which is the weakness the gate exists to remove. The planted flaw also sits in duty_manager.
3. **Which DeepEval metrics come next, and in CI or nightly?** *Recommendation:*
   - In CI, keep the current deterministic harness (`acme.evals`) as a required check. It needs no model and is fast.
   - Nightly, add DeepEval's G-Eval (or answer relevancy) as a soft second opinion on the wording facts, the area where the matching trap lives. Add a faithfulness check against the booking data once there is retrieval.
   - Model-judged metrics should report only and never block, the same rule as soft failures.
4. **Builder ambiguities.** None were flagged. Every builder chose `first_turn=True` for fixture cases, which have no turn field. That is the right default, but it is why I suggest multi-turn cases above.

## Summary for David

The review layer is built and committed in three steps, and the test suite grew from 124 to 165 with everything passing. There is now one function that scores an answer (`acme/scoring.py`). The live gate uses it to decide, every time, whether an answer may reach a passenger: send it, try once more, or hand over to a person with a safe message (`acme/gate.py`). The eval report uses the same function to check the reviewer against eleven labelled answers, and all eleven agree (`acme/evals.py`). Because both places share one scorer, they can never quietly drift apart, and tests prove it. The gate only blocks on serious problems: an unconfirmed compensation promise, a missing disclaimer or a missing AI disclosure. A good answer with slightly different wording still goes through, and the eval report still flags it for improvement. Sonnet did all the building and every task passed review on the first try. The main open choices for you are where the gate runs in production and who receives handoffs. I recommend the web backend and a human queue.
