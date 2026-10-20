# Building the Acme Air core: a tutorial

This tutorial explains the ideas behind each piece of the Acme Air core, in the order it was built. Each chapter covers one task from [tonight/BUILD_SPEC.md](../tonight/BUILD_SPEC.md) and follows the same pattern:

- **The idea**: the concept in plain terms
- **Why it matters**: what goes wrong without it, especially once AI agents are involved
- **See it in the code**: where to look
- **Try it**: a one-line experiment you can run from the repo root

Every chapter assumes you are in the repo root and have run `uv sync`.

---

## Chapter 0: The working method

### Test first, then build

**The idea.** For every piece, the test file is written before the code. You run the test, watch it fail, then write just enough code to make it pass. This is test-driven development (TDD).

**Why it matters.** A test that has never failed proves nothing. It might be checking the wrong thing, or nothing at all. Watching it fail first proves the test can actually catch a mistake. The spec goes further (Section 0): the tests and the rubric *define* what correct means, and the code is only the implementation.

**See it in the code.** Every task has a matching file in [tests/](../tests/). Read the test before the code it tests, because the test is the specification in runnable form.

**Try it.**

```bash
uv run pytest -q
```

### Pin everything

**The idea.** The project pins Python to 3.12 (`.python-version`), and `uv.lock` records the exact version and a cryptographic hash of every package.

**Why it matters.** Your Mac's default Python is 3.15, which is too new for some packages. More importantly, the spec's ground rules (Section 7) cite a real attack: in March 2026, malicious versions of a popular gateway package were published to PyPI. A lockfile with hashes means you install exactly the bytes you tested, not whatever was published most recently.

**See it in the code.** [pyproject.toml](../pyproject.toml) declares what you depend on, and [uv.lock](../uv.lock) records exactly what you got.

---

## Chapter 1: Synthetic data and named errors

### One source of truth

**The idea.** Every fact about the fictional airline lives in one file, [acme/data.py](../acme/data.py): bookings, flights, bags, loyalty accounts and fare rules. Nothing else in the code contains airline facts.

**Why it matters.** An AI agent will confidently invent a plausible fare rule or flight number if it can. The defence is that every fact an agent states must come from a tool, and every tool reads from this one place. When you later ask "did the agent hallucinate that?", you have one file to check against.

**See it in the code.** The ACME01 booking at [data.py:11](../acme/data.py:11) is the template. Every booking has exactly the same keys, and [test_data.py:8](../tests/test_data.py:8) enforces that. A consistent shape means tools and agents never have to guess whether a field exists.

### Data that is deliberately imperfect

**The idea.** Some data is shaped on purpose to test the code around it:

- `ALTERNATIVES` is stored out of time order, so the search tool must prove it sorts.
- `FARE_RULES` has no class Z, so the fares tool must handle a missing class honestly.
- `ACME01` is marked `time_critical: True`, so the reviewer can check for an urgency warning.

**Why it matters.** Perfect test data hides bugs. If the alternatives were already sorted, a tool that forgot to sort would still pass its test.

### Named errors

**The idea.** [acme/errors.py](../acme/errors.py) defines a family of errors such as `BookingNotFound` and `FareClassNotFound`, all children of one parent, `ToolError`.

**Why it matters.** A named error says *what* went wrong, and its message says *what to do next*. An agent that receives "Fare class Z not in fare table. Call list_fare_classes for valid classes." can recover. An agent that receives a blank failure tends to guess. The shared parent also lets later code catch "any tool error" in one place.

**Try it.**

```bash
uv run python -c "from acme.data import BOOKINGS; print(BOOKINGS['ACME01']['situation'])"
```

---

## Chapter 2: Tools

### Look it up, raise if missing, return a copy

**The idea.** Every tool follows the same three steps:

1. **Look it up** in `data.py`.
2. **Raise a named error if it is missing.** Never fall back to a guess or a default.
3. **Return a copy** of the record, never the original.

```python
def get_booking(pnr: str) -> dict:
    booking = BOOKINGS.get(pnr.upper())          # 1. look it up
    if booking is None:
        raise BookingNotFound(f"Booking {pnr} not found")   # 2. raise if missing
    return deepcopy(booking)                     # 3. return a copy
```

