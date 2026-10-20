# Acme Air core: build spec for qwen3.5:9b

Scope: the pure-Python core of the Acme Air lab. That means synthetic data, 8 tools (with 2 planted defects), a deterministic reviewer, a keyword routing baseline, 5 MCP servers and a pytest contract. There is no Kubernetes, no gateway and no LLM agents. Later parts of the lab point kagent at these servers.

How to use this file: each task below is one fresh chat. Paste **Global rules**, then the task section, then the current contents of any file the task imports. First ask for the test file, then for the implementation.

---

## Global rules (paste at the top of every prompt)

```
You are implementing part of a Python 3.12 project managed with uv.
Rules:
- Dependencies: mcp[cli] and pytest only. Standard library otherwise.
- Tools are pure functions in acme/tools/*.py. MCP servers in servers/ only wrap them.
- Return plain dict or list[dict]. Return copies (copy.deepcopy) of data, never the original objects.
- Errors: raise a subclass of acme.errors.ToolError with the exact message given in the spec.
- Never invent data. Everything comes from acme/data.py.
- Write ONE file per answer. Output the full file, no placeholders, no "..." elision.
- Do not change test files to make them pass.
```

## Layout

```
pyproject.toml
acme/__init__.py
acme/data.py
acme/errors.py
acme/tools/__init__.py
acme/tools/ops.py        # get_booking, get_flight_status, search_alternative_flights
acme/tools/baggage.py    # trace_bag            (PLANTED DEFECT: 4.5 s stall)
acme/tools/loyalty.py    # get_loyalty_account
acme/tools/fares.py      # check_fare_rule      (PLANTED DEFECT: no class Z), list_fare_classes
acme/tools/review.py     # score_service_review (weights live here only)
acme/rubric.py           # extract_facts
acme/routing.py          # ESCALATION_TABLE, route_by_keywords
servers/__init__.py
servers/ops_server.py, baggage_server.py, loyalty_server.py, fares_server.py, review_server.py
tests/test_data.py, test_tools.py, test_reviewer.py, test_routing.py, test_servers.py
tests/fixtures/reviewer_cases.json
tests/fixtures/routing_cases.json
```

There are 5 servers and 8 tools. ops has 3, baggage 1, loyalty 1, fares 2, review 1.

## Task 0: project setup (by hand, no model needed)

Create `pyproject.toml` exactly:

```toml
[project]
name = "acme-lab"
version = "0.1.0"
requires-python = ">=3.12,<3.14"
dependencies = ["mcp[cli]>=1.9,<2"]

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["acme", "servers"]

[tool.pytest.ini_options]
pythonpath = ["."]
markers = ["llm: calls local Ollama, run with ACME_LLM=1"]
```

Then:

```
uv python pin 3.12
mkdir -p acme/tools servers tests/fixtures
touch acme/__init__.py acme/tools/__init__.py servers/__init__.py
uv sync
uv run pytest -q
```

Done when `uv run pytest` runs and reports "no tests ran". The `uv.lock` file pins every package with hashes, which covers the spec's "pin and verify" rule. Commit it.

## Task 1: `acme/errors.py` and `acme/data.py`

errors.py:

```python
class ToolError(Exception): ...
class BookingNotFound(ToolError): ...
class FlightNotFound(ToolError): ...
class BagNotFound(ToolError): ...
class LoyaltyAccountNotFound(ToolError): ...
class FareClassNotFound(ToolError): ...
```

data.py holds module-level constants only. There are no functions.

- `NOW = "2026-11-02T10:30"`
- `DISCLAIMER = "Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice."`
- `BOOKINGS`: a dict keyed by PNR. Use exactly this shape for ACME01, and the same keys for every booking:

