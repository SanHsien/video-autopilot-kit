from __future__ import annotations

import contextlib
import hashlib
import io
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "longform_maker"))
sys.path.insert(0, str(ROOT / "src"))

import gate_core  # noqa: E402
import plan_gate  # noqa: E402

import interview_gate  # noqa: E402


def _stamp(day: date = None, who: str = "編輯甲") -> str:
    return f"合規：通過 {(day or date.today()).isoformat()} 複核：{who}（政策 checklist）"


def _signed_plan(**changes: str) -> str:
    fields = {
        "cluster": "示範主題",
        "compliance": _stamp(),
        "pair": "%d. 實際標題%d | 實際縮圖%d",
    }
    fields.update(changes)
    pairs = "\n".join(fields["pair"] % (i, i, i) for i in range(1, 9))
    return (
        "框架：成就\n機器：推薦\n"
        f"cluster關鍵字：{fields['cluster']}\n{fields['compliance']}\n"
        "Expected Views 對標：9,999 中位 x3\n"
        f"## 包裝候選\n{pairs}\n## 其他\n"
    )


def test_unedited_plan_template_is_blocked() -> None:
    text = (ROOT / "examples" / "PLAN_TEMPLATE.md").read_text(encoding="utf-8")

    ok, report = plan_gate.gate_plan(text)

    assert not ok
    assert {failure[:2] for failure in report["fails"]} >= {"P3", "P4", "P5"}


def test_filled_plan_passes() -> None:
    ok, report = plan_gate.gate_plan(_signed_plan())

    assert ok, report["fails"]
    assert report["pairs"] == 8


@pytest.mark.parametrize(
    ("changes", "rule"),
    [
        ({"compliance": "合規：通過（政策 checklist YYYY-MM-DD）"}, "P4"),
        ({"compliance": "合規：通過（TODO 補日期）"}, "P4"),
        ({"compliance": "合規：通過（政策 checklist 2026-01-01）"}, "P4"),  # 舊格式：無複核人
        ({"cluster": "你的主題詞"}, "P5"),
        ({"cluster": "TODO"}, "P5"),
        ({"pair": "%d. 標題候選%d | 縮圖概念%d"}, "P3"),
    ],
)
def test_placeholder_plan_fields_are_blocked(changes: dict, rule: str) -> None:
    ok, report = plan_gate.gate_plan(_signed_plan(**changes))

    assert not ok
    assert any(failure.startswith(rule) for failure in report["fails"])


def test_real_titles_that_mention_placeholder_words_still_count() -> None:
    real_titles = "%d. AI 概念一次講清楚%d | 大字 TODO 清單%d"
    ok, report = plan_gate.gate_plan(_signed_plan(pair=real_titles))

    assert ok, report["fails"]
    assert report["pairs"] == 8


def test_placeholder_pairs_are_named_in_the_p3_message() -> None:
    _ok, report = plan_gate.gate_plan(_signed_plan(pair="%d. 標題候選%d | 縮圖概念%d"))

    assert any("模板佔位" in failure for failure in report["fails"] if failure.startswith("P3"))


def test_plan_gate_selftest_passes() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert plan_gate._selftest() == 0


def test_make_assert_raises_when_gate_says_not_ok_without_reasons() -> None:
    check = gate_core.make_assert(lambda spec: (False, {"fails": [], "warns": []}),
                                  lambda spec: "x", "Demo gate FAIL")

    with pytest.raises(AssertionError, match="ok=False"):
        check({})


@pytest.mark.parametrize("report", [None, {"ok": True}, {"ok": False, "fails": []}])
def test_raise_if_failed_rejects_contract_violations(report) -> None:
    with pytest.raises(AssertionError, match="Demo gate FAIL"):
        gate_core.raise_if_failed(report, "x", "Demo gate FAIL")


def test_raise_if_failed_passes_a_clean_report() -> None:
    gate_core.raise_if_failed({"ok": True, "fails": [], "warns": []}, "x", "Demo gate FAIL")


@pytest.mark.parametrize("cases", [[], lambda check: None])
def test_selftest_runner_with_zero_checks_is_red(cases) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert gate_core.selftest_runner(cases) == 1


def test_gate_core_selftest_passes() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert gate_core._selftest() == 0


GUEST = dict(
    ep="01", name="示範來賓", one_line="兩個月做出上架的 App",
    achievements=[("App 下載 5,000", "url:https://example.com/app-dashboard")],
    links=["https://example.com"], start_state="完全不會寫程式",
    struggle="卡在上架審核", demo="用 AI 生成一個小工具", audience="短文平台",
    screenshots_ok=["App 後台 下載 5,000"],
)


@pytest.mark.parametrize(
    ("achievement", "rule"),
    [
        (("App 下載 5,000", "TODO 來源"), "I-B"),
        (("TODO 數字/成果", "url:https://example.com/x"), "I-E"),
    ],
)
def test_todo_left_in_achievements_is_blocked(achievement: tuple, rule: str) -> None:
    ok, report = interview_gate.gate_guest(dict(GUEST, achievements=[achievement]))

    assert not ok
    assert any(failure.startswith(rule) for failure in report["fails"])


def test_interview_gate_selftest_passes() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert interview_gate._selftest() == 0


def _plan_with_compliance(line: str) -> str:
    return _signed_plan(compliance=line)


