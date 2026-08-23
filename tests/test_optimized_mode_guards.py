from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _run_optimized(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return subprocess.run(
        [sys.executable, "-O", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
    )


def test_shorts_scan_guard_survives_python_optimized_mode(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "import shorts_autopilot as app; "
        f"app.INBOX = {str(inbox)!r}; "
        "app.scan('missing')"
    )

    result = _run_optimized(code)

    assert result.returncode != 0
    assert "找不到素材資料夾" in result.stderr


def test_template_placeholder_guard_survives_python_optimized_mode(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "demo.template.md").write_text("來賓：((來賓))", encoding="utf-8")
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "import interview_autopilot as app; "
        f"app.TPL_DIR = {str(templates)!r}; "
        "app.render('demo')"
    )

    result = _run_optimized(code)

    assert result.returncode != 0
    assert "有未填欄位" in result.stderr
