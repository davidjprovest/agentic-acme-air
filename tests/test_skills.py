from pathlib import Path

import pytest

from acme import rubric
from acme.data import DISCLAIMER
from acme.routing import ESCALATION_TABLE

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILL_DIRS = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []


def parse_frontmatter(text: str) -> dict:
    """Read the lines between the first two '---' lines as key: value pairs."""
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "missing opening ---"
    end = lines.index("---", 1)
    pairs = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs


def read_skill(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def test_both_skills_exist():
    assert [p.name for p in SKILL_DIRS] == ["service-recovery-protocol", "service-review-rubric"]


@pytest.mark.parametrize("folder", SKILL_DIRS, ids=lambda p: p.name)
def test_frontmatter_name_matches_folder(folder):
    assert parse_frontmatter((folder / "SKILL.md").read_text())["name"] == folder.name


@pytest.mark.parametrize("folder", SKILL_DIRS, ids=lambda p: p.name)
def test_frontmatter_description_not_empty(folder):
    assert parse_frontmatter((folder / "SKILL.md").read_text())["description"]


def test_protocol_contains_disclaimer_verbatim():
    assert DISCLAIMER in read_skill("service-recovery-protocol")


@pytest.mark.parametrize("desk", [desk for desk, _ in ESCALATION_TABLE])
def test_protocol_names_every_desk(desk):
    assert desk in read_skill("service-recovery-protocol")


def test_protocol_has_seven_numbered_rules():
    body = read_skill("service-recovery-protocol")
    for n in range(1, 8):
        assert f"\n{n}. " in body


RUBRIC_KEYWORDS = [
    *rubric.OPTION_MARKERS,
    *rubric.URGENCY_WORDS,
    rubric.NEXT_STEP,
    *rubric.PROMISE_WORDS,
    rubric.ELIGIBILITY_CAVEAT,
]


@pytest.mark.parametrize("keyword", RUBRIC_KEYWORDS)
def test_rubric_skill_contains_every_keyword(keyword):
    assert keyword in read_skill("service-review-rubric")


@pytest.mark.parametrize("desk,keywords", ESCALATION_TABLE, ids=[desk for desk, _ in ESCALATION_TABLE])
def test_protocol_table_row_matches_routing(desk, keywords):
    assert f"| {desk} | {', '.join(keywords)} |" in read_skill("service-recovery-protocol")
