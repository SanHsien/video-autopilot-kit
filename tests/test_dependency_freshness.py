from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_dependency_freshness as checker  # noqa: E402


def test_declared_requirement_files_all_exist() -> None:
    for name in checker.REQUIREMENT_FILES:
        assert (ROOT / name).is_file(), name


def test_parse_requirements_skips_comments_includes_and_markers() -> None:
    text = "\n".join(
        [
            "# Path 1 runtime",
            "",
            "-r requirements-path1.txt",
            "numpy>=1.26",
            "Pillow>=10  # burned-in captions",
            "pywin32>=306; sys_platform == 'win32'",
        ]
    )

    packages = checker.parse_requirements(text, "requirements-demo.txt")

    assert [package["name"] for package in packages] == ["numpy", "Pillow", "pywin32"]
    assert [package["minimum"] for package in packages] == ["1.26", "10", "306"]
    assert packages[0]["source"] == "requirements-demo.txt"


def test_load_direct_dependencies_lists_each_package_once() -> None:
    packages = checker.load_direct_dependencies()
    names = [package["name"].lower() for package in packages]

    assert len(names) == len(set(names))
    # requirements-build.txt pulls in requirements-path1.txt with -r; numpy must
    # not be reported twice because of it.
    assert names.count("numpy") == 1


def test_load_direct_dependencies_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(checker.DependencyCheckError, match="missing requirements file"):
        checker.load_direct_dependencies(tmp_path)


def test_release_key_ignores_prerelease_and_rejects_junk() -> None:
    assert checker.release_key("7.0.0rc1") == (7, 0, 0)
    assert checker.release_key("1.26") == (1, 26)
    assert checker.release_key("not-a-version") is None


def test_is_newer_version_compares_release_segments() -> None:
    assert checker.is_newer_version("2.5.2", "1.26")
    assert checker.is_newer_version("10.0", "9.9.9")
    assert not checker.is_newer_version("1.26", "1.26")
    assert not checker.is_newer_version("1.25", "1.26")
    assert not checker.is_newer_version("unknown", "1.26")


def test_is_newer_version_respects_the_declared_precision() -> None:
    # "Pillow>=10" claims nothing about the minor, so 10.4.0 is not a finding;
    # 12.3.0 still is.
    assert not checker.is_newer_version("10.4.0", "10")
    assert checker.is_newer_version("12.3.0", "10")
    # "rapidocr-onnxruntime>=1.4" is satisfied by 1.4.4 at its own precision.
    assert not checker.is_newer_version("1.4.4", "1.4")
    assert checker.is_newer_version("1.5.0", "1.4")


def test_render_markdown_marks_each_status() -> None:
    rows: list[dict[str, object]] = [
        {
            "name": "numpy",
            "source": "requirements-path1.txt",
            "requirement": "numpy>=1.26",
            "minimum": "1.26",
            "latest": "2.5.2",
            "outdated": True,
            "check_failed": False,
        },
        {
            "name": "Pillow",
            "source": "requirements-path1.txt",
            "requirement": "Pillow>=10",
            "minimum": "10",
            "latest": "10",
            "outdated": False,
            "check_failed": False,
        },
        {
            "name": "ghost",
            "source": "requirements-dev.txt",
            "requirement": "ghost",
            "minimum": "",
            "latest": "unknown",
            "outdated": False,
            "check_failed": True,
        },
    ]

    report = checker.render_markdown(rows)

    assert "REVIEW UPDATE" in report
    assert "| OK |" in report
    assert "CHECK FAILED" in report


def test_render_markdown_reports_the_error_instead_of_a_table() -> None:
    report = checker.render_markdown([], error="missing requirements file: x.txt")

    assert "Check failed" in report
    assert "missing requirements file: x.txt" in report
    assert "| Package |" not in report