@pytest.mark.parametrize(
    "line",
    [
        "合規：待複核",
        "合規：通過",
        "合規：通過（政策 checklist）",
        f"說明：合規：通過 {date.today().isoformat()} 複核：編輯甲",
        "合規：通過 之前不准開錄（待人工複核）",
        _stamp(who="AI"),
        _stamp(who="{你的名字}"),
        _stamp(day=date.today() + timedelta(days=30)),
        f"合規：通過 {date.today().year}-02-30 複核：編輯甲",
        f"合規：通過 {date.today().isoformat()}（政策 checklist）",
    ],
)
def test_p4_requires_a_dated_human_signed_stamp(line: str) -> None:
    ok, report = plan_gate.gate_plan(_plan_with_compliance(line))

    assert not ok
    assert any(failure.startswith("P4") for failure in report["fails"])


def test_p4_accepts_a_dated_named_stamp_and_a_bullet_prefix() -> None:
    assert plan_gate.gate_plan(_plan_with_compliance(_stamp()))[0]
    assert plan_gate.gate_plan(_plan_with_compliance("- " + _stamp()))[0]


def test_p4_rejects_contradicting_stamps() -> None:
    ok, report = plan_gate.gate_plan(_plan_with_compliance(_stamp() + "\n合規：待複核"))

    assert not ok
    assert any(failure.startswith("P4") for failure in report["fails"])


def test_filled_plan_template_passes_once_signed() -> None:
    text = (ROOT / "examples" / "PLAN_TEMPLATE.md").read_text(encoding="utf-8")
    text = text.replace("你的主題詞", "AI 剪輯")
    # 模板要求「把整行換成」簽章，不是只換文字
    text = re.sub(r"^合規：待複核.*$", lambda _m: _stamp(), text, count=1, flags=re.MULTILINE)
    for i, n in enumerate("一二三四五六七八", 1):
        text = text.replace(f"標題候選{n} | 縮圖概念{n}",
                            f"新手卡關的第 {i} 個原因 | 卡關畫面 {i} 紅圈")

    ok, report = plan_gate.gate_plan(text)

    assert ok, report["fails"]


@pytest.mark.parametrize(
    "source",
    [
        "", "?", "TBD", "待補", "待來賓提供", "未提供", "YYYY-06",
        "來賓提供後台截圖",                       # 沒有型別
        "guest-supplied screenshot",
        "url:ftp://example.com/x", "url:https://", "url:",
        "file:no/such/shot.png", "file:",
        "sha256:abc", "sha256:" + "g" * 64,
    ],
)
def test_untyped_or_unverifiable_sources_are_blocked(source: str) -> None:
    ok, report = interview_gate.gate_guest(
        dict(GUEST, achievements=[("App 下載 5,000", source)]))

    assert not ok
    assert any(failure.startswith("I-B") for failure in report["fails"])


def test_typed_sources_are_accepted(tmp_path) -> None:
    shot = tmp_path / "dashboard.png"
    shot.write_bytes(b"png")
    sources = [
        ("url", "url:https://example.com/proof", None),
        ("absolute file", "file:" + str(shot), None),
        ("relative file", "file:dashboard.png", str(tmp_path)),
        ("sha256", "sha256:" + hashlib.sha256(b"png").hexdigest(), None),
    ]
    for label, source, base in sources:
        ok, report = interview_gate.gate_guest(
            dict(GUEST, achievements=[("App 下載 5,000", source)]), base)
        assert ok, (label, report["fails"])


def test_relative_file_source_resolves_against_base_dir_only(tmp_path) -> None:
    (tmp_path / "dashboard.png").write_bytes(b"png")
    other = tmp_path / "other"
    other.mkdir()
    guest = dict(GUEST, achievements=[("App 下載 5,000", "file:dashboard.png")])

    assert interview_gate.gate_guest(guest, str(tmp_path))[0]
    assert not interview_gate.gate_guest(guest, str(other))[0]


@pytest.mark.parametrize(
    ("field", "value"),
    [("struggle", "TODO 最卡的一次"), ("audience", "（待補）"), ("links", ["TODO 連結"]),
     ("screenshots_ok", ["待確認"])],
)
def test_placeholder_in_any_string_field_is_blocked(field: str, value) -> None:
    ok, report = interview_gate.gate_guest(dict(GUEST, **{field: value}))

    assert not ok
    assert any(failure.startswith("I-E") for failure in report["fails"])


def test_assert_guest_passes_base_dir_through(tmp_path) -> None:
    (tmp_path / "s.png").write_bytes(b"x")
    guest = dict(GUEST, achievements=[("App 下載 5,000", "file:s.png")])

    assert interview_gate.assert_guest(guest, base_dir=str(tmp_path)) is guest
    with pytest.raises(AssertionError, match="來賓資料 gate FAIL"):
        interview_gate.assert_guest(guest, base_dir=str(tmp_path / "nope"))


def test_is_placeholder_distinguishes_real_text() -> None:
    for text in ("", "TODO 補來源", "待來賓提供", "YYYY-MM-DD", "標題候選一", "{你的名字}", "N/A"):
        assert gate_core.is_placeholder(text), text
    for text in ("App 下載 5,000", "期待的那一天", "等待審核三週", "Todoist 教學"):
        assert not gate_core.is_placeholder(text), text
