# Chunk 02: the agent layer, defined and tested offline

**Time box:** 60 minutes total: about 20 for the supervisor's cleanup and about 40 for these tasks.
**Builds on:** the core from chunk 01 (`acme/`, `servers/`, 67 tests).
**Spec reference:** `Acme Air multi-agent lab open source specification.md`, sections 2 (Scenario, Agent skills) and 3 (Part 1 learning points).

## Goal

Define the seven agents and the two agent skills as plain files in the repo, and prove with tests that they are consistent with the tools, servers and routing table that already exist. Also add the two protocol checks that the five-fact rubric leaves out: AI disclosure and the closing disclaimer.

Nothing here calls a model, installs software or needs Kubernetes. The agent files use **our own simple TOML format**, not kagent YAML. A later chunk renders them to kagent resources once kagent is installed and its API can be checked against the real thing. That avoids writing against an API nobody has verified.

## Ground rules for every task

- Dependencies: standard library only on top of what is installed. `tomllib` is in the standard library, and there is no PyYAML.
- Do not change existing behaviour. All 67 existing tests must still pass, and the test count may only go up.
- Do not touch the planted defects (`trace_bag` stall, missing fare class Z) or the planted orchestrator flaw described in Task B.
- Write the test first, run it, and see it fail. Then implement.
- Each task ends by adding a chapter to `docs/TUTORIAL.md`, in the existing style: The idea, Why it matters, See it in the code, Try it.
- Run tests with `uv run pytest -q`.

---

## Task A: the two agent skills (about 8 min)

Create these two files in the open SKILL.md format: YAML-style frontmatter with `name` and `description`, then a markdown body.

### `skills/service-recovery-protocol/SKILL.md`

- Frontmatter: `name: service-recovery-protocol`, plus a one-line description of when to use it. Every passenger-facing Acme Air agent applies it to every answer.
- Body: the seven rules from spec section 2, in order and numbered 1 to 7:
  1. Retrieve the booking before reasoning, and never invent booking data.
  2. Handle anything time-critical first, for example a departure in 40 minutes.
  3. Present at least two options, labelled "Option 1" and "Option 2", before a decision.
  4. Make no compensation or refund promise before eligibility is confirmed. Say "subject to eligibility".
  5. Use the escalation table that maps topic to owning desk. Reproduce the table from `acme/routing.py`, with each desk and its keywords.
  6. Disclose in the first turn that the passenger is talking to an AI assistant.
  7. Close every answer with the disclaimer, verbatim: `Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice.`

Rule 3's "Option 1" and "Option 2" wording and rule 4's "subject to eligibility" are deliberate. They match the reviewer's literal keywords, so agents that follow the skill pass the rubric.

### `skills/service-review-rubric/SKILL.md`

- Frontmatter: `name: service-review-rubric`, plus a description. It is used by the service_reviewer agent to score an existing answer.
- Body: the five facts and the exact keywords for each, copied from the constants in `acme/rubric.py` (`OPTION_MARKERS`, `URGENCY_WORDS`, `NEXT_STEP`, `PROMISE_WORDS`, `ELIGIBILITY_CAVEAT`). Then the instruction: pass the five booleans to `score_service_review` and never compute or adjust the score yourself.

### Tests: `tests/test_skills.py`

- Write a small frontmatter parser in the test file (or in `acme/skills.py` if Task C needs it too). It reads the lines between the first two `---` lines as `key: value` pairs.
- For each skill folder under `skills/`, check that the frontmatter `name` equals the folder name and that `description` is not empty.
- The protocol skill contains `acme.data.DISCLAIMER` verbatim.
- The protocol skill contains every desk name from `ESCALATION_TABLE`.
- The rubric skill contains every keyword from the five `acme/rubric.py` constants. This test keeps the document and the code in sync: if someone changes a keyword in code, this test fails until the skill is updated.

---

## Task B: seven agent definitions (about 12 min)

Create one TOML file per agent in `agents/`. They all share this schema:

```toml
name = "fares"
description = """Owns every question about fare rules, change fees, fare classes,
date changes and pets in cabin. Keywords: fare, fee, date change, pet."""
skills = ["service-recovery-protocol"]
tools = ["acme-fares/check_fare_rule", "acme-fares/list_fare_classes"]
delegates = []
system_message = """..."""
```

- `tools` entries are `"<FastMCP server name>/<tool name>"`.
- `delegates` lists agent names this agent may hand work to.
- `description` is a **routing trigger**: the topics and keywords the agent owns, never a personality blurb. This is spec Part 1's point.

| File | Tools | Delegates | Skills |
|---|---|---|---|
| `duty_manager.toml` | acme-ops/get_booking, acme-ops/get_flight_status | rebooking, baggage, loyalty, fares, customer_relations | service-recovery-protocol |
| `rebooking.toml` | acme-ops/search_alternative_flights | none | service-recovery-protocol |
| `baggage.toml` | acme-baggage/trace_bag | none | service-recovery-protocol |
| `loyalty.toml` | acme-loyalty/get_loyalty_account | none | service-recovery-protocol |
| `fares.toml` | acme-fares/check_fare_rule, acme-fares/list_fare_classes | none | service-recovery-protocol |
| `customer_relations.toml` | none (`tools = []`) | none | service-recovery-protocol |
| `service_reviewer.toml` | acme-review/score_service_review | none | service-review-rubric |