**Why the copy matters.** In Python, handing out a dictionary hands out a *reference* to the same object, not a fresh one. If a tool returned `BOOKINGS["ACME01"]` directly and some later code (or an agent's tool-handling code) appended a passenger to the result, it would be changing the airline's "database" itself. Every later call would then see the corrupted booking. `deepcopy` makes a fully independent duplicate, including the nested lists, so callers can do anything they like to their copy and the source stays clean.

**Why "raise if missing" matters.** The spec's first protocol rule is "never invent booking data". A tool that returned an empty booking or a default would let an agent carry on as if the booking existed. Raising stops that and forces the agent to say "I can't find that booking".

**See it in the code.** [ops.py:9](../acme/tools/ops.py:9) shows the pattern, and every other tool repeats it. [test_tools.py:17](../tests/test_tools.py:17) proves the copy: it adds an "Intruder" passenger to the returned booking and checks the original still has 3.

**Try it.** See that the original survives:

```bash
uv run python -c "
from acme.tools.ops import get_booking
from acme.data import BOOKINGS
b = get_booking('ACME01'); b['passengers'].clear()
print('copy:', b['passengers'], '| original:', BOOKINGS['ACME01']['passengers'])"
```

### Forgiving input, strict output

**The idea.** Tools accept `acme01` or `ACME01` (they call `.upper()` first), but they always return data in one exact shape.

**Why it matters.** Models and passengers are inconsistent about capitals. Being lenient about input avoids pointless failures, and being strict about output keeps everything downstream predictable.

### Planted defects

**The idea.** Two tools are broken on purpose, so that later parts of the lab have something real to find:

- **The slow tool.** [baggage.py](../acme/tools/baggage.py) sleeps 4.5 seconds before answering, to simulate a slow legacy system. A comment at the top says it must not be fixed.
- **The failing tool.** [fares.py](../acme/tools/fares.py) raises an error for class Z. The error names the missing class and points to `list_fare_classes`.

**Why it matters.** In Part 3 of the lab, participants use tracing to find where time goes. The stall gives them a clear target. The class Z failure tests whether an agent reports a failure honestly instead of inventing a rule to cover it. A failed tool call that the agent reports truthfully is a healthy signal, not a bug.

**Try it.** Watch the stall show up in the slowest tests:

```bash
uv run pytest --durations=3 -q
```

---

## Chapter 3: The reviewer

### Facts first, score second

**The idea.** Reviewing an answer is split into two separate jobs:

1. **Extract the facts.** [rubric.py](../acme/rubric.py) reads an answer and answers 5 yes/no questions: did it use the booking, offer options, flag anything urgent, give a next step, and promise compensation too early?
2. **Score the facts.** [review.py](../acme/tools/review.py) turns those 5 answers into a score and a pass or fail.

**Why it matters.** The spec says the reviewer "never computes the score itself" and the weights "live in the tool". Keeping the weights in one place means the same facts always produce the same score, whoever or whatever extracted them. Later, an AI reviewer agent will do the extracting, but it still cannot fiddle the maths.

### Deterministic, not judged

**The idea.** The rubric matches exact words only, ignoring capitals. It looks for "option 1" and "option 2", "next step", "urgent" and so on. There is no AI deciding whether an answer "feels" helpful.

**Why it matters.** An AI judge can give the same answer different scores on different runs, so a test suite built on it passes one minute and fails the next. Exact-word matching is boring, but it is repeatable and you can explain every mark. [test_reviewer.py:54](../tests/test_reviewer.py:54) scores the same answer three times and requires identical results.

### Weights, threshold and a hard fail

**The idea.** Each fact carries a weight (0.25, 0.25, 0.20, 0.15, 0.15), and an answer passes at 0.90 or above. Promising compensation before eligibility is confirmed sets the score to 0, whatever else the answer got right.

**Why it matters.** Because the smallest weight is 0.15, missing any single fact drops the score below 0.90. So in practice a pass needs all five. The hard fail exists because a premature compensation promise is the most expensive mistake an airline agent can make, and no amount of politeness should outweigh it.

**See it in the code.** The weights are at [review.py:8](../acme/tools/review.py:8) and the hard fail is at [review.py:34](../acme/tools/review.py:34). The careful version, "you may be entitled to compensation, subject to eligibility", passes because of the caveat check at [rubric.py:35](../acme/rubric.py:35).

### Proving it both ways

**The idea.** [reviewer_cases.json](../tests/fixtures/reviewer_cases.json) holds 11 sample answers labelled pass or fail. The suite checks that bad answers fail *and* good answers pass.

**Why it matters.** A reviewer that fails everything looks strict but is useless, and one that passes everything is worse. Only testing both directions shows it can tell good from bad.

### The matching trap

**The idea.** The `trap-vocabulary` answer does everything right but says "First choice" and "Second choice" instead of "Option 1" and "Option 2". It fails.

**Why it matters.** This is the downside of exact-word matching, and the spec's Part 2 makes participants experience it. The quality score can move while the agent's behaviour does not change at all, just because of wording. [test_reviewer.py:49](../tests/test_reviewer.py:49) records that vocabulary is the *only* reason this answer fails, so the trap is documented instead of hidden.

**Try it.**

```bash
uv run python -c "
from acme.rubric import extract_facts
from acme.tools.review import score_service_review
print(score_service_review(**extract_facts('Becker, ACME01: urgent. Option 1 or Option 2. Next step: pick one.', 'ACME01')))"
```

Then change "Option 1 or Option 2" to "plan A or plan B" and run it again.

---

## Chapter 4: Routing

### The escalation table

**The idea.** [routing.py](../acme/routing.py) holds a table mapping each desk to the keywords it owns. A question goes to the first desk whose keyword appears in it. If nothing matches, it goes to the duty manager.

**Why it matters.** This is the spec's protocol rule 5 written as code. It also becomes the baseline: when an AI router is built later, you can measure whether it actually beats a simple keyword list.

### Order is logic

**The idea.** The table is checked top to bottom, and customer relations comes first.

**Why it matters.** "I want compensation for my cancelled flight" contains both "compensation" and "cancel". It belongs with customer relations, not rebooking, so that desk has to be checked first. Reordering the table changes behaviour without changing a single keyword, which makes the order easy to break and worth testing.

### Word boundaries

**The idea.** Keywords must start at the beginning of a word. "bag" matches "bags", but "press" does not match "express".

**Why it matters.** Plain substring matching misroutes on accidental fragments inside longer words. The boundary check at [routing.py:26](../acme/routing.py:26) prevents that, and [test_routing.py:24](../tests/test_routing.py:24) proves it.

### Accepted-answer sets

**The idea.** Each routing case lists the desks allowed to take it, not just one. "ACME01: what happens to our bags now the connection is cancelled?" accepts both rebooking and baggage.

**Why it matters.** Some questions are genuinely ambiguous. Forcing a single right answer would make the test fail or pass depending on small routing changes. The spec calls this "flapping". The accepted set records the honest truth: either desk is fine.

### Where keywords run out

**The idea.** "I missed my connection" does not match the keyword "missed connection", because of the word "my" in between.

**Why it matters.** Real passengers phrase things loosely. Keyword routing is predictable but brittle. That trade-off is exactly why the lab later compares it with an AI router, on the same questions.

**Try it.**

```bash
uv run python -c "
from acme.routing import route_by_keywords
for q in ['My bags are lost', 'I missed my connection', 'Complaint: cancelled flight']:
    print(q, '->', route_by_keywords(q))"
```

---

## Chapter 5: MCP servers

### A standard plug socket for tools

**The idea.** The Model Context Protocol (MCP) is a standard way for an AI agent to discover and call tools. An MCP server advertises a list of tools, each with a name, a description and typed inputs. Any agent that speaks MCP, such as kagent, Goose or Claude, can connect, read that list and call the tools. It doesn't need to know they are written in Python.

**Why it matters.** Without a standard, every agent framework needs its own glue code for every tool. With MCP, you write the tools once and plug them into anything. For this lab there is a second reason, from the spec (Section 5.5): tool calls that travel over MCP can pass through a gateway, and the gateway can check *who* is calling *which* tool. Tools embedded inside an agent are invisible to the gateway, so they can't be secured that way. That's the foundation for all of Part 4.

### Thin wrappers

**The idea.** Each server file is only a wrapper. It imports the tested tool and hands the call straight through:

```python
@mcp.tool()
def check_fare_rule(fare_class: str) -> dict:
    """...description the agent reads..."""
    return fares.check_fare_rule(fare_class)
```

**Why it matters.** All the logic lives in `acme/tools/`, where it is tested directly and quickly. The server adds no behaviour of its own, so there is nothing new to go wrong in it. If a tool misbehaves, you know the bug is in the tool, not the plumbing.

### Five servers, eight tools

**The idea.** The tools are grouped by the desk that owns them:

| Server | Tools |
|---|---|
| acme-ops | get_booking, get_flight_status, search_alternative_flights |
| acme-baggage | trace_bag |
| acme-loyalty | get_loyalty_account |
| acme-fares | check_fare_rule, list_fare_classes |
| acme-review | score_service_review |

**Why it matters.** Each agent only gets the servers its desk needs. The baggage agent cannot even see the fares tools, which is the principle of least privilege: an agent can't misuse a tool it doesn't have.

### The description is the routing signal

**The idea.** A tool's docstring becomes the description the agent reads when deciding which tool to call. These descriptions are written as **routing triggers**: they list the topics and keywords the tool owns ("Use for: bag, baggage, luggage, suitcase, bag not arrived").

**Why it matters.** The model picks tools by reading descriptions, so a vague description ("handles bags") produces vague tool choices. The spec (Part 1) makes the same point about agent descriptions: write them as routing triggers, not personality blurbs. Descriptions can also carry instructions, which is how the fares tool tells the agent to "report the missing class, never invent a rule". [test_servers.py:31](../tests/test_servers.py:31) checks that no tool ships without a real description.

### Errors become messages, not crashes

**The idea.** When a tool raises an error, the MCP server doesn't crash. It returns a normal response marked `isError: true`, carrying the error's message. The agent reads that message like any other tool output.

**Why it matters.** This is why Chapter 1's named errors with helpful messages pay off. Asking for class Z gives the agent "Fare class Z not in fare table. Call list_fare_classes for valid classes.", which it can act on. [test_servers.py:42](../tests/test_servers.py:42) proves the planted failure survives the trip through the server with its message intact.

### Two ways to call a server

**The idea.** The tests call each server *in-process*: they import it and call `mcp.list_tools()` directly, which is fast. A real agent instead starts the server as a *separate process* and talks to it over stdin and stdout (the "stdio" transport). That's what `if __name__ == "__main__": mcp.run()` at the bottom of each file is for.

**Why it matters.** In-process tests prove the wiring. A separate-process check proves an outside agent can actually connect. Both were done for this chapter.

**Try it.** Open the MCP Inspector, a web page for poking at a server by hand:

```bash
npx @modelcontextprotocol/inspector uv run python -m servers.fares_server
```

In the Inspector, connect, open Tools, call `check_fare_rule` with `B`, then with `Z`, and compare the two results.

---

## Chapter 6: An AI router, measured

### Same question, two routers

**The idea.** [acme/llm_router.py](../acme/llm_router.py) asks the local model (qwen3.5:9b through Ollama) to name the desk for a question. It is measured against Chapter 4's keyword router on exactly the same cases, so the comparison is fair.

**Why it matters.** "The AI is better" is a claim, and a claim needs evidence. A simple baseline tells you whether the expensive, slower, less predictable option actually earns its place. If the keyword list scored the same, you'd keep the keyword list.

### The model names a desk, nothing else

**The idea.** The system prompt describes each desk as a routing trigger ("baggage: delayed, damaged or lost bags") with its keywords, then says "Do not answer the question" and asks for JSON only: `{"desk": "..."}`. The parser accepts only the six known desk names. Anything else, including a made-up desk like `lost_property`, comes back as `"invalid"`.

**Why it matters.** This is the "never guess" rule from Chapter 2 again. A model can hallucinate a desk that doesn't exist. Reporting `"invalid"` makes that visible in the score, instead of quietly sending the passenger somewhere random.

### Robust parsing

**The idea.** Ollama 0.40 can't force JSON output for qwen3.5. It replied `"structured output is unavailable"`, which showed up as an HTTP 501 error. So the router asks for JSON in the prompt, and the parser picks the first `{...}` object out of whatever comes back, even if the model wraps it in a code fence or adds chatter.

**Why it matters.** Small models are inconsistent about output format. Parsing tolerantly while *validating* strictly gets the best of both. [test_llm_router.py:35](../tests/test_llm_router.py:35) tests the fenced case.

### Offline tests and live tests

**The idea.** Most tests in [test_llm_router.py](../tests/test_llm_router.py) never call the model. They check prompt building and parsing, so they run in milliseconds every time. The one live test is marked `llm` and only runs when you set `ACME_LLM=1`.

**Why it matters.** A test suite that needs a running model is slow, noisy (your fans) and fails whenever Ollama is off. Splitting them keeps the everyday suite fast and reliable, and the expensive measurement stays opt-in.

### The result

| Case set | qwen3.5:9b | Keywords |
|---|---|---|
| Keyword-friendly (n=12) | 12/12 | 12/12 |
| Paraphrases (n=8) | 8/8 | 0/8 |

**What it shows.** On questions that happen to use the keywords, both routers are perfect. That tie was partly because the cases were written with the keyword list in mind. On natural phrasing ("miles" not "points", "dog" not "pet", "scrapped" not "cancelled"), the keyword router sends everything to the duty manager, while qwen gets all eight.

**Read it carefully.** These are small samples (n=12 and n=8), with one model at temperature 0. The spec's Part 3 rule applies: always show the sample size beside a score. This is a strong signal, not a proven rate.

### The test set can flatter you

**The idea.** The first comparison was a 12/12 tie, which looked like "keywords are as good as AI". The cause was the test set: the cases were written by someone who knew the keywords, and one question was even reworded to match them.

**Why it matters.** This is a quiet trap in evaluation. If the people writing the test know how the system works, they tend to write cases it passes. The fix is a second set written to avoid the system's vocabulary, which is what [routing_paraphrase_cases.json](../tests/fixtures/routing_paraphrase_cases.json) is. [test_llm_router.py:51](../tests/test_llm_router.py:51) records the keyword router's 0/8 as a known limitation, so it can't be forgotten.

**Try it.** With Ollama running:

```bash
ACME_LLM=1 uv run pytest -m llm -s -q
```

Then try your own phrasing:

```bash
uv run python -c "
from acme.llm_router import route_with_llm
print(route_with_llm('My suitcase smells of fish and the handle is gone'))"
```

---

## Chapter 7: Agent skills

### A skill is a rulebook in a file

**The idea.** A skill is a folder holding one `SKILL.md` file: a short header (`name` and `description`) followed by plain markdown instructions. An agent loads the skill and follows it. [service-recovery-protocol](../skills/service-recovery-protocol/SKILL.md) holds the seven service rules from the spec. Every passenger-facing agent applies it.

**Why it matters.** Without a skill, each agent's system message would repeat the same rules, and the copies would drift apart. One shared file means one place to change a rule.

### Written to match the reviewer

**The idea.** Rule 3 says to label options "Option 1" and "Option 2". Rule 4 says to write "subject to eligibility". Those exact words are what the reviewer in Chapter 3 looks for (see [rubric.py:11](../acme/rubric.py:11)). The disclaimer in rule 7 is copied word for word from `DISCLAIMER` in [data.py](../acme/data.py).

**Why it matters.** The reviewer is a literal keyword matcher, not a judge with taste. An agent that follows the skill therefore passes the rubric by construction, and a skill that paraphrased the rules would not.

### A second skill, for the reviewer

**The idea.** [service-review-rubric](../skills/service-review-rubric/SKILL.md) lists the five facts and their keywords. It tells the service_reviewer agent to pass five true or false values to `score_service_review` and never to work out the score itself.

**Why it matters.** The model reads and extracts. The code does the arithmetic. That split is what keeps the same answer scoring the same every time.

### The documents are tested against the code

**The idea.** [test_skills.py](../tests/test_skills.py) checks that each skill's `name` matches its folder, that the protocol contains the disclaimer verbatim and every desk name from the escalation table, and that the rubric skill contains every keyword from the constants in `acme/rubric.py`. The small frontmatter parser lives in the test file at [test_skills.py:13](../tests/test_skills.py:13).

**Why it matters.** A document that describes code goes stale quietly. Here, if someone changes a keyword in code, a test fails until the skill is updated. Prose and code stay in sync because a machine checks them.

**Try it.**

```bash
uv run pytest tests/test_skills.py -q
```

Then edit a keyword in `acme/rubric.py` (and put it back afterwards) to watch the sync test fail.

---

## Chapter 8: Agent definitions

### An agent is a small config file

**The idea.** Each of the seven agents is one TOML file in `agents/`, using a format we invented for this lab (it is not kagent YAML; a later chunk converts these once kagent is installed). A file holds six fields: `name`, `description`, `skills`, `tools`, `delegates` and `system_message`. For example, [fares.toml](../agents/fares.toml) names one skill, two tools and no delegates.

**Why it matters.** An agent is not magic. It is a name, a job description, some rulebooks, some tools and a prompt. Keeping that in a plain file means you can read it, diff it and test it without running a model.

### The description is a routing trigger

**The idea.** The `description` field is what an orchestrator reads to decide who gets a question. So it lists the topics and keywords the agent owns, taken from the escalation table at [routing.py:11](../acme/routing.py:11), instead of describing a friendly personality. See the fares description at [fares.toml:2](../agents/fares.toml:2).

**Why it matters.** An orchestrator choosing between agents sees only their descriptions. A vague description such as "a helpful travel expert" gives it nothing to match on, so questions get misrouted.

### One tool, one owner

**The idea.** There are 8 tools across the 5 servers, and each is assigned to exactly one agent. `tools` entries read `<server name>/<tool name>`, for example `acme-fares/check_fare_rule`. The duty manager holds the booking and flight-status tools, [customer_relations.toml](../agents/customer_relations.toml) holds none at all, and [service_reviewer.toml](../agents/service_reviewer.toml) holds only the scoring tool.

**Why it matters.** Clear ownership keeps each agent's job small and makes it obvious which agent to blame when an answer is wrong. An agent with every tool tends to use the wrong one.

### A planted flaw in the orchestrator

**The idea.** [duty_manager.toml](../agents/duty_manager.toml) contains a deliberate mistake, marked by a comment at [duty_manager.toml:6](../agents/duty_manager.toml:6). The last line of its system message, at [duty_manager.toml:12](../agents/duty_manager.toml:12), tells it to answer directly whenever it can instead of delegating. An orchestrator that does so skips the specialist desks.

**Why it matters.** This is the lab's exercise: find the sentence, remove it, and measure whether routing improves. Do not remove it yet. Fixing it is only meaningful if you can show the before and after.

### Open question: where does the reviewer run?

service_reviewer is not a delegate of the duty manager, because it scores answers and never resolves a case. Whether it runs inside the agent graph or from the evaluation harness outside it is not decided yet. That is settled in Part 2, so for now it is an open question.

**Try it.**

```bash
cat agents/fares.toml
uv run python -c "import tomllib; print(tomllib.load(open('agents/duty_manager.toml','rb'))['delegates'])"
```

---

## Chapter 9: Loading and checking agents

### One function reads them all

**The idea.** [load_agents](../acme/agents.py:14) reads every `.toml` file in `agents/` and returns a dictionary keyed by agent name. It refuses a file that lacks any of the six fields listed in [REQUIRED_KEYS](../acme/agents.py:11), or whose `name` differs from its file name (so `fares.toml` must say `name = "fares"`). The error message names the file, so a typo is easy to find.

**Why it matters.** A config file that is silently wrong is worse than one that fails loudly. Checking the shape at load time means every later step can trust what it reads.

### Tests that connect the files to everything else

**The idea.** [test_agents.py](../tests/test_agents.py) compares the agent files with the real servers and the routing table. It asks each server which tools it offers and checks that every `server/tool` entry exists ([test_agents.py:58](../tests/test_agents.py:58) checks that all 8 tools have exactly one owner). It checks that every delegate is a real agent, that each skill folder exists, and that each desk's description contains keywords from the escalation table.

**Why it matters.** An agent that names a tool which does not exist fails only when a passenger asks the question. These tests catch it in under a second, with no model involved. They also catch drift: add a ninth tool to a server and the ownership test fails until some agent claims it.

### A test that guards the flaw

**The idea.** [the planted-flaw test](../tests/test_agents.py:98) checks that the duty manager's self-answer sentence is still present. It looks odd to test for a mistake, but the flaw is a deliberate part of the lab and must not be fixed by accident.

**Why it matters.** When participants remove the sentence in Part 1, this test will fail. That is intended: it is the signal that the before-and-after measurement has begun. The test's docstring says so, to stop a well-meaning tidy-up.

**Try it.**

```bash
uv run pytest tests/test_agents.py -q
uv run python -c "from acme.agents import load_agents; print(sorted(load_agents()))"
```

---

## Chapter 10: Protocol checks

### Two rules the rubric does not cover

**The idea.** The reviewer in Chapter 3 scores five facts. Rules 6 and 7 of the service protocol are not among them: tell the passenger they are talking to an AI assistant, and end with the fixed disclaimer. [check_protocol](../acme/protocol.py:13) checks both and returns `disclosed_ai`, `has_disclaimer` and `passed`. The disclosure phrases are listed in [AI_DISCLOSURES](../acme/protocol.py:10).

**Why it matters.** Telling people they are talking to an AI is a legal requirement in the EU (AI Act, Article 50), so it gets its own named check instead of being hidden as a sixth rubric fact. Keeping it separate also leaves the rubric at exactly five facts, as the spec says.

### Literal matching, with one exception for later turns

**The idea.** The disclosure check is case-insensitive: "AI ASSISTANT" counts. The disclaimer check is case-sensitive and must match `DISCLAIMER` from [data.py](../acme/data.py:5) word for word, so a shouting or re-capitalised copy fails ([test_protocol.py:39](../tests/test_protocol.py:39)). The disclosure is only needed on the first turn. With `first_turn=False`, `disclosed_ai` is always True ([test_protocol.py:29](../tests/test_protocol.py:29)).

**Why it matters.** Like the rubric, this is plain string matching with no model judging, so the same answer always gets the same result. Being strict about the disclaimer means the legal text cannot be quietly reworded.

### Keeping the good examples honest

**The idea.** [test_every_good_case_passes_protocol](../tests/test_protocol.py:47) runs `check_protocol` over every case in `reviewer_cases.json` marked as a good answer. The fixture is read, never edited.

**Why it matters.** If someone adds a "good" example that forgets the disclosure or disclaimer, this test fails. The examples that teach what a good answer looks like must themselves follow every rule.

**Try it.**

```bash
uv run pytest tests/test_protocol.py -q
uv run python -c "from acme.protocol import check_protocol; print(check_protocol('Hello.'))"
```

---

## Chapter 11: One review function

### One scorer, wrapped once

**The idea.** Scoring an answer takes three existing steps: [extract_facts](../acme/rubric.py:18) pulls out the five facts, [score_service_review](../acme/tools/review.py:18) turns them into a score, and [check_protocol](../acme/protocol.py:13) checks the AI disclosure and the disclaimer. [review_answer](../acme/scoring.py:20) calls all three and returns everything in one dict: `facts`, `score`, `protocol`, `hard_failures` and `soft_failures`. It adds no scoring rules of its own.

**Why it matters.** Later chapters review answers in two places: live, before a passenger sees them, and afterwards, in a batch report. If each place had its own copy of the scoring, the copies would drift apart and the same answer would pass in one place and fail in the other. A single function means there is only one thing to trust and one thing to fix.

### Hard failures and soft failures

**The idea.** Not every failure is equally serious. The three [HARD_FAILURES](../acme/scoring.py:13) are a compensation promise made before eligibility is confirmed, a missing disclaimer and a missing AI disclosure. These are safety and legal problems. Everything else the rubric can fail, such as the option labels or the next step, is a soft failure: it is recorded but never blocks.

**Why it matters.** The rubric matches literal words. An answer can offer two perfectly good choices without writing "option 1" and "option 2", and the rubric would mark it down. That is the matching trap. If the live check blocked on it, a correct answer would be stopped. Blocking only on hard failures keeps the live check safe, while soft failures still show up in the later report. The trap case is tested as a soft failure only ([test_scoring.py:30](../tests/test_scoring.py:30)), and the bad promise trips all three hard failures in order ([test_scoring.py:26](../tests/test_scoring.py:26)).

### Proving there is one path

**The idea.** [test_review_uses_the_one_scoring_path](../tests/test_scoring.py:49) runs for every fixture case and checks that `review_answer` returns exactly what calling `extract_facts`, `score_service_review` and `check_protocol` by hand returns. The `first_turn=False` case ([test_scoring.py:43](../tests/test_scoring.py:43)) shows the disclosure rule relaxing on later turns.

**Why it matters.** This is a parity test. If someone ever adds a second copy of the scoring logic, or changes the wrapper so it disagrees with the originals, this test fails.

**Try it.**

```bash
uv run pytest tests/test_scoring.py -q
uv run python -c "from acme.scoring import review_answer; print(review_answer('Hello.', 'ACME01')['hard_failures'])"
```

---

## Chapter 12: The in-graph gate

### A check that always runs

**The idea.** Between a drafted answer and the passenger sits a small piece of code, [gate_answer](../acme/gate.py:24). It calls [review_answer](../acme/scoring.py:20) from Chapter 11 and makes one of three decisions. `deliver`: there are no hard failures, so the answer goes out unchanged. `retry`: there is a hard failure and this is an early attempt, so the answer is held back and the agents try again. `handoff`: there is still a hard failure on the last attempt, so the passenger gets a fixed safe message instead.

**Why it matters.** The gate is code, not the service_reviewer agent, on purpose. An instruction such as "call the reviewer last" only works if the model chooses to obey it, and that is exactly the weakness planted in `agents/duty_manager.toml`. Code does not forget or get talked out of it. The gate also blocks only on hard failures, so the matching trap from Chapter 11 can never stop a correct answer ([test_gate.py:25](../tests/test_gate.py:25)).

### Retry once, then a human

**The idea.** [MAX_ATTEMPTS](../acme/gate.py:14) is 2. A bad promise on attempt 1 gives `retry` with no text to deliver ([test_gate.py:31](../tests/test_gate.py:31)). The same answer on attempt 2 gives `handoff` ([test_gate.py:37](../tests/test_gate.py:37)). An attempt number below 1 is a mistake in the caller, so it raises `ValueError` ([test_gate.py:48](../tests/test_gate.py:48)).

**Why it matters.** Models sometimes produce a good answer on a second try, so one retry is cheap. But looping forever is worse than failing, so after the limit the case goes to a person.

### The safe fallback has to be safe itself

**The idea.** [HANDOFF_MESSAGE](../acme/gate.py:16) says the passenger is talking to an AI assistant, says a member of the Acme Air team will take over, names the next step, promises nothing, and ends with `DISCLAIMER` joined on from [data.py](../acme/data.py:5) rather than retyped. [A test](../tests/test_gate.py:43) runs it through the same review and requires no hard failures.

**Why it matters.** A safety net that breaks the rules it enforces would be useless. Because the fallback is checked by the same scorer, changing its wording in a way that breaks a rule fails a test.

**Try it.**

```bash
uv run pytest tests/test_gate.py -q
uv run python -c "from acme.gate import gate_answer; print(gate_answer('You are entitled to EUR 600.', 'ACME01', attempt=2)['decision'])"
```

---

## Chapter 13: Post-run evals

### Checking the checker

**The idea.** The fixture file holds eleven labelled answers, each marked as one that should pass or should not. [run_eval](../acme/evals.py:18) scores every one with `review_answer` from Chapter 11 and asks `gate_answer` from Chapter 12 what the live gate would do on a first attempt. It returns one record per case, in the same order as the fixture, plus a summary of five counts: `n` (cases scored), `agreed` (the score's pass or fail matches the label), `passed`, `hard_failed` (cases with at least one hard failure) and `delivered` (cases the live gate would let through).

**Why it matters.** A reviewer you never test is just another thing you hope works. Running it over answers whose correct verdict you already know tells you how far to trust it. The evals add no scoring rules of their own, so they measure the same code the passengers' answers go through ([test_evals.py:39](../tests/test_evals.py:39) checks the scores match).

### Two verdicts that differ on purpose

**The idea.** The vocabulary-trap answer is good but does not use the exact words "option 1". The post-run score marks it down, yet the live gate delivers it ([test_evals.py:29](../tests/test_evals.py:29)). The bad promise is marked down and the gate asks for a retry ([test_evals.py:35](../tests/test_evals.py:35)).

**Why it matters.** The post-run report is strict so you can see wording problems and improve the agents. The live gate is lenient so a correct answer is never blocked. Seeing both verdicts side by side in one table shows that trade-off clearly.

### A report you can open anywhere

**The idea.** [render_html](../acme/evals.py:65) writes a single self-contained page: the summary first, then one row per case. Each rate is written with its sample size, such as `11/11 (n=11)`, so nobody mistakes eleven cases for proof of anything broad. It uses no scripts, no links and no external styles, and all case text is escaped ([test_evals.py:54](../tests/test_evals.py:54)), so a strange case id cannot inject markup.

**Why it matters.** A report that pulls in outside resources can break or leak when opened offline or shared. Showing the sample size next to every score keeps the numbers honest.

**Try it.**

```bash
uv run pytest tests/test_evals.py -q
uv run python -m acme.evals --html eval.html   # then open eval.html in a browser
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'acme'` outside pytest

**What is happening.** uv installs this project by writing a small pointer file, `.venv/lib/python3.12/site-packages/_editable_impl_acme_lab.pth`, which tells Python where the `acme` code lives. On macOS that file can end up with the system's *hidden* flag set, and recent Python versions skip hidden `.pth` files as a safety measure. Python then never reads the pointer.

The tests still pass because pytest adds the repo folder to Python's search path itself (`pythonpath = ["."]` in `pyproject.toml`). Commands that load a server *by file path*, like `uv run mcp dev servers/fares_server.py`, don't, so they fail.

Clearing the flag with `chflags nohidden` works briefly, but on this Mac something re-applies it within minutes, so don't rely on it.

**Fix.** Start servers *as modules* from the repo root. With `python -m`, Python searches the current folder, so `acme` is always found, whatever the pointer file is doing:

```bash
uv run python -m servers.fares_server
```

For the MCP Inspector, wrap that same command:

```bash
npx @modelcontextprotocol/inspector uv run python -m servers.fares_server
```

Use the same `python -m servers.<name>` form when configuring Goose or kagent to start a server.
