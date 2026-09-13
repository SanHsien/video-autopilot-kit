from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]


def test_configure_bundled_tools_prepends_bin_directory(tmp_path, monkeypatch) -> None:
    from path1_core import configure_bundled_tools

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    suffix = ".exe" if os.name == "nt" else ""
    (bin_dir / f"ffmpeg{suffix}").write_bytes(b"MZ")
    (bin_dir / f"ffprobe{suffix}").write_bytes(b"MZ")
    monkeypatch.setenv("PATH", str(tmp_path / "system"))

    resolved = configure_bundled_tools(tmp_path)

    assert resolved == bin_dir
    assert str(bin_dir) == os.environ["PATH"].split(os.pathsep)[0]


def test_configure_bundled_tools_is_optional_in_source_mode(tmp_path) -> None:
    from path1_core import configure_bundled_tools

    assert configure_bundled_tools(tmp_path) is None


def test_validate_short_project_requires_plan_only_for_build(tmp_path) -> None:
    from path1_core import validate_short_project

    project = tmp_path / "short-001"
    project.mkdir()
    assert validate_short_project(project, "scan") == project.resolve()

    with pytest.raises(ValueError, match="_plan.py"):
        validate_short_project(project, "build")

    (project / "_plan.py").write_text("SPEC = {}", encoding="utf-8")
    assert validate_short_project(project, "build") == project.resolve()

    with pytest.raises(ValueError, match="未知"):
        validate_short_project(project, "publish")
    with pytest.raises(ValueError, match="不存在"):
        validate_short_project(tmp_path / "missing", "scan")


def test_run_short_job_reuses_existing_autopilot_api(tmp_path) -> None:
    from path1_core import run_short_job

    project = tmp_path / "short-002"
    project.mkdir()
    (project / "_plan.py").write_text("SPEC = {}", encoding="utf-8")
    bgm = tmp_path / "bgm"
    bgm.mkdir()
    calls: list[tuple] = []
    module = SimpleNamespace(
        scan=lambda name, inbox=None: calls.append(("scan", name, inbox)) or {"clips": []},
        build=lambda name, inbox=None, bgm_root=None: calls.append(
            ("build", name, inbox, bgm_root)
        )
        or {"all_green": True},
    )

    scan_result = run_short_job("scan", project, module=module)
    build_result = run_short_job("build", project, bgm, module=module)

    assert calls == [
        ("scan", "short-002", str(tmp_path.resolve())),
        ("build", "short-002", str(tmp_path.resolve()), str(bgm.resolve())),
    ]
    assert scan_result.ok is True
    assert build_result.ok is True
    assert build_result.output_dir == project.resolve() / "_out"


