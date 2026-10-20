# Tonight's plan: Acme Air core in 2 hours

> **Note:** the `uv run mcp dev servers/...` check below fails on this Mac. Use `npx @modelcontextprotocol/inspector uv run python -m servers.fares_server` instead (see Troubleshooting in [docs/TUTORIAL.md](../docs/TUTORIAL.md)).

## What and why

The full spec is a 4.5-hour lab on a Kubernetes stack: kind/Podman, kagent, agentgateway, Keycloak, OpenFGA, Langfuse, DeepEval and Presidio. None of the cluster tooling is installed, and a 9B local model can't stand that up in 2 hours.

Section 0 says evaluation comes before agents. So tonight's chunk is the pure-Python core that every later part depends on:

- synthetic data
- 8 tools, with the two planted defects (the 4.5 s `trace_bag` stall and the class Z failure in `check_fare_rule`)
- a deterministic reviewer (the rubric plus `score_service_review`)
- a keyword routing baseline
- 5 FastMCP servers
- a pytest suite as the contract

Tomorrow's kagent work only needs to point at these servers.

Out of scope tonight: K8s, kagent, gateway, identity, tracing, DeepEval, Presidio, the web app and LLM agents.

The build spec is in [BUILD_SPEC.md](BUILD_SPEC.md).

## Before you start (10 min)

1. Raise Ollama's context window so the spec plus the code fits:

   ```bash
   launchctl setenv OLLAMA_CONTEXT_LENGTH 32768
   ```

   Then quit and reopen the Ollama app.
2. Pick a harness (see Q1). For the Goose route:

   ```bash
   brew install block-goose-cli
   ```

   ```bash
   goose configure
   ```

   Choose provider Ollama and model `qwen3.5:9b`.
3. Do BUILD_SPEC Task 0 by hand: write pyproject, run `uv python pin 3.12`, then `uv sync`.

## Run sheet

| Time | Step | Done when |
|---|---|---|
| 0:00 to 0:10 | Setup + Task 0 | `uv run pytest` runs (no tests) |
| 0:10 to 0:25 | Task 1: errors + data | test_data green, commit |
| 0:25 to 0:45 | Task 2: tools | test_tools green incl. 4.5 s stall and Z error, commit |
| 0:45 to 1:10 | Task 3: rubric + reviewer | 10+ reviewer cases green, commit |
| 1:10 to 1:25 | Task 4: routing | 10+ routing cases green, commit |
| 1:25 to 1:45 | Task 5: MCP servers | 8 tools listed, Inspector opens, commit |
| 1:45 to 2:00 | Full run, update TECH_STACK.md, note gaps | all green, final commit |
| Spare | Task 6: LLM router | accuracy number recorded vs keyword baseline |

If you're behind at 1:10, cut Task 4's extra cases down to the 6 given ones. If you're behind at 1:45, ship without Task 5's Inspector check.

## Loop per task (built for a 9B model)

1. Start a new chat. Paste the Global rules, the task section, and the current contents of the files the task imports.
2. Ask for the **test file only**. Check it against the task's assertion list.
3. Run it and watch it fail: `uv run pytest tests/test_x.py -q`.
4. Ask for the implementation, **one file per answer**.
5. On failure, paste back only the failing test name and the last error line. After 2 failed retries, switch to `qwen2.5-coder:7b` or hand-fix.
6. When green, commit with `git add -A && git commit -m "task N: ..."`.

## Questions to decide, with recommendations

1. **Which harness drives qwen?** Goose, OpenCode and Continue are all missing.
   *Rec:* use the Goose CLI on Ollama `qwen3.5:9b`. It is the spec's Part 0 pick, so tonight doubles as a dry run. If tool calls flake within 10 minutes, drop to chat-and-paste (Continue in VS Code, or `ollama run qwen3.5:9b`). Don't spend the night debugging the harness.

