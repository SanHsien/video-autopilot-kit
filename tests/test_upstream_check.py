from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_upstream_updates as checker  # noqa: E402


def sample_baseline() -> dict:
    return {
        "repo": "https://example.invalid/upstream.git",
        "branch": "main",
        "reviewed_through": "a" * 40,
        "reviewed_date": "2026-08-09",
    }


def test_baseline_file_is_complete() -> None:
    baseline = checker.load_baseline()

    assert baseline["repo"].endswith("Hao0321/video-autopilot-kit.git")
    assert baseline["branch"] == "main"
    assert len(baseline["reviewed_through"]) == 40


def test_load_baseline_rejects_missing_and_invalid_files(tmp_path: Path) -> None:
    with pytest.raises(checker.UpstreamCheckError, match="missing baseline"):
        checker.load_baseline(tmp_path / "missing.json")

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{", encoding="utf-8")
    with pytest.raises(checker.UpstreamCheckError, match="invalid baseline"):
        checker.load_baseline(invalid_json)

    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text(json.dumps({"repo": "x"}), encoding="utf-8")
    with pytest.raises(checker.UpstreamCheckError, match="missing fields"):
        checker.load_baseline(incomplete)


def test_load_baseline_requires_full_sha(tmp_path: Path) -> None:
    baseline = sample_baseline()
    baseline["reviewed_through"] = "abc1234"
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    with pytest.raises(checker.UpstreamCheckError, match="40-character SHA"):
        checker.load_baseline(path)


def test_run_git_reports_failure(tmp_path: Path) -> None:
    with pytest.raises(checker.UpstreamCheckError, match="git status failed"):
        checker.run_git(["status"], tmp_path)


def test_render_markdown_reports_clean_state_and_errors() -> None:
    clean = checker.render_markdown(sample_baseline(), [])
    failed = checker.render_markdown(sample_baseline(), [], error="fetch failed")

    assert "No new upstream commits" in clean
    assert "Check failed" in failed
    assert "fetch failed" in failed


def test_render_markdown_lists_files_and_limits_noise() -> None:
    commits = [
        {
            "sha": "b" * 40,
            "short": "bbbbbbb",
            "date": "2026-08-10",
            "subject": "fix: demo | contract",
            "files": [f"src/file_{index}.py" for index in range(10)],
        }
    ]

    report = checker.render_markdown(sample_baseline(), commits)

    assert "1 upstream commit(s) require review" in report
    assert "fix: demo \\| contract" in report
    assert "… +2 more" in report


def test_baseline_matches_decision_log() -> None:
    baseline = checker.load_baseline()
    decisions = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")

    assert baseline["reviewed_date"] in decisions
