"""The Pages file must keep the version placeholder. Do not weaken these tests."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "site" / "index.html"


def _text(element_id: str) -> str:
    html = PAGE.read_text(encoding="utf-8")
    match = re.search(
        rf"""id=["']{element_id}["'][^>]*>\s*(.*?)\s*</""",
        html,
        flags=re.DOTALL,
    )
    assert match, element_id
    return match.group(1)


def test_version_placeholder_stays_in_git() -> None:
    assert _text("version") == "__VERSION__"


def test_student_id_is_latin_digits() -> None:
    assert re.fullmatch(r"[0-9]+", _text("student-id"))


def test_name_and_sentence_are_filled_in() -> None:
    assert _text("student-name") not in {"", "YOUR_NAME"}
    assert _text("sentence") not in {"", "YOUR_SENTENCE"}