2. **Thinking mode on or off?**
   *Rec:* keep it off (`think: false`, or `/no_think` in chat) while implementing, because it is several times faster. Turn it on only to diagnose a test that keeps failing.

3. **Who writes the tests, qwen or Claude?**
   *Rec:* qwen writes them from the spec's assertion lists and you review them before implementing, which is the TDD loop from Section 0. If a test file comes out wrong twice, have Claude write that one file. The tests are the contract, so they must be right.

4. **How are the 8 tools split across 5 servers?** The spec doesn't say.
   *Rec:* ops (get_booking, get_flight_status, search_alternative_flights), baggage, loyalty, fares (2) and review. Write this back into the spec.

5. **What does "passes if ≥90% of facts match" mean with 5 facts?** In practice it means all 5.
   *Rec:* make it a weighted score that passes at ≥0.90, with a compensation promise as a hard fail at 0. The weights live only in `score_service_review`, which matches the spec ("weights live in the tool").

6. **The gate needs ≥10 accepted answers for each of 7 agents, which is 70 cases. Tonight?**
   *Rec:* no. Tonight covers the reviewer (10) and routing (10). Add 10 per desk once real agents produce answers.

7. **DeepEval tonight?**
   *Rec:* no. Note the contradiction in the spec: gate 0.4 bans free-form judges, but DeepEval Task Completion is LLM-judged. Decide that the deterministic pytest suite is the gate, and that DeepEval judge metrics are reported but non-gating.

8. **Should the spec get an edit pass?**
   *Rec:* yes, a 15-minute pass tomorrow. Fix these:
   - 0.3 says "three core metrics" but lists four.
   - Section 0 sits above the title.
   - The agent, tool and stack tables were split by the docx conversion.
   - The 5.7 table is broken.
   - TECH_STACK.md says "gwen3.5"; the Ollama tag is `qwen3.5:9b`.

9. **What about the unzipped .docx files in the repo root?**
   *Rec:* they are gitignored now (`[Content_Types].xml`, `_rels/`, `docProps/`, `word/`). Delete them when convenient, and keep the source .docx outside the repo or in `docs/`.

10. **Which model if qwen3.5:9b stalls?**
    *Rec:* use `qwen2.5-coder:7b` for the mechanical files (data.py, servers). Keep qwen3.5:9b for the rubric and routing logic, where reasoning matters.

11. **When should the cluster stack be installed?**
    *Rec:* tomorrow, in a separate session. Install Podman, kind and kubectl first, then kagent, with its agents pointing at tonight's MCP servers.

12. **Should rules 6 (AI disclosure) and 7 (disclaimer) be in the rubric?** The rubric defines 5 facts.
    *Rec:* keep the rubric at 5 as the spec says. Add `disclosed_ai` and `has_disclaimer` as separate protocol checks once agents produce answers. Rule 6 is a legal requirement (Article 50), so it deserves its own named test.

13. **How often should you commit?**
    *Rec:* once per green task, so `git checkout -- .` can undo a bad qwen edit in one command.

14. **Is 3.15 or 3.12 the right Python version?** The system Python is 3.15.
    *Rec:* pin 3.12 through uv. Wheels for `pydantic-core` (pulled in by `mcp`) may not exist for 3.15 yet, and a Rust build would eat your night.

## Verification at the end

```bash
uv run pytest -q --durations=5
```

```bash
uv run mcp dev servers/fares_server.py
```

```bash
ACME_LLM=1 uv run pytest -m llm -s
```

Check these:
- All tests are green, and trace_bag shows ≥4.5 s in the durations.
- The Inspector lists 2 fares tools, and `check_fare_rule` with `Z` shows the planted error.
- The reviewer is proven both ways (the bad answer fails, the good answer passes), and the vocabulary trap is recorded.
- Optional: the LLM router accuracy compared with the keyword baseline.

## Tomorrow's next step

Spec edit pass (Q8). Then install Podman, kind and kubectl, and wrap these MCP servers as kagent `RemoteMCPServer` resources.
