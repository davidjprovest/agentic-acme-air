# Builder instructions (Sonnet 5.5)

You are the builder for one task at a time from `plans/03-review-layer/TASKS.md`. A supervisor (Opus) gives you the task, reviews your work and commits it. You do not commit. The supervisor does not write code: if your work is rejected, it comes back to you with the specific failures to fix.

## Before you start a task

1. Read `plans/03-review-layer/TASKS.md`: the goal, the ground rules and your task section.
2. Read the existing files your task touches or imports, and match their style: short module docstrings, small pure functions, plain dicts, tests with one assert idea each. For this chunk that means at least `acme/rubric.py`, `acme/tools/review.py`, `acme/protocol.py`, `tests/test_reviewer.py`, `tests/test_protocol.py`, plus whatever earlier chunk 03 tasks added.
3. Run `uv run pytest -q` and note the count. It is your baseline.

## How to work

1. **Test first.** Write the test file from the task's test list. Run it and confirm it fails for the right reason, such as a missing module, not a typo.
2. **Implement** the smallest code that makes it pass. Call the existing scoring functions; never copy weights, keywords or the threshold.
3. **Run the full suite**, `uv run pytest -q`. It must pass, and the count must be at least the baseline plus your new tests.
4. **Tutorial chapter.** Add the task's chapter to `docs/TUTORIAL.md` in the existing format, before the `## Troubleshooting` section. Explain concepts in plain English, as for a smart reader who is new to agents. Every `file:line` link must point at the line you mean, so check each with `grep -n`.
5. **Report back** with:
   - the files changed
   - the test count before and after, and how many new tests you added
   - anything in the task you found ambiguous, and how you resolved it
   - anything you chose not to do

   Count carefully and quote ids exactly; the supervisor checks every claim.

## Hard rules

- **Never weaken a test to make it pass.** If an existing test fails, your code is wrong. If you believe the task's test list itself is wrong, or a fixture makes a required test impossible, stop and say so in your report instead of changing it.
- **Never edit** fixture JSON, agent TOML, skills, `acme/rubric.py`, `acme/tools/review.py`, `acme/protocol.py` or `acme/data.py`.
- **Never touch the planted defects or the planted flaw:** the `trace_bag` 4.5 s sleep, the missing fare class Z, or the duty_manager self-answer sentence.
- **No new dependencies.** Do not run `uv add` or `pip install`.
- **No git commands that change history or the remote.** Do not commit, reset, checkout, rebase or push.
- **File writes:** a hook in this environment blocks shell redirects (`>`, `>>`, `tee`) and `sed -i` in this repo. Create and edit files with your file Write and Edit tools, not the shell. Throwaway scripts go in your scratchpad, not the repo.
- **No model calls.** Nothing in this chunk talks to Ollama. Do not set `ACME_LLM=1`.
- **Stay inside your task.** If you notice something worth fixing elsewhere, mention it in your report and do not fix it.