```python
"ACME01": {
    "pnr": "ACME01",
    "passengers": ["Anna Becker", "Jonas Becker", "Mia Becker"],
    "segments": [
        {"flight_no": "AC101", "origin": "LIS", "destination": "FRA", "departure": "2026-11-02T06:00"},
        {"flight_no": "AC245", "origin": "FRA", "destination": "HEL", "departure": "2026-11-02T10:15"},
    ],
    "fare_class": "M",
    "checked_bags": 3,
    "loyalty_id": None,
    "bag_file_reference": None,
    "pet_in_cabin": False,
    "time_critical": True,
    "owning_desk": "rebooking",
    "situation": "Family of three, Frankfurt connection cancelled, three checked bags",
},
```

- ACME02 differs from ACME01 in these keys:
  - passengers `["Claire Dubois"]`
  - one segment AC330 CDG to ARN, departing 2026-11-01T17:40
  - fare_class "Y"
  - checked_bags 1
  - bag_file_reference "ARNAC10234"
  - time_critical False
  - owning_desk "baggage"
  - situation "Bag delayed on Paris to Stockholm, file reference raised"
- ACME03 differs in these keys:
  - passengers `["Erik Lindqvist"]`
  - one segment AC900 ARN to JFK, departing 2026-11-20T11:00
  - fare_class "Y"
  - checked_bags 1
  - loyalty_id "LY3003"
  - time_critical False
  - owning_desk "loyalty"
  - situation "Gold member asking for a long-haul upgrade"
- ACME04 differs in these keys:
  - passengers `["Sofia Rossi"]`
  - one segment AC512 FCO to MUC, departing 2026-11-12T08:25
  - fare_class "B"
  - checked_bags 0
  - pet_in_cabin True
  - time_critical False
  - owning_desk "fares"
  - situation "Basic fare holder changing dates, pet booked in cabin"
- `FLIGHTS`: a dict keyed by flight_no. Each value is `{"flight_no", "status", "long_haul"}`.
  - AC101: LANDED, False
  - AC245: CANCELLED, False
  - AC330: ARRIVED, False
  - AC900: SCHEDULED, True
  - AC512: SCHEDULED, False
- `ALTERNATIVES`: a dict keyed by `(origin, destination)` tuple. Each value is a list of `{"flight_no", "departure", "via", "seats_available"}`. Put it in this deliberately unsorted order:
  - `("FRA","HEL")`:
    - AC251, 2026-11-02T19:45, via None, 9 seats
    - AC247, 2026-11-02T11:10, via None, 3 seats
    - AC1803, 2026-11-02T14:05, via "MUC", 6 seats
- `BAG_TRACES`: keyed by file reference.
  - "ARNAC10234" maps to:

    ```python
    {"file_reference": "ARNAC10234", "bag_tag": "AC123456",
     "status": "LOCATED_CDG", "forwarded_on": "AC332",
     "delivery_eta": "next day by 18:00"}
    ```
- `LOYALTY`: keyed by loyalty_id.
  - "LY3003" maps to:

    ```python
    {"loyalty_id": "LY3003", "name": "Erik Lindqvist", "tier": "Gold",
     "points": 84200, "long_haul_upgrade_cost": 60000}
    ```
- `FARE_RULES`: keyed by class. Each value is `{"fare_class", "name", "change_fee_eur", "refundable", "pet_in_cabin_fee_eur"}`.
  - Y: "Flex", 0, True, 60
  - J: "Business", 0, True, 60
  - M: "Semi-flex", 75, False, 60
  - B: "Basic", 120, False, 60
  - There is **no Z**. This is deliberate.

`tests/test_data.py` asserts:
- `set(BOOKINGS) == {"ACME01","ACME02","ACME03","ACME04"}`
- every booking has the same set of keys as ACME01
- `"Z" not in FARE_RULES`
- ACME01 has 3 passengers and `checked_bags == 3`
- every segment's flight_no is in FLIGHTS
- DISCLAIMER equals the exact sentence above

## Task 2: tools (`ops.py`, `baggage.py`, `loyalty.py`, `fares.py`)

Exact signatures and errors:

