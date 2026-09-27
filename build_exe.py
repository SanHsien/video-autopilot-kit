#!/usr/bin/env python3
"""建置包含 Path 1 Python 套件與 ffmpeg/ffprobe 的 Windows 單檔 EXE。"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "video_autopilot_path1.spec"
OUTPUT = ROOT / "dist" / "video-autopilot-path1.exe"


def resolve_media_binaries(
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[Path, Path]:
    """找出建置時要內嵌的兩支媒體工具；少任何一支都停止。"""

    resolved = []
    for name in ("ffmpeg", "ffprobe"):
        raw = which(name)
        if not raw or not Path(raw).is_file():
            raise RuntimeError(
                f"找不到 {name}；請先安裝 ffmpeg 並確認 ffmpeg/ffprobe 都在 PATH"
            )
        resolved.append(Path(raw).resolve())
    return resolved[0], resolved[1]


def resolve_ffmpeg_notices(ffmpeg: Path) -> tuple[Path, Path]:
    """尋找 Gyan/FFmpeg binary distribution 隨附的授權與建置說明。"""

    for distribution_root in list(ffmpeg.parents)[:4]:
        license_file = distribution_root / "LICENSE"
        readme = distribution_root / "README.txt"
        if license_file.is_file() and readme.is_file():
            return license_file, readme
    raise RuntimeError("FFmpeg distribution 缺少 LICENSE 或 README.txt")


def inspect_ffmpeg_build(ffmpeg: Path) -> str:
    """拒絕不可再散布的 nonfree build，並回傳本次套用的 FFmpeg license。"""

    result = subprocess.run(
        [str(ffmpeg), "-version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    if result.returncode:
        raise RuntimeError("無法讀取 ffmpeg build configuration")
    output = result.stdout + result.stderr
    if "--enable-nonfree" in output:
        raise RuntimeError("拒絕封裝 --enable-nonfree 的 FFmpeg build")
    if "--enable-gpl" in output:
        return "GPL-3.0-or-later" if "--enable-version3" in output else "GPL-2.0-or-later"
    return "LGPL-3.0-or-later" if "--enable-version3" in output else "LGPL-2.1-or-later"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if sys.platform != "win32":
        print("PyInstaller 不提供跨平台編譯；請在 Windows 建置這個 EXE。")
        return 2
    ffmpeg, ffprobe = resolve_media_binaries()
    ffmpeg_license, ffmpeg_readme = resolve_ffmpeg_notices(ffmpeg)
    license_id = inspect_ffmpeg_build(ffmpeg)
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "VAK_FFMPEG": str(ffmpeg),
            "VAK_FFPROBE": str(ffprobe),
            "VAK_FFMPEG_LICENSE": str(ffmpeg_license),
            "VAK_FFMPEG_README": str(ffmpeg_readme),
        }
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(SPEC),
        "--noconfirm",
        "--clean",
    ]
    print("Building:", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, env=env)
    if result.returncode:
        return result.returncode
    if not OUTPUT.is_file() or OUTPUT.stat().st_size < 1_000_000:
        print(f"建置失敗：產物不存在或過小：{OUTPUT}")
        return 1
    shutil.copy2(ffmpeg_license, OUTPUT.parent / "FFmpeg-GPLv3.txt")
    shutil.copy2(ffmpeg_readme, OUTPUT.parent / "FFmpeg-BUILD-README.txt")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", OUTPUT.parent / "THIRD_PARTY_NOTICES.md")
    build_info = {
        "app_version": "0.13.0",
        "artifact": OUTPUT.name,
        "artifact_bytes": OUTPUT.stat().st_size,
        "artifact_sha256": _sha256(OUTPUT),
        "ffmpeg": {"path": str(ffmpeg), "license": license_id, "sha256": _sha256(ffmpeg)},
        "ffprobe": {"path": str(ffprobe), "license": license_id, "sha256": _sha256(ffprobe)},
    }
    (OUTPUT.parent / "path1-build-info.json").write_text(
        json.dumps(build_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Bundled FFmpeg license: {license_id}")
    print(f"Done: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
