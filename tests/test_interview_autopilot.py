from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "longform_maker"))
sys.path.insert(0, str(ROOT / "src"))

import gate_core  # noqa: E402

import interview_autopilot  # noqa: E402
import interview_gate  # noqa: E402

TRICKY_NAMES = [
    'Dwayne "The Rock"',
    "C:\new\table",
    r"back\slash",
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


def _setup_planning_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, achievements=None
) -> tuple[Path, dict]:
    plan_root = tmp_path / "planning"
    plan_root.mkdir()
    monkeypatch.setattr(interview_autopilot, "PLAN_ROOT", str(plan_root))

    # Keep profile predictable: HOST_NAME is unfilled by default, CLUSTER is filled
    profile = dict(interview_autopilot.PROFILE_DEFAULTS)
    profile["CLUSTER"] = "示範主題"
    monkeypatch.setattr(
        interview_autopilot,
        "_PROFILE_CACHE",
        {interview_autopilot.PROFILE_PATH: profile},
    )

    ep_dir = plan_root / "interview_EP01"
    ep_dir.mkdir()

    achv = achievements or [("下載 5,000", "url:https://example.com/app-dashboard")]
    guest_dict = {
        "ep": "01",
        "name": "小明",
        "one_line": "兩個月做出上架的 App",
        "achievements": achv,
        "links": ["https://example.com"],
        "start_state": "完全不會寫程式",
        "struggle": "卡在上架審核",
        "demo": "用 AI 生成一個小工具",
        "audience": "你的短文平台",
        "screenshots_ok": ["後台截圖 下載 5,000"],
    }
    guest_code = f"# -*- coding: utf-8 -*-\nGUEST = {guest_dict!r}\n"
    (ep_dir / "_guest.py").write_text(guest_code, encoding="utf-8")
    return ep_dir, guest_dict


def test_cli_plan_reviewer_wiring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ep_dir, _ = _setup_planning_env(tmp_path, monkeypatch)

    # 1. Without --reviewer: compliance stamp uses unfilled {你的名字} -> plan_gate P4 fails
    monkeypatch.setattr(
        sys, "argv", ["interview_autopilot", "plan", "01", "--compliance-ok"]
    )
    assert interview_autopilot.main() == 1

    # 2. Without --compliance-ok: compliance line is unsigned ("待複核") -> plan_gate P4 fails
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "interview_autopilot",
            "plan",
            "01",
            "--reviewer",
            "測試複核人",
        ],
    )
    assert interview_autopilot.main() == 1

    # 3. Direct plan() call without reviewer raises AssertionError from plan_gate
    with pytest.raises(AssertionError, match="規劃 gate FAIL（plan_gate）"):
        interview_autopilot.plan("01", compliance_ok=True, reviewer=None)

    # 4. With --reviewer: passed through to plan_gate P4 stamp -> PASS
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "interview_autopilot",
            "plan",
            "01",
            "--compliance-ok",
            "--reviewer",
            "測試複核人",
        ],
    )
    assert interview_autopilot.main() == 0

    # Deliverables are generated and carry the stamped reviewer name
    pub_kit = ep_dir / "EP01_publish_kit.md"
    assert pub_kit.is_file()
    assert "複核：測試複核人" in pub_kit.read_text(encoding="utf-8")


def test_plan_passes_base_dir_to_interview_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    ep_dir, guest = _setup_planning_env(
        tmp_path, monkeypatch, achievements=[("下載 5,000", "file:proof.png")]
    )
    (ep_dir / "proof.png").write_bytes(b"dummy_png_bytes")

    # plan() forwards base_dir=d to assert_guest -> succeeds
    res_dir = interview_autopilot.plan("01", compliance_ok=True, reviewer="測試複核人")
    assert res_dir == str(ep_dir)

    # If base_dir is omitted or pointed to a directory without proof.png, assert_guest fails
    with pytest.raises(AssertionError, match="file: 指向的檔案不存在"):
        interview_gate.assert_guest(guest)

    with pytest.raises(AssertionError, match="file: 指向的檔案不存在"):
        interview_gate.assert_guest(guest, base_dir=str(tmp_path))


