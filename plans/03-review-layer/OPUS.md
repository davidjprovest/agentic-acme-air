# Supervisor instructions (Opus 5.5): review only

You supervise chunk 03 of the Acme Air lab in a 60 minute box. **Sonnet builds; you review.** You do three things:

1. Take a baseline.
2. Dispatch Tasks A, B and C from `TASKS.md` to a Sonnet 5.5 builder, review each one and commit it.
3. Write the report.

**You write no code, tests or tutorial text.** Your only file writes are `REPORT.md` and commits. Every defect goes back to the builder.

David is the owner. Explain each step to him in simple terms as you go, with pointers to the important `file:line`s. Write for him, not for another engineer.

## Context you need

- Chunk 03 builds the review layer decided in `plans/02-agent-layer/REPORT.md`, question 1: one scorer, called live by a gate and after the fact by an eval harness.
- `TASKS.md` in this folder is the work. `SONNET.md` is the builder's rules.
- **Environment traps:**
  - A hook blocks shell redirects and `sed -i` in this repo.
  - Start servers with `python -m servers.<name>`, never `mcp dev <file>`.
  - Don't call Ollama.
  - Never rewrite git history and never push.

## Phase 0: baseline (5 min)

1. Run `uv run pytest -q` and `git status`. Expect 124 passed, 1 skipped, and a clean tree. If the tree is not clean, stop and ask David.
2. Read `TASKS.md`, `SONNET.md`, and the files the tasks build on: `acme/rubric.py`, `acme/tools/review.py`, `acme/protocol.py`, `tests/fixtures/reviewer_cases.json`.

## Phase 1: dispatch and review (45 min)

Run Tasks A, B and C **in that order, one at a time**. B calls A's `review_answer`; C calls both.

For each task:

1. **Dispatch.** Spawn a builder with the Agent tool, `model: "sonnet"`, `run_in_background: false`, and a prompt containing:
   - "Read plans/03-review-layer/SONNET.md and follow it exactly."
   - "Your task is Task <X> in plans/03-review-layer/TASKS.md."
   - the current test count, and the chapter number for the tutorial (A = 11, B = 12, C = 13)
   - anything from an earlier task the builder needs to know
2. **Review.** Do not trust the report. Check it yourself:
   - `git status` and the full diff of every changed and new file.
   - `uv run pytest -q`: it passes, and the count went up by exactly the number of new tests.
   - No existing file outside the task changed. In particular, `git diff` shows nothing for `tests/fixtures/`, `agents/`, `skills/`, `acme/rubric.py`, `acme/tools/review.py`, `acme/protocol.py` and `acme/data.py`.
   - **No second copy of scoring logic:** grep the new module for weights, keywords, `0.90` or retyped disclaimer text.
   - Every requirement in the task section, line by line, including each test in its test list.
   - The tutorial chapter exists in the right place, and every `file:line` link in it lands on the intended line. Check with `sed -n '<n>p' <file>`.
   - Check every number and id the builder quotes. Note any misstatement in the report even if the code is right.
3. **Decide.**
   - **Accept:** commit with `feat: chunk 03 task <X> - <summary>`.
   - **Reject:** send the specific failures back to the same builder with SendMessage, quoting the requirement and what you found. Allow at most 2 rounds. If it still fails, do not fix it yourself: leave it uncommitted, stop the chunk (later tasks depend on it), and report it to David as not done with the remaining failures.
   - **A gap the task did not ask for** (a missing test you think matters): don't add it yourself. Send it to the builder as an extra request if it is small and inside the task; otherwise list it in the report as a suggestion.
4. **Explain to David** in 3 to 5 plain lines: what was built, why it matters, and which 2 or 3 `file:line`s to read.

If the time box runs short, finish reviewing the current task cleanly, don't start the next one, and list the rest as not done.

## Phase 2: report (5 min)

Write `plans/03-review-layer/REPORT.md` with:

- the test count before and after each task
- the commits made
- each task: accepted on which round, what was sent back and why
- every misstatement found in a builder report
- the tasks done and not done
- questions for David, each with your recommendation. At least these:
  - Where should the gate live once agents run: in the web app's backend for frontend (BFF), or in a kagent hook if one exists? Note that kagent's API is still unverified.
  - Should the handoff go to a human queue, or back to the duty_manager agent first?
  - Which DeepEval metrics come next, and do they run in CI or nightly?
  - Anything ambiguous the builder flagged.

Commit the report as `docs: chunk 03 report`. End with a one-paragraph summary for David in plain English.

## Commit format

End every commit message with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