| Function | Returns | Error, with exact message |
|---|---|---|
| `get_booking(pnr: str) -> dict` | deepcopy of BOOKINGS[pnr.upper()] | `BookingNotFound(f"Booking {pnr} not found")` |
| `get_flight_status(flight_no: str) -> dict` | deepcopy of FLIGHTS entry | `FlightNotFound(f"Flight {flight_no} not found")` |
| `search_alternative_flights(origin: str, destination: str) -> list[dict]` | list sorted by `departure` ascending; empty list if none | none |
| `trace_bag(file_reference: str) -> dict` | BAG_TRACES entry, after `time.sleep(4.5)` | `BagNotFound(f"Bag file {file_reference} not found")` |
| `get_loyalty_account(loyalty_id: str) -> dict` | LOYALTY entry | `LoyaltyAccountNotFound(f"Loyalty account {loyalty_id} not found")` |
| `check_fare_rule(fare_class: str) -> dict` | FARE_RULES entry | `FareClassNotFound(f"Fare class {fare_class} not in fare table. Call list_fare_classes for valid classes.")` |
| `list_fare_classes() -> list[str]` | `sorted(FARE_RULES)` which is `["B","J","M","Y"]` | none |

`baggage.py` must start with this comment, verbatim:

```python
# PLANTED DEFECT: trace_bag sleeps 4.5 seconds to simulate a slow legacy
# bag-tracing system. This stall is intentional and must not be fixed.
```

`tests/test_tools.py` asserts:
- `get_booking("acme01")["pnr"] == "ACME01"` (case-insensitive lookup)
- mutating a returned booking does not change `BOOKINGS`
- `get_booking("NOPE99")` raises `BookingNotFound`, and the message contains "NOPE99"
- `get_flight_status("AC245")["status"] == "CANCELLED"`
- `search_alternative_flights("FRA","HEL")` gives flight numbers `["AC247","AC1803","AC251"]`
- `search_alternative_flights("XXX","YYY") == []`
- `trace_bag("ARNAC10234")` returns status "LOCATED_CDG" and takes `>= 4.5` seconds (use `time.perf_counter`)
- `check_fare_rule("B")["change_fee_eur"] == 120`
- `check_fare_rule("Z")` raises `FareClassNotFound`. The message contains "Z" and "list_fare_classes".
- `list_fare_classes() == ["B","J","M","Y"]`
- `get_loyalty_account("LY3003")["tier"] == "Gold"`

## Task 3: rubric and reviewer (`acme/rubric.py`, `acme/tools/review.py`)

All matching is literal, case-insensitive substring matching on `answer.lower()`. No LLM is involved.

`extract_facts(answer: str, pnr: str) -> dict` looks up `BOOKINGS[pnr]` and returns exactly these 5 boolean keys:

| Key | True when |
|---|---|
| `used_booking` | answer contains the PNR, or the lead passenger surname (`passengers[0].split()[-1]`) |
| `offered_options` | answer contains `"option 1"` AND `"option 2"` |
| `flagged_time_critical` | if booking `time_critical` is True: answer contains any of `"urgent"`, `"immediately"`, `"departs in"`. If time_critical is False: always True |
| `cited_next_step` | answer contains `"next step"` |
| `promised_compensation_without_confirmation` | answer contains any of `"entitled to"`, `"refunded you"`, `"will refund"`, `"will compensate"` AND does NOT contain `"subject to eligibility"` |

`extract_facts` never computes a score.

`score_service_review(used_booking: bool, offered_options: bool, flagged_time_critical: bool, cited_next_step: bool, promised_compensation_without_confirmation: bool) -> dict`:

```python
WEIGHTS = {
    "used_booking": 0.25,
    "offered_options": 0.25,
    "flagged_time_critical": 0.20,
    "cited_next_step": 0.15,
    "no_unconfirmed_promise": 0.15,   # earned when promised_compensation_without_confirmation is False
}
PASS_THRESHOLD = 0.90
```

The rules:
- `failed_facts` lists, in WEIGHTS order, the keys that were not earned.
- `score` is `round(sum of earned weights, 2)`.
- If `promised_compensation_without_confirmation` is True, `score = 0.0`. This is a hard fail.
- `passed = score >= PASS_THRESHOLD`.
- `message = "PASS"` if passed, else `"FAIL: " + ", ".join(failed_facts)`.
- It returns `{"score", "passed", "failed_facts", "message"}`.