def test_interview_gate_fallback_regex_matches_gate_core():
    # Load interview_gate in fallback isolation (when gate_core import fails)
    spec = importlib.util.spec_from_file_location(
        "interview_gate_fallback_isolated",
        str(ROOT / "src" / "interview_gate.py"),
    )
    fallback_mod = importlib.util.module_from_spec(spec)
    saved_modules = dict(sys.modules)
    saved_path = list(sys.path)
    try:
        sys.modules["gate_core"] = None
        sys.path = [p for p in sys.path if "longform_maker" not in p]
        spec.loader.exec_module(fallback_mod)
    finally:
        sys.modules.clear()
        sys.modules.update(saved_modules)
        sys.path = saved_path

    # Check that fallback regex patterns and flags exactly equal gate_core canonical ones
    assert fallback_mod._PH_RE.pattern == gate_core._PLACEHOLDER_RE.pattern
    assert fallback_mod._PH_RE.flags == gate_core._PLACEHOLDER_RE.flags
    assert fallback_mod._PH_WHOLE_RE.pattern == gate_core._PLACEHOLDER_WHOLE_RE.pattern
    assert fallback_mod._PH_WHOLE_RE.flags == gate_core._PLACEHOLDER_WHOLE_RE.flags

    # Check identical behavior on sample inputs
    samples = [
        "",
        "   ",
        "TODO",
        "TODO 補來源",
        "TBD",
        "FIXME",
        "XXX",
        "YYYY",
        "MM-DD",
        "YYYY-MM-DD",
        "待補",
        "待填",
        "待定",
        "待查",
        "待寫",
        "待確",
        "待提供",
        "待來賓提供",
        "未提供",
        "未填",
        "候選一",
        "概念三",
        "你的主題詞",
        "你的名字",
        "你的cluster",
        "{你的名字}",
        "?",
        "？",
        "...",
        "…",
        "-",
        "—",
        "_",
        "＿",
        "N/A",
        "none",
        "null",
        "無",
        "沒有",
        "不明",
        "未知",
        "App 下載 5,000",
        "真實標題",
        "Todoist 教學",
        "期待的那一天",
        "等待審核三週",
        "2026-10-30",
        "url:https://example.com/demo",
        "file:screenshot.png",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    ]
    for s in samples:
        assert fallback_mod.is_placeholder(s) == gate_core.is_placeholder(s), (
            f"Fallback is_placeholder({s!r}) != gate_core.is_placeholder({s!r})"
        )


def test_single_file_fallback_fail_closed_contract():
    # Verify interview_autopilot and interview_gate fallback fail-closed behavior matches gate_core
    spec_auto = importlib.util.spec_from_file_location(
        "interview_autopilot_fallback_isolated",
        str(ROOT / "src" / "interview_autopilot.py"),
    )
    auto_fallback = importlib.util.module_from_spec(spec_auto)
    saved_modules = dict(sys.modules)
    saved_path = list(sys.path)
    try:
        sys.modules["gate_core"] = None
        sys.path = [p for p in sys.path if "longform_maker" not in p]
        spec_auto.loader.exec_module(auto_fallback)
    finally:
        sys.modules.clear()
        sys.modules.update(saved_modules)
        sys.path = saved_path

    bad_reports = [
        None,
        "not-a-dict",
        {"ok": True},  # missing fails list
        {"ok": False, "fails": []},  # ok=False without reasons
        {"ok": False, "fails": ["failed reason"]},
    ]
    for rep in bad_reports:
        with pytest.raises(AssertionError):
            auto_fallback._raise_if_failed(rep, "label", "title")
        with pytest.raises(AssertionError):
            gate_core.raise_if_failed(rep, "label", "title")

