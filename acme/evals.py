"""Post-run evals: score the labelled cases and show what the live gate would do.

Everything goes through review_answer and gate_answer, the two functions the
graph uses. This module never re-implements a weight, keyword or threshold.
"""

import argparse
import html
import json
from pathlib import Path

from acme.gate import gate_answer
from acme.scoring import review_answer

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "reviewer_cases.json"


def run_eval(cases: list[dict]) -> dict:
    """Score every case with review_answer and record what the live gate would do.

    Returns {"records": [...], "summary": {...}}.
      record, one per case, in input order:
        id, pnr, expected_pass, passed (score["passed"]), score (score["score"]),
        hard_failures, soft_failures, gate_decision (gate_answer at attempt=1),
        agrees (passed == expected_pass)
      summary, all counts over the cases:
        n:           number of cases scored
        agreed:      cases where passed equals expected_pass
        passed:      cases the post-run score marks as passed
        hard_failed: cases with at least one hard failure
        delivered:   cases the live gate would deliver (decision "deliver")
    """
    records = []
    for case in cases:
        review = review_answer(case["answer"], case["pnr"])
        gate = gate_answer(case["answer"], case["pnr"], attempt=1)
        passed = review["score"]["passed"]
        records.append(
            {
                "id": case["id"],
                "pnr": case["pnr"],
                "expected_pass": case["expected_pass"],
                "passed": passed,
                "score": review["score"]["score"],
                "hard_failures": review["hard_failures"],
                "soft_failures": review["soft_failures"],
                "gate_decision": gate["decision"],
                "agrees": passed == case["expected_pass"],
            }
        )
    summary = {
        "n": len(records),
        "agreed": sum(r["agrees"] for r in records),
        "passed": sum(r["passed"] for r in records),
        "hard_failed": sum(bool(r["hard_failures"]) for r in records),
        "delivered": sum(r["gate_decision"] == "deliver" for r in records),
    }
    return {"records": records, "summary": summary}


def _esc(value) -> str:
    return html.escape(str(value))


def render_html(result: dict) -> str:
    """A self-contained HTML report: summary first, then one table row per case.
    No external scripts, stylesheets, fonts or links. Every rate shows its sample
    size beside it, written as n=<count>. All case text is HTML-escaped."""
    s = result["summary"]
    n = s["n"]
    lines = [
        ("Reviewer agrees with labels", "agreed"),
        ("Post-run passed", "passed"),
        ("Hard failures", "hard_failed"),
        ("Live gate would deliver", "delivered"),
    ]
    items = "".join(f"<li>{label}: {s[key]}/{n} (n={n})</li>" for label, key in lines)
    rows = "".join(
        "<tr>"
        f"<td>{_esc(r['id'])}</td><td>{_esc(r['pnr'])}</td>"
        f"<td>{_esc(r['expected_pass'])}</td><td>{_esc(r['passed'])}</td>"
        f"<td>{_esc(r['score'])}</td>"
        f"<td>{_esc(', '.join(r['hard_failures']))}</td>"
        f"<td>{_esc(', '.join(r['soft_failures']))}</td>"
        f"<td>{_esc(r['gate_decision'])}</td><td>{_esc(r['agrees'])}</td>"
        "</tr>"
        for r in result["records"]
    )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>Acme Air review evals</title>"
        "<style>body{font-family:sans-serif;margin:2em}"
        "table{border-collapse:collapse}td,th{border:1px solid #999;padding:4px 8px}"
        "</style></head><body>"
        f"<h1>Acme Air review evals</h1><ul>{items}</ul>"
        "<table><thead><tr><th>id</th><th>pnr</th><th>expected pass</th><th>passed</th>"
        "<th>score</th><th>hard failures</th><th>soft failures</th><th>gate</th>"
        f"<th>agrees</th></tr></thead><tbody>{rows}</tbody></table>"
        "</body></html>"
    )


def main(argv: list[str] | None = None) -> int:
    """`uv run python -m acme.evals [--html PATH]`: print one summary line,
    e.g. 'reviewer agrees with labels 11/11 (n=11)', and write the report if asked."""
    parser = argparse.ArgumentParser(prog="acme.evals")
    parser.add_argument("--html", metavar="PATH", help="write an HTML report here")
    args = parser.parse_args(argv)
    result = run_eval(json.loads(FIXTURE.read_text()))
    s = result["summary"]
    print(f"reviewer agrees with labels {s['agreed']}/{s['n']} (n={s['n']})")
    if args.html:
        Path(args.html).write_text(render_html(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
