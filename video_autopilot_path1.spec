# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows-first Path 1 desktop application."""
import os
import sys

from PyInstaller.utils.hooks import collect_submodules


sys.path.insert(0, os.path.abspath("src"))
ffmpeg = os.environ.get("VAK_FFMPEG", "ffmpeg.exe")
ffprobe = os.environ.get("VAK_FFPROBE", "ffprobe.exe")
ffmpeg_license = os.environ.get("VAK_FFMPEG_LICENSE", "FFmpeg-GPLv3.txt")
ffmpeg_readme = os.environ.get("VAK_FFMPEG_README", "FFmpeg-BUILD-README.txt")
binaries = [(ffmpeg, "bin"), (ffprobe, "bin")]
hiddenimports = [
    "shorts_autopilot",
    "teardown",
    "system_health",
    *collect_submodules("silent_vlog_maker"),
    *collect_submodules("longform_maker"),
    *collect_submodules("capcut_helpers"),
]

a = Analysis(
    ["path1_gui.py"],
    pathex=[".", "src"],
    binaries=binaries,
    datas=[
        ("LICENSE", "licenses"),
        ("THIRD_PARTY_NOTICES.md", "licenses"),
        (ffmpeg_license, "licenses/ffmpeg"),
        (ffmpeg_readme, "licenses/ffmpeg"),
        ("README.md", "."),
        ("README.en.md", "."),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["rapidocr_onnxruntime", "onnxruntime", "opencc", "cv2"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="video-autopilot-path1",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version="path1_version_info.txt",
)
