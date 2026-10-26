from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capcut_helpers.subtitle_corrections import apply_subtitle_corrections  # noqa: E402


def _draft(text: str) -> dict:
    content = {"text": text, "styles": [{"range": [0, len(text)]}]}
    return {"materials": {"texts": [{"content": json.dumps(content, ensure_ascii=False)}]}}


@pytest.mark.parametrize(
    "right",
    [r"C:\new\1", r"\d+", r"a\g<0>b", "100%\\"],
)
def test_replacement_text_is_literal_not_a_regex_template(right: str) -> None:
    draft = _draft("open cloud now")

    stats = apply_subtitle_corrections(draft, extra_corrections={"cloud": right}, verbose=False)

    corrected = json.loads(draft["materials"]["texts"][0]["content"])["text"]
    assert corrected == f"open {right} now"
    assert stats["total_fixes"] == 1
