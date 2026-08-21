"""Compare the pinned ranges in requirements-*.txt against the latest PyPI releases.

Dependabot proposes upgrades one pull request at a time, which answers "is there a
newer release of this package?" but never "how far behind is the whole runtime?".
This reads every direct requirement this repo declares, asks PyPI for the current
release of each, and writes a Markdown report.

It compares declarations only. Nothing here inspects the installed environment and
nothing here edits a requirements file: a newer release is a prompt to read the
changelog and run the suite, not a merge.

    python tools/check_dependency_freshness.py --output report.md --github-output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "video-autopilot-kit-dependency-freshness"

# Ordered by how much a surprise costs: the runtime the EXE ships first, then the
# optional pipeline, then the tools that only ever run in CI.
REQUIREMENT_FILES = (
    "requirements-path1.txt",
    "requirements-optional.txt",
    "requirements-dev.txt",
    "requirements-build.txt",
)

_REQUIREMENT_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)$")
_MINIMUM_RE = re.compile(r"(>=|>|==|~=)\s*([0-9][0-9A-Za-z.!+_-]*)")
_RELEASE_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*")


class DependencyCheckError(RuntimeError):
    """Raised when a requirements file cannot be read."""


def release_key(version: str) -> tuple[int, ...] | None:
    """Return the numeric release segment of a version, or None if unparsable.

    Pre-release and local suffixes are dropped, so 7.0.0rc1 and 7.0.0 rank the
    same. That is precise enough to answer "has the declared floor aged?" without
    adding a PEP 440 parser to a repo whose runtime is numpy and Pillow.
    """
    match = _RELEASE_RE.match(version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(0).split("."))


def is_newer_version(latest: str, declared: str) -> bool:
    latest_key = release_key(latest)
    declared_key = release_key(declared)
    if latest_key is None or declared_key is None:
        return False
    return latest_key > declared_key


def parse_requirements(text: str, source: str) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        # "-r requirements-path1.txt" is followed separately; expanding it here
        # would list numpy and Pillow twice.
        if not line or line.startswith("-"):
            continue
        head = line.split(";", 1)[0].strip()
        match = _REQUIREMENT_RE.match(head)
        if not match:
            continue
        name, specifiers = match.groups()
        minimum = _MINIMUM_RE.search(specifiers)
        packages.append(
            {
                "name": name,
                "minimum": minimum.group(2) if minimum else "",
                "requirement": line,
                "source": source,
            }
        )
    return packages


def load_direct_dependencies(root: Path = REPO_ROOT) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    seen: set[str] = set()
    for name in REQUIREMENT_FILES:
        path = root / name
        if not path.is_file():
            raise DependencyCheckError(f"missing requirements file: {name}")
        for package in parse_requirements(path.read_text(encoding="utf-8"), name):
            key = package["name"].lower().replace("_", "-")
            if key in seen:
                continue
            seen.add(key)
            packages.append(package)
    return packages


def fetch_pypi_version(package_name: str, timeout: float = 10.0) -> str | None:
    quoted_name = urllib.parse.quote(package_name, safe="")
    request = urllib.request.Request(
        f"https://pypi.org/pypi/{quoted_name}/json",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    version = payload.get("info", {}).get("version")
    return str(version) if version else None


def collect_status(packages: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for package in packages:
        minimum = package["minimum"]
        latest = fetch_pypi_version(package["name"])
        rows.append(
            {
                **package,
                "latest": latest or "unknown",
                "outdated": bool(minimum and latest and is_newer_version(latest, minimum)),
                "check_failed": not minimum or latest is None,
            }
        )
    return rows


def render_markdown(rows: list[dict[str, object]], error: str | None = None) -> str:
    lines = ["# Dependency freshness report", ""]
    if error:
        lines.extend(["## Check failed", "", f"```text\n{error}\n```", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Package | Declared in | Requirement | PyPI latest | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        if row["check_failed"]:
            status = "CHECK FAILED"
        elif row["outdated"]:
            status = "REVIEW UPDATE"
        else:
            status = "OK"
        lines.append(
            f"| `{row['name']}` | `{row['source']}` | `{row['requirement']}` | "
            f"`{row['latest']}` | {status} |"
        )
    if not rows:
        lines.append("| - | - | - | - | CHECK FAILED |")
    lines.extend(
        [
            "",
            "Declared ranges are compared against PyPI. The installed environment is",
            "not inspected and no file is edited by this check.",
            "",
            "## Review policy",
            "",
            "1. Read the release notes, and check the supported Python versions.",
            "2. Run the full test suite plus the Windows EXE build before widening a range.",
            "3. numpy, Pillow, and PyInstaller changes need a real EXE smoke run; CI alone",
            "   cannot prove the portable build still starts.",
            "",
        ]
    )
    return "\n".join(lines)


def write_github_output(rows: list[dict[str, object]], report_path: Path) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    outdated = any(bool(row["outdated"]) for row in rows)
    check_failed = not rows or any(bool(row["check_failed"]) for row in rows)
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"outdated={'true' if outdated else 'false'}\n")
        output.write(f"check_failed={'true' if check_failed else 'false'}\n")
        output.write(
            f"needs_attention={'true' if outdated or check_failed else 'false'}\n"
        )
        output.write(f"report_path={report_path.as_posix()}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dependency-freshness-report.md")
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Write status fields to GITHUB_OUTPUT",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when a declared range has aged.",
    )
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    error: str | None = None
    try:
        rows = collect_status(load_direct_dependencies())
    except DependencyCheckError as exc:
        error = str(exc)

    report = render_markdown(rows, error)
    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(report)

    if args.github_output:
        write_github_output(rows, output_path)
    if error:
        return 2
    if args.strict and any(bool(row["outdated"]) or bool(row["check_failed"]) for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
