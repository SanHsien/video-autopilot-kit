from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "longform_maker"))
sys.path.insert(0, str(ROOT / "src"))

import gate_core  # noqa: E402
import plan_gate  # noqa: E402

import interview_gate  # noqa: E402


def _signed_plan(**changes: str) -> str:
    fields = {
        "cluster": "示範主題",
        "compliance": "合規：通過（政策 checklist 2026-01-01）",
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
    achievements=[("App 下載 5,000", "來賓提供後台截圖")],
    links=["https://example.com"], start_state="完全不會寫程式",
    struggle="卡在上架審核", demo="用 AI 生成一個小工具", audience="短文平台",
    screenshots_ok=["App 後台 下載 5,000"],
)


@pytest.mark.parametrize(
    "achievement",
    [("App 下載 5,000", "TODO 來源"), ("TODO 數字/成果", "來賓自報")],
)
def test_todo_left_in_achievements_is_blocked(achievement: tuple) -> None:
    ok, report = interview_gate.gate_guest(dict(GUEST, achievements=[achievement]))

    assert not ok
    assert any(failure.startswith("I-E") for failure in report["fails"])


def test_interview_gate_selftest_passes() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert interview_gate._selftest() == 0
