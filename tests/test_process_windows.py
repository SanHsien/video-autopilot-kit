from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capcut_helpers import process  # noqa: E402


def _completed(returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def test_process_query_checks_capcut_and_helpers(monkeypatch) -> None:
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return _completed(0, "1\n")

    monkeypatch.setattr(process.subprocess, "run", fake_run)

    assert process.is_capcut_running() is True
    command = calls[0][0][-1]
    assert "CapCut" in command
    assert "CapCutHelper" in command
    assert calls[0][1]["timeout"] == 15


def test_process_query_fails_closed_on_command_error(monkeypatch) -> None:
    monkeypatch.setattr(
        process.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(1, "", "access denied"),
    )

    assert process.is_capcut_running() is True


def test_process_query_fails_closed_when_powershell_is_missing(monkeypatch) -> None:
    def missing_shell(*_args, **_kwargs):
        raise FileNotFoundError("powershell.exe")

    monkeypatch.setattr(process.subprocess, "run", missing_shell)

    assert process.is_capcut_running() is True


def test_safe_kill_never_reports_success_when_kill_fails(monkeypatch) -> None:
    monkeypatch.setattr(process, "kill_capcut_all", lambda: (1, "access denied"))
    monkeypatch.setattr(process, "is_capcut_running", lambda: False)
    monkeypatch.setattr(process.time, "sleep", lambda _seconds: None)

    assert process.safe_kill_then_verify(max_retries=2) is False


def test_safe_kill_handles_missing_powershell_without_false_success(monkeypatch) -> None:
    def missing_shell():
        raise FileNotFoundError("powershell.exe")

    monkeypatch.setattr(process, "kill_capcut_all", missing_shell)
    monkeypatch.setattr(process.time, "sleep", lambda _seconds: None)

    assert process.safe_kill_then_verify(max_retries=1) is False
