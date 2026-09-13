"""依賴新鮮度檢查器：紅燈的兩條正當出口。

宣告是相容性承諾，不是消音鍵。當某個下限**不該**跟著現行版走時，只有兩種留下理由的
做法：宣告行上的 `# freshness-hold:`（長期政策），或 `.github/dependency-deferrals.json`
記下「這次不升 + 當時看到的版本」（PyPI 超過該版本就自動失效）。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_dependency_freshness", ROOT / "tools" / "check_dependency_freshness.py"
)
assert _spec is not None and _spec.loader is not None
freshness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freshness)


def test_hold_marker_is_read_from_the_requirement_line() -> None:
    packages = freshness.parse_requirements(
        "pytest>=8.4,<9  # freshness-hold: 矩陣還有 py3.9\nruff>=0.16,<1\n",
        "requirements-dev.txt",
    )

    holds = {package["name"]: package["hold"] for package in packages}
    assert holds == {"pytest": "矩陣還有 py3.9", "ruff": ""}


def test_a_comment_without_the_marker_is_not_a_hold() -> None:
    packages = freshness.parse_requirements("ruff>=0.16,<1  # 一般註解\n", "requirements-dev.txt")

    assert packages[0]["hold"] == ""


def test_deferral_without_a_reviewed_release_is_ignored(tmp_path: Path) -> None:
    # 沒有 deferredLatest 的條目等於永久靜音，直接忽略。
    path = tmp_path / "deferrals.json"
    path.write_text(json.dumps({"deferrals": {"numpy": {"reason": "later"}}}), encoding="utf-8")

    assert freshness.load_deferrals(path) == {}


def test_deferral_with_a_reviewed_release_is_read(tmp_path: Path) -> None:
    path = tmp_path / "deferrals.json"
    path.write_text(
        json.dumps(
            {"deferrals": {"numpy": {"deferredLatest": "2.5.2", "reason": "要先在 Windows 驗算"}}}
        ),
        encoding="utf-8",
    )

    assert freshness.load_deferrals(path) == {"numpy": ("2.5.2", "要先在 Windows 驗算")}


def test_missing_deferrals_file_defers_nothing(tmp_path: Path) -> None:
    assert freshness.load_deferrals(tmp_path / "absent.json") == {}


def test_aged_floor_needs_review_unless_held_or_deferred() -> None:
    assert freshness.needs_review({"outdated": True, "hold": "", "deferred_reason": ""})
    assert not freshness.needs_review({"outdated": True, "hold": "政策", "deferred_reason": ""})
    assert not freshness.needs_review(
        {"outdated": True, "hold": "", "deferred_reason": "已評估，等桌面驗證"}
    )
