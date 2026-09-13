"""
capcut_helpers.process — Kill CapCut Desktop processes (M20 防 auto-save 覆蓋).

CapCut Windows 預設 minimize-to-tray — 「關視窗」≠「完全 quit」。
8 個 process（CapCut.exe + helper processes）必須全部 kill 才能安全 edit JSON。
"""
import subprocess
import time

_POWERSHELL_TIMEOUT_SEC = 15


def kill_capcut_all() -> tuple[int, str]:
    """Kill all CapCut.exe + helper processes via PowerShell.

    Returns:
        (return_code, stdout) — 0 if success or no processes running.

    M20: must run BEFORE editing draft JSON externally. Otherwise CapCut's
    auto-save (cached in-memory state) will overwrite your file on next save.
    """
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$ErrorActionPreference='Stop'; "
         "Get-Process -Name CapCut,CapCutHelper -ErrorAction SilentlyContinue | "
         "Stop-Process -Force -ErrorAction Stop"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_POWERSHELL_TIMEOUT_SEC,
    )
    return result.returncode, result.stdout + result.stderr


def is_capcut_running() -> bool:
    """Check if any CapCut process is alive (post-kill verification)."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "@(Get-Process -Name CapCut,CapCutHelper "
             "-ErrorAction SilentlyContinue).Count"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_POWERSHELL_TIMEOUT_SEC,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    if result.returncode != 0:
        return True
    try:
        return int(result.stdout.strip()) > 0
    except (ValueError, AttributeError):
        return True


def safe_kill_then_verify(max_retries: int = 3) -> bool:
    """Kill + verify dead. Retry up to N times.

    Returns True if successfully killed all processes, False otherwise.
    """
    for _attempt in range(max_retries):
        try:
            return_code, _output = kill_capcut_all()
        except (OSError, subprocess.SubprocessError):
            return_code = 1
        time.sleep(1.5)
        if return_code == 0 and not is_capcut_running():
            return True
    return False
