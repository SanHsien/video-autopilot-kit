from __future__ import annotations

from pathlib import Path

import pytest


def test_resolve_media_binaries_requires_ffmpeg_and_ffprobe(tmp_path) -> None:
    from build_exe import resolve_media_binaries

    ffmpeg = tmp_path / "ffmpeg.exe"
    ffprobe = tmp_path / "ffprobe.exe"
    ffmpeg.write_bytes(b"MZ")
    ffprobe.write_bytes(b"MZ")
    found = {"ffmpeg": str(ffmpeg), "ffprobe": str(ffprobe)}

    assert resolve_media_binaries(which=found.get) == (ffmpeg, ffprobe)

    with pytest.raises(RuntimeError, match="ffprobe"):
        resolve_media_binaries(which={"ffmpeg": str(ffmpeg)}.get)


def test_resolve_ffmpeg_notices_requires_distribution_files(tmp_path) -> None:
    from build_exe import resolve_ffmpeg_notices

    root = tmp_path / "ffmpeg"
    binary = root / "bin" / "ffmpeg.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"MZ")
    license_file = root / "LICENSE"
    readme = root / "README.txt"
    license_file.write_text("GPLv3", encoding="utf-8")
    readme.write_text("build configuration", encoding="utf-8")

    assert resolve_ffmpeg_notices(binary) == (license_file, readme)

    readme.unlink()
    with pytest.raises(RuntimeError, match="README"):
        resolve_ffmpeg_notices(binary)


def test_inspect_ffmpeg_build_rejects_nonfree(monkeypatch, tmp_path) -> None:
    import build_exe

    binary = tmp_path / "ffmpeg.exe"
    binary.write_bytes(b"MZ")
    result = type(
        "Result",
        (),
        {"returncode": 0, "stdout": "configuration: --enable-gpl --enable-version3", "stderr": ""},
    )()
    monkeypatch.setattr(build_exe.subprocess, "run", lambda *args, **kwargs: result)
    assert build_exe.inspect_ffmpeg_build(binary) == "GPL-3.0-or-later"

    result.stdout += " --enable-nonfree"
    with pytest.raises(RuntimeError, match="nonfree"):
        build_exe.inspect_ffmpeg_build(binary)


def test_pyinstaller_contract_files_are_declared() -> None:
    root = Path(__file__).parents[1]
    spec = (root / "video_autopilot_path1.spec").read_text(encoding="utf-8")
    build_requirements = (root / "requirements-build.txt").read_text(encoding="utf-8")

    assert "path1_gui.py" in spec
    assert "ffmpeg.exe" in spec
    assert "ffprobe.exe" in spec
    assert "FFmpeg-GPLv3.txt" in spec
    assert "console=False" in spec
    assert (root / "path1_version_info.txt").is_file()
    assert (root / "THIRD_PARTY_NOTICES.md").is_file()
    assert "PyInstaller" in build_requirements
    assert "requirements-path1.txt" in build_requirements