`tests/fixtures/reviewer_cases.json` is a list of `{"id", "pnr", "answer", "expected_pass", "trap"}`. It needs at least 10 cases, at least 5 passing and at least 5 failing. These three must be included verbatim:

```json
[
  {"id": "bad-promise", "pnr": "ACME01", "trap": false, "expected_pass": false,
   "answer": "You are entitled to EUR 600 and I have refunded you."},
  {"id": "good-acme01", "pnr": "ACME01", "trap": false, "expected_pass": true,
   "answer": "You are chatting with Acme Air's AI assistant. Becker family, booking ACME01: your Frankfurt to Helsinki connection AC245 is cancelled. This is urgent: the next flight departs in 40 minutes. Option 1: AC247 at 11:10, 3 seats available now. Option 2: AC251 at 19:45. Next step: tell me which option and I will rebook all three passengers and your 3 checked bags. Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice."},
  {"id": "trap-vocabulary", "pnr": "ACME01", "trap": true, "expected_pass": false,
   "answer": "You are chatting with Acme Air's AI assistant. Becker family, booking ACME01: AC245 is cancelled. This is urgent: the next flight departs in 40 minutes. First choice: AC247 at 11:10. Second choice: AC251 at 19:45. Next step: tell me which you prefer. Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice."}
]
```

The trap case is correct behaviour scored as a fail, because it uses "first choice" instead of "option 1". That is the spec's matching trap, and it is recorded on purpose.

`tests/test_reviewer.py` asserts:
- For each fixture, `score_service_review(**extract_facts(answer, pnr))["passed"] == expected_pass`. Use `pytest.mark.parametrize` with `ids` from `id`.
- The bad-promise case has `score == 0.0`, and its message starts with `"FAIL:"`.
- The good-acme01 case has `message == "PASS"` and `score == 1.0`.
- Scoring the good answer 3 times gives 3 identical dicts.
- `set(extract_facts(...).keys())` equals the 5 fact names, and there is no `"score"` key.
- A non-time-critical booking (ACME02) gets `flagged_time_critical == True` with no urgency words.

## Task 4: routing baseline (`acme/routing.py`)

```python
ESCALATION_TABLE = [   # checked in this order; first match wins
    ("customer_relations", ["compensation", "complaint", "refund", "lawyer", "legal", "press", "enforcement"]),
    ("fares",              ["fare", "fee", "date change", "pet"]),
    ("loyalty",            ["points", "tier", "gold", "upgrade"]),
    ("baggage",            ["bag", "luggage", "suitcase"]),
    ("rebooking",          ["cancel", "missed connection", "rebook", "disrupt"]),
]
```

`route_by_keywords(question: str) -> str`: for each desk in order, check each keyword with `re.search(r"\b" + re.escape(kw), question, re.IGNORECASE)`. The leading word boundary only, so "bag" matches "bags" but "press" does not match "express". Return the first desk that matches. If nothing matches, return `"duty_manager"`.

`tests/fixtures/routing_cases.json` is a list of `{"id", "question", "accepted"}`. It needs at least 10 cases. These six must be included verbatim. Add at least 4 more, at least one per desk:

```json
[
  {"id": "acme01-cancelled", "question": "ACME01: our connection in Frankfurt was cancelled, what now?", "accepted": ["rebooking"]},
  {"id": "acme02-bag", "question": "ACME02: my bag has not arrived in Stockholm.", "accepted": ["baggage"]},
  {"id": "acme03-upgrade", "question": "ACME03: can I upgrade to business on my long-haul flight?", "accepted": ["loyalty"]},
  {"id": "acme04-date-change", "question": "ACME04: what is the fee to change my travel dates?", "accepted": ["fares"]},
  {"id": "complaint-600", "question": "I demand EUR 600 compensation for this cancelled flight or I go to the national enforcement body and the press.", "accepted": ["customer_relations"]},
  {"id": "acme01-bags-ambiguous", "question": "ACME01: what happens to our bags now the connection is cancelled?", "accepted": ["rebooking", "baggage"]}
]
```