def test_shorts_defaults_follow_public_environment_contract(tmp_path, monkeypatch) -> None:
    inbox = tmp_path / "inbox"
    bgm = tmp_path / "bgm"
    monkeypatch.setenv("VIDEO_KIT_SHORTS_INBOX", str(inbox))
    monkeypatch.setenv("VIDEO_KIT_BGM_ROOT", str(bgm))
    spec = importlib.util.spec_from_file_location(
        "shorts_autopilot_defaults_test", ROOT / "src" / "shorts_autopilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.INBOX == str(inbox)
    assert module.BGM_ROOT == str(bgm)
    assert "creator0321" not in (ROOT / "src" / "shorts_autopilot.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("band", ["wide", "top", "mid", "bottom"])
def test_parse_teardown_options_accepts_supported_bands(tmp_path, band) -> None:
    from path1_core import parse_teardown_options

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    target, parsed_band, threshold = parse_teardown_options(video, band, "0.25")

    assert target == video.resolve()
    assert parsed_band == band
    assert threshold == 0.25


def test_parse_teardown_options_rejects_invalid_threshold(tmp_path) -> None:
    from path1_core import parse_teardown_options

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="0 到 1"):
        parse_teardown_options(video, "wide", "2")
    with pytest.raises(ValueError, match="必須是數字"):
        parse_teardown_options(video, "wide", "abc")
    with pytest.raises(ValueError, match="字幕區域"):
        parse_teardown_options(video, "side", "0.2")
    with pytest.raises(ValueError, match="不存在"):
        parse_teardown_options(tmp_path / "missing.mp4", "wide", "0.2")


def test_run_teardown_job_processes_folder_mp4_files(tmp_path) -> None:
    from path1_core import run_teardown_job

    first = tmp_path / "a.mp4"
    second = tmp_path / "nested" / "b.mp4"
    first.write_bytes(b"video")
    second.parent.mkdir()
    second.write_bytes(b"video")
    calls = []
    module = SimpleNamespace(
        teardown=lambda path, band, threshold: calls.append((path, band, threshold))
    )

    result = run_teardown_job(tmp_path, "wide", 0.3, module=module)

    assert [Path(item[0]).name for item in calls] == ["a.mp4", "b.mp4"]
    assert all(item[1:] == ("wide", 0.3) for item in calls)
    assert result.ok is True
    assert result.details["videos"] == 2


def test_run_teardown_job_rejects_empty_folder(tmp_path) -> None:
    from path1_core import run_teardown_job

    with pytest.raises(ValueError, match="找不到 MP4"):
        run_teardown_job(tmp_path, "wide", 0.25, module=SimpleNamespace())


def test_parse_screen_clean_options_validates_crop_and_trim(tmp_path) -> None:
    from path1_core import parse_screen_clean_options

    source = tmp_path / "capture.mp4"
    source.write_bytes(b"video")
    output = tmp_path / "clean.mp4"

    parsed = parse_screen_clean_options(source, output, "1920:930:0:100", "1", "2")
    assert parsed[0] == source.resolve()
    assert parsed[1] == output.resolve()
    assert parsed[2:] == ("1920:930:0:100", 1.0, 2.0)

    with pytest.raises(ValueError, match="W:H:X:Y"):
        parse_screen_clean_options(source, output, "bad", "1", "2")
    with pytest.raises(ValueError, match="至少 1 秒"):
        parse_screen_clean_options(source, output, "1920:930:0:100", "0.5", "2")
    with pytest.raises(ValueError, match=".mp4"):
        parse_screen_clean_options(source, tmp_path / "clean.mov", "1920:930:0:100", "1", "2")
    with pytest.raises(ValueError, match="必須是數字"):
        parse_screen_clean_options(source, output, "1920:930:0:100", "one", "2")


def test_run_screen_clean_job_calls_existing_core(tmp_path) -> None:
    from path1_core import run_screen_clean_job

    source = tmp_path / "capture.mp4"
    source.write_bytes(b"video")
    output = tmp_path / "out" / "clean.mp4"
    calls = []
    module = SimpleNamespace(
        clean_screen_recording=lambda *args, **kwargs: calls.append((args, kwargs))
    )

    result = run_screen_clean_job(
        source, output, "1920:930:0:100", 1.0, 2.0, module=module
    )

    assert calls[0][0] == (str(source), str(output), "1920:930:0:100")
    assert calls[0][1] == {"head_trim": 1.0, "tail_trim": 2.0}
    assert result.output_dir == output.parent


def test_run_delivery_qa_creates_evidence_paths(tmp_path) -> None:
    from path1_core import run_delivery_qa_job

    video = tmp_path / "finished.mp4"
    video.write_bytes(b"video")
    calls = []

    def fake_qa(path, **kwargs):
        calls.append((path, kwargs))
        return {"deliver_ok": True}

    result = run_delivery_qa_job(
        video,
        check_audio=True,
        module=SimpleNamespace(final_delivery_qa=fake_qa),
    )

    evidence = tmp_path / "finished_path1_qa"
    assert calls[0][0] == str(video.resolve())
    assert calls[0][1]["audio"] is True
    assert calls[0][1]["contact_out"] == str(evidence / "contact_sheet.jpg")
    assert calls[0][1]["sheets_dir"] == str(evidence / "fullframe")
    assert result.ok is True
    assert result.output_dir == evidence


def test_run_delivery_qa_preserves_blocking_result(tmp_path) -> None:
    from path1_core import run_delivery_qa_job

    video = tmp_path / "blocked.mp4"
    video.write_bytes(b"video")
    module = SimpleNamespace(final_delivery_qa=lambda *args, **kwargs: {"deliver_ok": False})

    result = run_delivery_qa_job(video, check_audio=False, module=module)

    assert result.ok is False
    assert "阻擋" in result.message


def test_settings_round_trip_uses_explicit_path(tmp_path) -> None:
    from path1_core import load_settings, save_settings

    target = tmp_path / "settings.json"
    payload = {"project_dir": "C:/素材", "bgm_dir": "D:/bgm"}
    save_settings(payload, target)

    assert load_settings(target) == payload
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    target.write_text("not json", encoding="utf-8")
    assert load_settings(target) == {}


def test_dependency_status_reports_core_packages_and_tools(monkeypatch) -> None:
    import path1_core

    fake = SimpleNamespace(stdout="ffmpeg version test\n", stderr="", returncode=0)
    monkeypatch.setitem(sys.modules, "numpy", SimpleNamespace(__version__="test"))
    monkeypatch.setitem(sys.modules, "PIL", SimpleNamespace(__version__="test"))
    monkeypatch.setattr(path1_core.shutil, "which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr(path1_core.subprocess, "run", lambda *args, **kwargs: fake)

    status = path1_core.dependency_status()

    assert set(status) == {"ffmpeg", "ffprobe", "numpy", "Pillow"}
    assert all(item["ok"] for item in status.values())
