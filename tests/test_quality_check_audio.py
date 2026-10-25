from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from silent_vlog_maker.quality_check import verify_output  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not installed",
)


def _encode(path: Path, with_audio: bool) -> Path:
    command = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=64x64:d=1"]
    if with_audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(path)]
    subprocess.run(command, check=True, capture_output=True)
    return path


def test_missing_audio_track_is_reported(tmp_path: Path) -> None:
    result = verify_output(_encode(tmp_path / "silent.mp4", False), expected_outro=False)

    assert any("no audio track" in issue for issue in result["issues"])


def test_missing_audio_can_be_declared_intended(tmp_path: Path) -> None:
    result = verify_output(_encode(tmp_path / "silent.mp4", False),
                           expected_outro=False, expected_audio=False)

    assert not any("audio" in issue for issue in result["issues"])


def test_unreadable_file_is_not_reported_clean(tmp_path: Path) -> None:
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"not a video")

    result = verify_output(broken, expected_outro=False)

    assert any("probe failed" in issue for issue in result["issues"])


def test_audio_track_is_measured(tmp_path: Path) -> None:
    result = verify_output(_encode(tmp_path / "tone.mp4", True), expected_outro=False)

    assert "audio_lra_lu" in result
    assert not any("no audio track" in issue for issue in result["issues"])