`tests/test_routing.py` asserts:
- For each case, `route_by_keywords(question) in accepted`, parametrised by id.
- `route_by_keywords("hello") == "duty_manager"`.
- `route_by_keywords("express train") == "duty_manager"`. This is the word-boundary check.

## Task 5: MCP servers (`servers/*.py`)

Pattern for each server, shown for fares:

```python
from mcp.server.fastmcp import FastMCP
from acme.tools import fares

mcp = FastMCP("acme-fares")

@mcp.tool()
def check_fare_rule(fare_class: str) -> dict:
    """Fare rules for one fare class: change fee, refundability, pet-in-cabin fee.
    Use for: fare rules, change fees, date changes, refunds by fare, pets in cabin.
    Errors if the class is not in the fare table; then call list_fare_classes."""
    return fares.check_fare_rule(fare_class)

@mcp.tool()
def list_fare_classes() -> list[str]:
    """List every valid fare class code. Use when a fare class is unknown or rejected."""
    return fares.list_fare_classes()

if __name__ == "__main__":
    mcp.run()
```

| File | FastMCP name | Tools |
|---|---|---|
| ops_server.py | acme-ops | get_booking, get_flight_status, search_alternative_flights |
| baggage_server.py | acme-baggage | trace_bag |
| loyalty_server.py | acme-loyalty | get_loyalty_account |
| fares_server.py | acme-fares | check_fare_rule, list_fare_classes |
| review_server.py | acme-review | score_service_review |

Write docstrings as routing triggers: list the topics and keywords the tool owns, not a personality blurb.

`tests/test_servers.py`:
- Import all five server modules.
- For each, `names = {t.name for t in asyncio.run(mod.mcp.list_tools())}` must equal the table's tool set.
- The union of all names has length 8.
- `asyncio.run(fares_server.mcp.call_tool("check_fare_rule", {"fare_class": "Z"}))` raises. Use `pytest.raises(Exception)` and assert `"Z" in str(excinfo.value)`. FastMCP wraps tool errors, so do not assert the exception class.

Manual check: `uv run mcp dev servers/fares_server.py` opens the MCP Inspector, and calling `check_fare_rule` with `Z` shows the planted error.

## Task 6 (stretch): LLM router (`acme/llm_router.py`)

`route_with_llm(question: str, model: str = "qwen3.5:9b") -> str`:
- Use `urllib.request` only. POST `http://localhost:11434/api/chat` with:

  ```json
  {"model": model, "stream": false, "think": false, "format": "json",
   "options": {"temperature": 0},
   "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]}
  ```
- `SYSTEM` is built from `ESCALATION_TABLE`. It lists each desk with its keywords, and then says: `Reply only with JSON {"desk": "<one of: customer_relations, fares, loyalty, baggage, rebooking, duty_manager>"}`.
- Parse `response["message"]["content"]` as JSON and return `["desk"]`.

`tests/test_llm_router.py`:
- `pytestmark = [pytest.mark.llm, pytest.mark.skipif(os.environ.get("ACME_LLM") != "1", reason="set ACME_LLM=1")]`
- One test runs every routing case and prints `LLM accuracy: x/N` beside `keyword accuracy: y/N`. It asserts LLM accuracy `>= 0.6` (a low bar; this is a measurement, not a gate).

Run: `ACME_LLM=1 uv run pytest -m llm -s`.

## Definition of done

- `uv run pytest -q` passes. The trace_bag test shows `>= 4.5 s` in `uv run pytest --durations=5`.
- There are 8 tools across 5 servers, and the Inspector opens the fares server.
- The reviewer is proven in both directions (the bad answer fails, the good answer passes), and the vocabulary trap is recorded.
- There are 10 or more routing cases, including the ambiguous ACME01 bags case with two accepted desks.
