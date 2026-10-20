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
uv run mcp dev servers/fares_server.py
```

In the Inspector, connect, open Tools, call `check_fare_rule` with `B`, then with `Z`, and compare the two results.
