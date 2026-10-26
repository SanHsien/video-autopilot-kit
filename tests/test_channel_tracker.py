from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_save_state_failure_keeps_previous_state_file(tmp_path):
    import json

    import channel_tracker

    path = tmp_path / "channel_state.json"
    good = {"videos": [{"name": "v1"}], "pending_actions": []}
    channel_tracker.save_state(good, str(path))
    with pytest.raises(TypeError):
        channel_tracker.save_state({"videos": [], "bad": {1, 2}}, str(path))
    assert json.loads(path.read_text(encoding="utf-8")) == good
    assert [p.name for p in tmp_path.iterdir()] == ["channel_state.json"]
