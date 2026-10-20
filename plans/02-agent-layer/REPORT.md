# Chunk 02 report

## Tests

| | Passed | Skipped |
|---|---|---|
| Before (start of chunk) | 67 | 1 (opt-in `llm`) |
| After cleanup | 67 | 1 |
| After Task A | 95 | 1 |
| After Task B | 95 | 1 (B adds files only; C tests them) |
| After Task C | 113 | 1 |
| After Task D | **124** | 1 |

No existing test was edited except the cleanup tweak in `tests/test_reviewer.py:33` (same assertion, now calls the existing `review()` helper). Unchanged since the start of the chunk: `acme/data.py`, every fixture JSON, `acme/tools/baggage.py`, `acme/tools/fares.py`, all of `servers/`. All 31 `file:line` links in `docs/TUTORIAL.md` were re-checked and land on the intended line.

## Commits (none pushed)

```
5385392 feat: chunk 02 task D - AI disclosure and disclaimer protocol checks
f98d7aa feat: chunk 02 task C - agent loader and consistency tests
2480652 feat: chunk 02 task B - seven agent definitions in TOML
4a6b0d9 feat: chunk 02 task A - service recovery and review rubric skills
791fc2a chore: README quickstart, accurate TECH_STACK, superseded notes on chunk 01 plans
d2db716 chore: tighten reviewer score sum and reuse review() helper in tests
```

## Cleanup (full table in CLEANUP.md)

**Applied:** superseded notes on `tonight/BUILD_SPEC.md` and `tonight/PLAN.md` (`"format": "json"`, `mcp dev`); `TECH_STACK.md` rewritten with what is actually used; `README.md` quickstart; reviewer sums `WEIGHTS.items()`; parametrized reviewer test reuses `review()`.

**Skipped:** shared fixture loader (parametrize needs data at import time, gain ~3 lines); shared tool lookup helper (medium risk, hides the pattern the tutorial teaches); `compare()` printing (not actually duplicated); unzipped `.docx` debris in repo root (already gitignored, deleting local files is your call); fixture path style (cosmetic).

## Tasks

All four done, one commit each. Each was accepted on the first round; no rejections.

- **A, skills:** accepted. I added one test myself: each escalation-table row in the protocol skill must match `acme/routing.py` exactly (`tests/test_skills.py:72`). The builder's tests only checked desk names, so keyword drift would have gone unnoticed.
- **B, agent TOMLs:** accepted as delivered.
- **C, loader and tests:** accepted as delivered.
- **D, protocol checks:** accepted. The builder's report miscounted the good fixture cases (said 6, there are 5); the code and tests are correct.

Not done: nothing.

## Questions for David

1. **Should service_reviewer run inside the agent graph, or only from the evaluation harness?**
   *Recommendation: evaluation harness only.* It scores answers and never resolves cases, so putting it in the graph invites the duty manager to route passengers to it and adds a model call to every answer. Run it after the fact over transcripts; it stays a pure judge and you keep its scores comparable across runs.
2. **Is TOML-to-kagent rendering the next chunk, or the web app?**
   *Recommendation: kagent rendering first.* The agents only become testable against a real model once they run somewhere, and Part 1's planted-flaw exercise needs that. The web app is a front end on top of a working graph. Install kagent, check its real CRD schema, then write the renderer against it, with a golden-file test per agent.
3. **Should the frontmatter parser move to `acme/skills.py`?** (builder flagged) It lives in `tests/test_skills.py:13` because only tests use it. *Recommendation: move it when the kagent renderer needs to read skills, not before.*
4. **Should the escalation table have one source?** The keyword table now appears in `acme/routing.py`, the protocol skill, and (as keywords) in each agent description. Tests keep them in sync, which is the right call for now. *Recommendation: leave it; if it changes often, generate the skill table from code.*
5. **The `.docx` debris** (`[Content_Types].xml`, `_rels/`, `docProps/`, `word/`) in the repo root: gitignored, but clutters the folder. *Recommendation: delete it locally.*

## Summary

The codebase now describes its agents, not just its tools. There are two rulebooks (skills) that every agent reads, seven agent definitions in plain TOML files, a loader that refuses broken files, and tests that tie all of it to the real MCP servers and routing table without ever calling a model. That means a typo in a tool name, a tool with no owner, or a rulebook that drifts from the code now fails in under a second instead of in front of a passenger. Two missing protocol rules, the AI disclosure and the disclaimer, now have their own checks. The planted lab flaws are intact and guarded by tests. The suite went from 67 to 124 passing tests across six commits, nothing pushed. The next decision is yours: render these agents to kagent (my pick) or start the web app.
