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


@pytest.mark.parametrize("doc", ["examples/README.md", "knowledge/ops-automation.md"])
def test_docs_point_channel_state_copy_at_the_path_the_tracker_reads(doc):
    # The setup docs told users to copy the template to the repo root; the tracker reads
    # src/channel_state.json, so the documented copy step left the tracker without state.
    import channel_tracker

    expected = Path(channel_tracker.STATE_PATH).relative_to(ROOT).as_posix()
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert expected in text


def test_ops_automation_names_scripts_by_paths_that_exist():
    # Bare names like `plan_gate.py` do not run from the repo root; every script the
    # ops guide tells people to run must be a repo-relative path that exists.
    import re

    text = (ROOT / "knowledge" / "ops-automation.md").read_text(encoding="utf-8")
    names = set(re.findall(r"`(?:python )?([\w./-]+\.py)", text))
    assert names
    missing = sorted(n for n in names if not (ROOT / n).is_file())
    assert missing == []
