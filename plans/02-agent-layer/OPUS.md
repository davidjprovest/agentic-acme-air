# Supervisor instructions (Opus 5.5)

You supervise chunk 02 of the Acme Air lab. You do three things in a 60 minute box:

1. Review the codebase and clean it up.
2. Dispatch the build tasks to a Sonnet 5.5 builder.
3. Review and commit the builder's work.

David is the owner. He wants each step explained in simple terms, with pointers to the important lines, so write your updates for him, not for another engineer.

## Context you need

- The repo is the pure-Python core of the lab spec (`Acme Air multi-agent lab open source specification.md`):
  - `acme/`: data, 8 tools, rubric, routing, LLM router
  - `servers/`: 5 FastMCP servers
  - `tests/`: 67 tests passing, 1 opt-in `llm` test skipped
  - `docs/TUTORIAL.md`: one chapter per task
- The chunk 01 plan and spec are in `tonight/`. Chunk 02 is in this folder: `TASKS.md` for the work and `SONNET.md` for the builder's rules.
- **Environment traps:**
  - A hook blocks shell redirects and `sed -i` in this repo, so edit files with the Write and Edit tools.
  - Start servers with `python -m servers.<name>`, never `mcp dev <file>`.
  - Don't call Ollama.
  - Never rewrite git history and never push.

## Phase 0: baseline (5 min)

1. Run `uv run pytest -q` and `git status`. Record the test count and confirm the tree is clean.
2. Read every file in `acme/`, `servers/` and `tests/`, plus `docs/TUTORIAL.md`, `README.md`, `TECH_STACK.md` and `tonight/BUILD_SPEC.md`.

## Phase 1: cleanup review (15 min, you do this yourself)

Goal: make the codebase cleaner and more succinct **without changing behaviour**. Work in this order:

1. **Propose.** Write `plans/02-agent-layer/CLEANUP.md`, a table with these columns: item, file(s), what and why, risk (low or med), decision (apply or skip, with a reason).
2. **Apply.** Do the low-risk "apply" items. After each group, run the full suite and commit with a message like `chore: <what>`.
3. **Skip the rest.** Medium-risk items stay listed as proposals for David.

### Constraints that override any cleanup idea

- **Test count only goes up.** Never delete or weaken a test assertion.
- **The planted defects stay byte-for-byte:** the `trace_bag` sleep and its comment, and the missing class Z with its error message.
- **The MCP surface is unchanged:** server names, tool names, parameter names and types. Docstrings may be tightened but must keep their "Use for:" keywords.
- **Data values in `acme/data.py` and every fixture JSON are unchanged.**
- **Teaching clarity beats DRY.** The tutorial teaches "look it up, raise if missing, return a copy" from the tools. If you factor that into a shared helper, the pattern has to stay obvious to a reader, and the tutorial must be updated. If in doubt, leave the tools explicit.
- **After any code move, re-check every `file:line` link in `docs/TUTORIAL.md`.**

### Candidates to assess

These came from the person who built chunk 01. Assess each one rather than assuming it is right, and add any you find:

- The fixture-loading boilerplate (`json.loads(Path(__file__).parent / "fixtures" / ...)`) is repeated in 3 test files. A `tests/conftest.py` helper may be cleaner.
- `tonight/BUILD_SPEC.md` is now stale in two places:
  - It tells the LLM router to send `"format": "json"`, which Ollama 0.40 rejects.
  - It says to use `uv run mcp dev servers/...`, which fails on this Mac.

  Either correct it or add a short "superseded" note at the top pointing to the code and tutorial.
- `TECH_STACK.md` still says "gwen3.5" (the model is `qwen3.5:9b`) and doesn't list what was actually used: uv, Python 3.12, `mcp` 1.30 FastMCP, pytest and Ollama 0.40.
- `README.md` is one line. Give it a short quickstart: `uv sync`, `uv run pytest -q`, the Inspector command, `ACME_LLM=1` for the live router test, and links to the tutorial and plans.
- `acme/tools/review.py` builds an `earned` dict that repeats the weight names. Check whether it can be simpler while staying readable.
- Repeated `.upper()` plus lookup plus `deepcopy` across the 4 tool modules. See the teaching-clarity constraint above.
- `tests/test_llm_router.py` duplicates the comparison printing. It is probably fine, but check.

## Phase 2: dispatch the builder (35 min)

Run Tasks A, B, C and D from `TASKS.md` **in that order, one at a time**. C validates B, and B names A's skills.

For each task:

1. **Dispatch.** Spawn a builder with the Agent tool, `model: "sonnet"`, and a prompt containing:
   - "Read plans/02-agent-layer/SONNET.md and follow it exactly."
   - "Your task is Task <X> in plans/02-agent-layer/TASKS.md."
   - anything from your cleanup that changed a file the task touches, such as a new `conftest.py` helper to use

   Use `run_in_background: false`, because you need the result before the next task.
2. **Review.** When the builder reports back, do not trust the report. Check it:
   - `git diff --stat` and read the full diff.
   - `uv run pytest -q`: it passes, and the count went up by the new tests only.
   - Confirm no existing test was edited, using `git diff tests/` on old files.
   - Check every requirement in the task section, line by line.
   - The planted flaw and defects are untouched.
   - The tutorial chapter exists and its links resolve.
3. **Decide.**
   - **Accept:** commit with `feat: chunk 02 task <X> - <summary>`.
   - **Reject:** send the specific failures back to the same builder with SendMessage. Allow at most 2 rounds. After that, fix it yourself and say so in the report.
4. **Explain to David** in 3 to 5 plain lines: what was built, why it matters, and which 2 or 3 file lines to read.

If a task blows its time box, finish the current task cleanly, skip the rest and list them as not done. Don't start a task you can't finish.

## Phase 3: report (5 min)

Write `plans/02-agent-layer/REPORT.md` with:

- the test count before and after
- the commits made
- the cleanup items applied and skipped
- the tasks done and not done
- the questions for David, each with your recommendation. At least these:
  - Should service_reviewer run inside the agent graph, or only from the evaluation harness?
  - Is the TOML-to-kagent rendering the next chunk, or the web app?
  - Anything ambiguous the builder flagged.

End with a one-paragraph summary for David in plain English.

## Commit format

End every commit message with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

Builder-written commits are still made by you, so use the same line.
