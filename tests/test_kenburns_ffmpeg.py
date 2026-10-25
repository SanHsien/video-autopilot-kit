from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from silent_vlog_maker.effects import kenburns_pan_right, kenburns_zoom_in  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture(scope="module")
def still(tmp_path_factory: pytest.TempPathFactory) -> str:
    path = str(tmp_path_factory.mktemp("kenburns") / "still.png")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
         "color=c=0x202020:s=800x600,format=gray,"
         "geq=lum='if(lte(hypot(X-400,Y-300),60),235,32)'",
         "-frames:v", "1", path],
        check=True, capture_output=True,
    )
    return path


@pytest.mark.parametrize("build", [kenburns_zoom_in, kenburns_pan_right])
@pytest.mark.parametrize("scale", ["360:640", "640:360"])
def test_kenburns_filter_runs_and_keeps_moving(still: str, build, scale: str) -> None:
    width, height = (int(value) for value in scale.split(":"))
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", still, "-vf", build(1.0, 30, scale) + ",format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")[-300:]
    frame = width * height
    assert len(result.stdout) == 30 * frame
    assert result.stdout[-frame:] != result.stdout[-2 * frame:-frame]
