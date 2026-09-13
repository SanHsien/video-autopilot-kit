from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def test_shorts_gate_quickstart_runs() -> None:
    result = run_script("examples/04_shorts_gate.py")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK -- all four gate scenarios behaved as expected" in result.stdout


@pytest.mark.parametrize(
    ("script", "marker"),
    [
        ("examples/05_interview_plan.py", "OK -- interview_gate demo passed"),
        ("examples/06_teardown.py", "OK -- teardown demo passed"),
    ],
)
def test_pure_python_examples_run(script: str, marker: str) -> None:
    result = run_script(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker in result.stdout


def test_quick_system_health_runs_in_cjk_workspace() -> None:
    result = run_script("src/system_health.py", "--quick")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "HEALTH GREEN" in result.stdout
