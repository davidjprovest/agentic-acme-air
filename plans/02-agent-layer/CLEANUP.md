# Chunk 02 cleanup review

Baseline before cleanup: 67 passed, 1 skipped (opt-in `llm`). Goal: cleaner and shorter, no behaviour change.

| # | Item | File(s) | What and why | Risk | Decision |
|---|---|---|---|---|---|
| 1 | Shared fixture loader | `tests/test_routing.py`, `tests/test_reviewer.py`, `tests/test_llm_router.py` | Each file loads its JSON in one line. A `conftest.py` *fixture* can't replace it, because `@pytest.mark.parametrize` needs the cases at import time, before fixtures exist. A plain helper module would save about one line per file and add an import indirection. | low | **Skip.** Net gain is ~3 lines and the one-liner is already obvious to a reader. |
| 2 | `tonight/BUILD_SPEC.md` stale | `tonight/BUILD_SPEC.md`, `tonight/PLAN.md` | Spec tells the LLM router to send `"format": "json"` (Ollama 0.40 rejects it with HTTP 501 for qwen3.5) and to start servers with `uv run mcp dev servers/...` (fails on this Mac, hidden `.pth`). Add a short "superseded" note at the top of each, pointing to the code and tutorial. Historical text left as written. | low | **Apply.** |
| 3 | `TECH_STACK.md` wrong and thin | `TECH_STACK.md` | Says "gwen3.5"; the tag is `qwen3.5:9b`. Missing what was actually used: uv, Python 3.12, `mcp` 1.30 FastMCP, pytest 9, Ollama 0.40. | low | **Apply.** |
| 4 | `README.md` is one line | `README.md` | Add a quickstart: `uv sync`, `uv run pytest -q`, Inspector command, `ACME_LLM=1` live test, links to tutorial and plans. | low | **Apply.** |
| 5 | `earned` dict in reviewer | `acme/tools/review.py` | The dict repeats the weight names, but it is the readable bridge from five parameters to five weights; zipping against `WEIGHTS` order would be shorter and more fragile. Only change: sum over `WEIGHTS.items()` instead of re-indexing `WEIGHTS[fact]`. Same line, same result. | low | **Apply** (the one-line tweak only). |
| 6 | Shared lookup helper for tools | `acme/tools/*.py` | `.upper()` + `.get()` + raise + `deepcopy` repeats in 5 functions. Tutorial Chapter 2 teaches exactly this pattern from `ops.py:9`. A helper would hide the lesson and each function is 4 lines. | med | **Skip.** Teaching clarity beats DRY. |
| 7 | Duplicated comparison printing | `tests/test_llm_router.py` | `compare()` is already one shared function, called twice. Nothing duplicated. | low | **Skip.** No change needed. |
| 8 | Parametrized reviewer test re-implements `review()` | `tests/test_reviewer.py:33` | `test_case_scores_as_expected` inlines the same call that `review(case_id)` wraps. Use `review(case["id"])`. Same assertion, same line numbers. | low | **Apply.** |
| 9 | Unzipped `.docx` debris in repo root | `[Content_Types].xml`, `_rels/`, `docProps/`, `word/` | Already in `.gitignore` and untracked. Deleting local files is David's call. | low | **Skip.** Not tracked; leave for David. |
| 10 | Inconsistent fixture path style | `tests/test_routing.py`, `tests/test_reviewer.py` | `test_llm_router.py` uses a `FIXTURES` constant, the other two inline the path. Cosmetic. | low | **Skip.** Same reason as item 1. |

Untouched by design: the `trace_bag` sleep and its comment, missing class Z and its error message, every MCP server/tool/parameter name, every value in `acme/data.py` and the fixture JSON.