That is 8 tools, each assigned to exactly one agent. service_reviewer is **not** a delegate of duty_manager: it scores answers and never resolves a case. Whether it runs inside the graph or from the evaluation harness is decided in Part 2, so record that as an open question in the tutorial chapter.

### What each system message must say

Write these in plain sentences.

- **duty_manager:**
  - You are the single entry point.
  - Retrieve the booking with get_booking first.
  - Frame the problem, then delegate to the desk that owns it, using the escalation table.
  - Disclose that you are an AI assistant in your first turn.
  - **PLANTED FLAW:** include this sentence verbatim: `If you can answer the question yourself with your own tools, answer it directly instead of delegating.` Put this TOML comment on the line above the `system_message` key: `# PLANTED FLAW (spec Part 1): the sentence starting "If you can answer the question yourself" makes the orchestrator self-answer. Participants find it, remove it and re-measure. Do not remove it here.`
- **rebooking, baggage, loyalty:**
  - Own your topics.
  - Use your tool before answering.
  - Follow service-recovery-protocol.
- **fares:** the same as the three above, plus: if check_fare_rule reports a missing fare class, report the missing class to the passenger, call list_fare_classes, and never invent a rule.
- **customer_relations:**
  - Owns compensation, complaints, legal threats and refunds.
  - Refuses operational questions in one sentence that names the owning desk.
  - Never promises compensation before eligibility is confirmed.
- **service_reviewer:**
  - Scores an existing answer against service-review-rubric.
  - Extracts the five facts and passes them to score_service_review.
  - Never computes the score and never resolves a case.

### Descriptions

Each desk agent's description must contain at least 3 of that desk's keywords from `ESCALATION_TABLE` in `acme/routing.py`. Desks with fewer than 3 keywords must contain all of them. duty_manager's description says it is the entry point that frames and routes every passenger question. service_reviewer's says it scores answers.

---

## Task C: loader and consistency tests (about 10 min)

### `acme/agents.py`

```python
AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
REQUIRED_KEYS = {"name", "description", "skills", "tools", "delegates", "system_message"}

def load_agents(directory: Path = AGENTS_DIR) -> dict[str, dict]:
    """Read every agents/*.toml with tomllib, keyed by name.
    Raise ValueError naming the file if a key is missing or name != file stem."""
```

### Tests: `tests/test_agents.py`

- There are exactly 7 agents: duty_manager, rebooking, baggage, loyalty, fares, customer_relations and service_reviewer.
- Every agent has all of `REQUIRED_KEYS`.
- **Tools exist.** For every `server/tool` entry, the tool is listed by that server's `mcp.list_tools()`. Build a map from FastMCP name to module, for example `acme-ops` to `servers.ops_server`. Reuse the pattern in `tests/test_servers.py`.
- **Every tool is owned exactly once.** The tool entries across all agents number 8, contain no duplicates, and equal the set of all tools on all 5 servers.
- The ownership matches the Task B table exactly.
- Every delegate is a known agent. duty_manager's delegates are exactly the 5 desks.
- customer_relations has `tools == []`.
- **Routing-trigger rule.** Each desk's description contains at least `min(3, len(keywords))` of its `ESCALATION_TABLE` keywords, matched case-insensitively.
- Every skill named by an agent exists as `skills/<name>/SKILL.md`.
- The planted flaw sentence is present in duty_manager's system_message. Give this test a docstring saying it guards a planted lab flaw and must not be "fixed".
- fares' system_message contains `list_fare_classes` and the word `invent`.
- `load_agents` on a temporary directory holding one broken file raises `ValueError` naming the file. Use pytest's `tmp_path`.

---

## Task D: protocol checks (about 7 min)

### `acme/protocol.py`

```python
AI_DISCLOSURES = ("ai assistant", "virtual assistant", "talking to an ai", "chatting with an ai")

def check_protocol(answer: str, first_turn: bool = True) -> dict:
    """Spec rules 6 and 7, checked literally and case-insensitively.
    disclosed_ai: on the first turn the answer contains one of AI_DISCLOSURES; True on later turns.
    has_disclaimer: acme.data.DISCLAIMER appears verbatim (case-sensitive).
    passed: both True."""
```

This is deliberately separate from `acme/rubric.py`. The spec's rubric has exactly five facts, and these two rules are checked beside it. Rule 6 is a legal requirement (EU AI Act Article 50), so it deserves its own named test.

### Tests: `tests/test_protocol.py`

- These use `tests/fixtures/reviewer_cases.json` and must not edit it.
- `good-acme01` passes both checks.
- `bad-promise` fails both.
- `fail-no-booking` fails `has_disclaimer`.
- `first_turn=False` with no disclosure still gives `disclosed_ai is True`.
- A disclaimer with altered capitals fails, which proves the case-sensitive match.
- Every reviewer case with `expected_pass: true` also passes `check_protocol`. This keeps the good examples honest.

---

## Definition of done

- `uv run pytest -q` passes with more than 67 tests, and nothing is skipped other than the opt-in `llm` test.
- The new folders exist: `skills/` (2 SKILL.md files), `agents/` (7 TOML files), `acme/agents.py` and `acme/protocol.py`.
- `docs/TUTORIAL.md` has new chapters for skills, agent definitions and protocol checks, and every `file:line` link in it points at the right line.
- There is one commit per task.
- No push.

## Out of scope for this chunk

kagent manifests, running agents against a model, the web app, Keycloak, and any change to tool behaviour.
