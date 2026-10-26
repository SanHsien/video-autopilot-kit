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
