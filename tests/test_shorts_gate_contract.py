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
    "rules",
    [
        {"first_cut_max": float("nan")},
        {"first_cut_max": float("inf")},
        {"dur_min": "10"},
        {"loop_tol": True},
        {"sr_fail": -1.0},
        {"dur_deadzone": (40.0, 30.0)},
        {"dur_deadzone": (30.0,)},
        {"white_tokens": "white"},
        {"dur_min": 30.0, "dur_max": 20.0},
        ["first_cut_max", 3.0],
    ],
)
def test_invalid_rule_values_fail_closed(rules) -> None:
    with pytest.raises(AssertionError, match="rule|rules|dur_min"):
        shorts_gate.merge_rules(rules)


def test_valid_rule_overrides_still_merge() -> None:
    merged = shorts_gate.merge_rules(
        {"dur_deadzone": None, "white_tokens": ["white", "cream"], "nonwhite_max_colors": 3}
    )

    assert merged["dur_deadzone"] is None
    assert merged["nonwhite_max_colors"] == 3


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


@pytest.mark.parametrize("spec", [None, [], "spec", 42])
def test_non_dict_spec_is_blocked_instead_of_crashing(spec) -> None:
    ok, report = shorts_gate.gate_shorts(spec)

    assert not ok
    assert any("SPEC" in failure for failure in report["fails"])


@pytest.mark.parametrize(
    "changes",
    [
        {"place": 123},
        {"what": ["測試說明"]},
        {"addr": 5},
        {"name": None},
        {"platform": ["ig_reels"]},
    ],
)
def test_wrongly_typed_fields_are_blocked_instead_of_crashing(changes: dict) -> None:
    spec = make_long_spec()
    spec.update(changes)

    ok, report = shorts_gate.gate_shorts(spec)

    assert not ok
    assert any("SPEC" in failure for failure in report["fails"])


def test_negative_segment_start_is_blocked() -> None:
    spec = make_long_spec()
    clip, _start, duration = spec["segs"][1]
    spec["segs"][1] = (clip, -1.5, duration)

    ok, report = shorts_gate.gate_shorts(spec)

    assert not ok
    assert any("SPEC segs[1] in_sec" in failure for failure in report["fails"])


@pytest.mark.parametrize(
    "scan",
    [
        [1],
        {"clips": "rows"},
        {"clips": ["clip"]},
        {"clips": [{"name": "clip", "rows": "rows"}]},
        {"clips": [{"name": "clip", "rows": ["row"]}]},
        {"clips": [{"name": "clip", "rows": [{"t": "2.0", "bright": "dark"}]}]},
    ],
)
def test_malformed_frame_scan_is_ignored(tmp_path: Path, scan) -> None:
    import json

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"")
    (tmp_path / "_scan.json").write_text(json.dumps(scan), encoding="utf-8")
    spec = make_long_spec()
    spec["segs"] = [(str(clip), start, duration) for _old, start, duration in spec["segs"]]

    ok, report = shorts_gate.gate_shorts(
        spec,
        {"dur_min": 26.0, "dur_max": 60.0, "dur_deadzone": None},
    )

    assert ok, report["fails"]


def test_bad_frame_scan_rows_do_not_hide_the_first_frame_warning(tmp_path: Path) -> None:
    import json

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"")
    rows = [
        {"t": 2.0, "sharp": 10.0, "bright": 100},
        {"t": 5.0, "sharp": 40.0, "bright": 100},
        {"t": 7.0, "sharp": float("nan"), "bright": 100},
        {"t": "9.0", "sharp": 99.0, "bright": 100},
        "row",
    ]
    scan = {"clips": [{"name": "clip", "rows": rows}, "clip"]}
    (tmp_path / "_scan.json").write_text(json.dumps(scan), encoding="utf-8")
    spec = make_long_spec()
    spec["segs"] = [(str(clip), start, duration) for _old, start, duration in spec["segs"]]

    ok, report = shorts_gate.gate_shorts(
        spec,
        {"dur_min": 26.0, "dur_max": 60.0, "dur_deadzone": None},
    )

    assert ok, report["fails"]
    assert any("S-Q" in warning and "clip@5.0s=40.0" in warning for warning in report["warns"])


def test_assert_shorts_names_a_non_dict_spec() -> None:
    with pytest.raises(AssertionError, match="Shorts gate FAIL"):
        shorts_gate.assert_shorts(None)


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
