from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "longform_maker"))
sys.path.insert(0, str(ROOT / "src"))

import interview_autopilot  # noqa: E402

TRICKY_NAMES = [
    'Dwayne "The Rock"',
    "C:\new\table",
    "back\slash",
    "小明\n第二行",
    "o'brien",
]


@pytest.mark.parametrize("name", TRICKY_NAMES)
def test_invite_guest_stub_round_trips_any_name(tmp_path, monkeypatch, name):
    monkeypatch.setattr(interview_autopilot, "PLAN_ROOT", str(tmp_path))
    plan_dir = Path(interview_autopilot.invite("01", name))
    source = (plan_dir / "_guest.py").read_text(encoding="utf-8")
    scope: dict = {}
    exec(compile(source, "_guest.py", "exec"), scope)  # noqa: S102 - 剛產出的 stub
    assert scope["GUEST"]["name"] == name
    assert scope["GUEST"]["ep"] == "01"


def test_render_keeps_double_parentheses_inside_filled_values(tmp_path, monkeypatch):
    (tmp_path / "demo.template.md").write_text("Hi ((name)), ((topic))\n", encoding="utf-8")
    monkeypatch.setattr(interview_autopilot, "TPL_DIR", str(tmp_path))
    out = interview_autopilot.render("demo", name="用 ((AI)) 剪輯的人", topic="x")
    assert out.strip() == "Hi 用 ((AI)) 剪輯的人, x"


def test_render_still_rejects_unfilled_fields(tmp_path, monkeypatch):
    (tmp_path / "demo.template.md").write_text("Hi ((name)) ((missing))\n", encoding="utf-8")
    monkeypatch.setattr(interview_autopilot, "TPL_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="missing"):
        interview_autopilot.render("demo", name="a")
