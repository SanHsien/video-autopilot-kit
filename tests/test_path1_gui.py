from __future__ import annotations

import importlib
import json


def test_gui_import_does_not_create_window() -> None:
    module = importlib.import_module("path1_gui")

    assert hasattr(module, "Path1GUI")
    assert hasattr(module, "launch")
    assert module.APP_VERSION


def test_gui_exposes_all_primary_path1_workflows() -> None:
    from path1_gui import WORKFLOWS

    assert set(WORKFLOWS) == {
        "shorts_scan",
        "shorts_build",
        "teardown",
        "delivery_qa",
        "screen_clean",
        "health",
    }


def test_write_diagnostics_records_real_dependency_sources(tmp_path, monkeypatch) -> None:
    import path1_gui

    status = {
        "ffmpeg": {"ok": True, "path": "bundle/bin/ffmpeg.exe", "version": "9.0"},
        "ffprobe": {"ok": True, "path": "bundle/bin/ffprobe.exe", "version": "9.0"},
    }
    monkeypatch.setattr(path1_gui, "dependency_status", lambda: status)
    output = tmp_path / "diagnostics.json"

    assert path1_gui.write_diagnostics(output) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["app_version"] == path1_gui.APP_VERSION
    assert payload["dependencies"] == status
