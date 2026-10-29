from __future__ import annotations

import ast
import re
import sys
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


def test_version_literals_are_synchronized() -> None:
    root = Path(__file__).parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import path1_core

    # 1. path1_core.py
    core_version = path1_core.APP_VERSION
    assert core_version, "path1_core.APP_VERSION 必須為非空字串"

    # 2. build_exe.py: app_version in build_info dict
    build_exe_source = (root / "build_exe.py").read_text(encoding="utf-8")
    tree = ast.parse(build_exe_source, filename="build_exe.py")
    ast_versions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, val in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "app_version":
                    if isinstance(val, ast.Constant):
                        ast_versions.append(val.value)
    assert len(ast_versions) == 1, f"build_exe.py 預期存在單一 app_version，實測找到 {ast_versions}"
    build_exe_version = str(ast_versions[0])

    # 3. path1_version_info.txt
    version_info_text = (root / "path1_version_info.txt").read_text(encoding="utf-8")

    file_version_match = re.search(
        r"StringStruct\([uU]?['\"]FileVersion['\"],\s*[uU]?['\"]([^'\"]+)['\"]\)",
        version_info_text,
    )
    assert file_version_match is not None, "path1_version_info.txt 缺少 FileVersion 定義"
    file_version_str = file_version_match.group(1)

    product_version_match = re.search(
        r"StringStruct\([uU]?['\"]ProductVersion['\"],\s*[uU]?['\"]([^'\"]+)['\"]\)",
        version_info_text,
    )
    assert product_version_match is not None, "path1_version_info.txt 缺少 ProductVersion 定義"
    product_version_str = product_version_match.group(1)

    filevers_match = re.search(
        r"filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", version_info_text
    )
    assert filevers_match is not None, "path1_version_info.txt 缺少 filevers 定義"
    filevers_tuple = tuple(int(x) for x in filevers_match.groups())

    prodvers_match = re.search(
        r"prodvers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", version_info_text
    )
    assert prodvers_match is not None, "path1_version_info.txt 缺少 prodvers 定義"
    prodvers_tuple = tuple(int(x) for x in prodvers_match.groups())

    assert build_exe_version == core_version, (
        f"build_exe.py ({build_exe_version}) != path1_core ({core_version})"
    )
    assert file_version_str == core_version, (
        f"path1_version_info FileVersion ({file_version_str}) != path1_core ({core_version})"
    )
    assert product_version_str == core_version, (
        f"path1_version_info ProductVersion ({product_version_str}) != path1_core ({core_version})"
    )

    parts = [int(p) for p in core_version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    expected_tuple = tuple(parts[:4])

    assert filevers_tuple == expected_tuple, (
        f"path1_version_info filevers ({filevers_tuple}) != ({expected_tuple})"
    )
    assert prodvers_tuple == expected_tuple, (
        f"path1_version_info prodvers ({prodvers_tuple}) != ({expected_tuple})"
    )
