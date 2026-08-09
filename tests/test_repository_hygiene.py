from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_maintenance_skeleton_is_complete() -> None:
    required = [
        ".editorconfig",
        ".gitattributes",
        ".pre-commit-config.yaml",
        ".github/dependabot.yml",
        ".github/pull_request_template.md",
        ".github/workflows/ci.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/upstream-check.yml",
        "AGENTS.md",
        "CLAUDE.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "FORK.md",
        "SECURITY.md",
        "docs/DECISIONS.md",
        "docs/DEVELOPMENT.md",
        "docs/INTEGRATIONS.md",
        "docs/UPSTREAM.md",
        "requirements-dev.txt",
        "requirements-optional.txt",
        "tools/check_upstream_updates.py",
        "tools/dev_check.ps1",
        "tools/upstream_baseline.json",
    ]

    missing = [item for item in required if not (ROOT / item).is_file()]
    assert not missing, f"missing maintenance files: {missing}"


def test_private_and_generated_content_is_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in (
        "profiles/",
        "config.py",
        "*.mp4",
        "*.wav",
        ".venv/",
        "*draft_content.json",
        "interview_EP*/",
    ):
        assert pattern in gitignore


def test_fork_identity_is_transparent() -> None:
    fork = (ROOT / "FORK.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Hao0321/video-autopilot-kit" in fork
    assert "MIT" in fork
    assert "FORK.md" in readme
