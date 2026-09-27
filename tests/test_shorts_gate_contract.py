from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SHORTS_DIR = ROOT / "src" / "longform_maker"
sys.path.insert(0, str(SHORTS_DIR))

import shorts_gate  # noqa: E402


def make_long_spec() -> dict:
    clip = str(SHORTS_DIR / "shorts_gate.py")
    return {
        "name": "custom-band",
        "place": "測試地",
        "what": "測試說明",
        "addr": "測試地｜某路 1 號",
        "segs": [
            (clip, 2.0, 2.0),
            (clip, 5.0, 9.0),
            (clip, 15.0, 9.0),
            (clip, 25.0, 10.0),
            (clip, 1.0, 1.0),
        ],
        "caps_by_seg": [
            (0, [("測試地", "white")], "hook"),
            (1, [("測試說明", "white")], "sub"),
            (2, [("內容一", "white")], "sub"),
            (3, [("內容二", "white")], "sub"),
        ],
        "bgm_folder": "demo",
    }


def test_documented_default_rules_are_public() -> None:
    assert shorts_gate.DEFAULT_RULES["dur_min"] == 13.0
    assert shorts_gate.DEFAULT_RULES["dur_max"] == 25.0
    assert shorts_gate.DEFAULT_RULES["first_cut_max"] == 2.05


def test_rule_override_allows_a_calibrated_duration_band() -> None:
    spec = make_long_spec()

    default_ok, default_report = shorts_gate.gate_shorts(spec)
    custom_ok, custom_report = shorts_gate.gate_shorts(
        spec,
        {"dur_min": 26.0, "dur_max": 60.0, "dur_deadzone": None},
    )

    assert not default_ok
    assert any("S-B" in failure for failure in default_report["fails"])
    assert custom_ok, custom_report["fails"]


def test_rule_override_does_not_mutate_defaults() -> None:
    original = dict(shorts_gate.DEFAULT_RULES)

    merged = shorts_gate.merge_rules({"first_cut_max": 3.0})

    assert merged["first_cut_max"] == 3.0
    assert shorts_gate.DEFAULT_RULES == original


def test_report_reflects_selected_platform_and_custom_thresholds() -> None:
    spec = make_long_spec()
    spec["platform"] = "ig_reels"
    spec["segs"][0] = (spec["segs"][0][0], 2.0, 2.5)

    ok, report = shorts_gate.gate_shorts(spec, {"first_cut_max": 2.4})

    assert not ok
    assert report["platform"] == "ig_reels"
    assert any("> 2.4s" in failure for failure in report["fails"])


def test_unknown_rule_key_fails_closed() -> None:
    with pytest.raises(AssertionError, match="unknown rule key"):
        shorts_gate.merge_rules({"dur_mn": 12.0})


@pytest.mark.parametrize(
    "changes",
    [
        {"segs": None},
        {"segs": []},
        {"segs": [("clip.mp4", 0.0)]},
        {"segs": [("clip.mp4", 0.0, -1.0)]},
        {"caps_by_seg": None},
        {"caps_by_seg": [(99, [("越界", "white")], "sub")]},
        {"caps_by_seg": [(0, [], "hook")]},
        {"caps_by_seg": [(0, [("缺顏色",)], "hook")]},
    ],
)
def test_malformed_specs_are_blocked_instead_of_crashing(changes: dict) -> None:
    spec = make_long_spec()
    spec.update(changes)

    ok, report = shorts_gate.gate_shorts(spec)

    assert not ok
    assert any("SPEC" in failure for failure in report["fails"])


def test_assert_shorts_accepts_the_same_override_contract() -> None:
    ready = shorts_gate.assert_shorts(
        make_long_spec(),
        {"dur_min": 26.0, "dur_max": 60.0, "dur_deadzone": None},
    )

    assert ready["_dur"] == 31.0
    assert ready["caps"]


def test_embedded_shorts_gate_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert shorts_gate._selftest() == 0
    assert "SELFTEST GREEN" in capsys.readouterr().out
