import json

import pytest

from acme.evals import FIXTURE, main, render_html, run_eval
from acme.scoring import review_answer

CASES = json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def result():
    return run_eval(CASES)


def record(result, case_id):
    return next(r for r in result["records"] if r["id"] == case_id)


def test_reviewer_agrees_with_every_label(result):
    assert result["summary"]["n"] == 11
    assert result["summary"]["agreed"] == 11


def test_records_are_in_fixture_order(result):
    assert [r["id"] for r in result["records"]] == [c["id"] for c in CASES]


def test_trap_is_marked_down_but_live_gate_delivers(result):
    rec = record(result, "trap-vocabulary")
    assert rec["passed"] is False
    assert rec["gate_decision"] == "deliver"


def test_bad_promise_is_retried_by_the_gate(result):
    assert record(result, "bad-promise")["gate_decision"] == "retry"


def test_scores_match_review_answer(result):
    for case, rec in zip(CASES, result["records"]):
        expected = review_answer(case["answer"], case["pnr"])["score"]["score"]
        assert rec["score"] == expected


def test_html_has_ids_and_sample_size_without_script_or_links(result):
    html = render_html(result)
    for case in CASES:
        assert case["id"] in html
    assert "n=11" in html
    assert "<script" not in html
    assert "http" not in html


def test_html_escapes_case_text():
    cases = [{"id": "<b>x</b>", "pnr": "ACME02", "answer": "Hello.", "expected_pass": False}]
    html = render_html(run_eval(cases))
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>x</b>" not in html


def test_main_prints_summary_and_writes_html(tmp_path, capsys):
    path = tmp_path / "eval.html"
    assert main(["--html", str(path)]) == 0
    assert path.exists()
    assert "11/11" in capsys.readouterr().out
