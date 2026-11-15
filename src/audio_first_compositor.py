"""Local audio-first green-screen compositor (stdlib + ffmpeg/ffprobe).

Short visuals/BGM loop; narration defines the timeline. Output is always a new MP4.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import tempfile
from pathlib import Path

try:
    from .av_util import run
except ImportError:  # direct CLI
    from av_util import run


def probe(path: Path) -> dict:
    """Read streams, failing closed on invalid or missing media."""
    result = run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)])
    if result.returncode:
        raise ValueError(f"Cannot probe {path.name}: {result.stderr.strip()}")
    return json.loads(result.stdout)


# Pixel formats that already carry transparency. chromakey replaces the alpha plane, so
# transparent areas would silently turn opaque (usually black) instead of showing the
# background.
_ALPHA_PIX_FMT = re.compile(r"(yuva|gbrap|ya\d|argb|rgba|abgr|bgra|ayuv|vuya)")


def compose(
    narration,
    greenscreen,
    background,
    bgm,
    output,
    *,
    fps=30,
    width=1280,
    height=720,
    key="0x00FF00",
    similarity=0.15,
    blend=0.05,
    despill=0.5,
    bgm_gain=0.25,
    duck_threshold=0.02,
    duck_ratio=12,
):
    """Composite local media; reject existing output and preserve all inputs.

    ``despill`` is passed to ffmpeg's despill ``mix`` option (how the spill map weighs
    red against blue); 0 is a valid mix, not "off". Pass ``despill=None`` to skip the
    despill filter entirely.

    Raises ValueError/OSError on invalid input or failed encoding. No shell, network
    service, overwrite flag, or third-party Python runtime dependency is used.
    """
    if not isinstance(fps, int) or isinstance(fps, bool) or not 1 <= fps <= 120:
        raise ValueError("fps must be an integer in 1..120")
    for size in (width, height):
        if not isinstance(size, int) or isinstance(size, bool) or size < 2 or size % 2:
            raise ValueError("width/height must be positive even integers")
    for name, value, low, high in (
        ("similarity", similarity, 0.01, 1),
        ("blend", blend, 0, 1),
        ("despill", 0.5 if despill is None else despill, 0, 1),
        ("bgm_gain", bgm_gain, 0, 1),
        ("duck_threshold", duck_threshold, 0.000976563, 1),
        ("duck_ratio", duck_ratio, 1, 20),
    ):
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not low <= value <= high
        ):
            raise ValueError(f"Invalid {name}")
    if not isinstance(key, str) or not re.fullmatch(r"0x[0-9A-Fa-f]{6}", key):
        raise ValueError("key must be 0xRRGGBB")
    names = ("narration", "greenscreen", "background", "bgm")
    paths = []
    for name, value in zip(names, (narration, greenscreen, background, bgm)):
        # Own ASCII message: the OS text is localized and garbles on legacy consoles.
        if not Path(value).is_file():
            raise FileNotFoundError(f"Input not found ({name}): {Path(value).name!a}")
        paths.append(Path(value).resolve(strict=True))
    destination = Path(output).absolute()
    if destination.suffix.lower() != ".mp4":
        raise ValueError("Output must be .mp4")
    if not destination.parent.is_dir():
        raise ValueError("Output directory does not exist")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Output already exists; refusing to overwrite")
    metadata = [probe(p) for p in paths]
    for data, kind in zip(metadata, ("audio", "video", "video", "audio")):
        if not any(s.get("codec_type") == kind for s in data.get("streams", [])):
            raise ValueError(f"Input requires {'an' if kind == 'audio' else 'a'} {kind} stream")
    green = next(s for s in metadata[1]["streams"] if s["codec_type"] == "video")
    if _ALPHA_PIX_FMT.match(str(green.get("pix_fmt", ""))):
        raise ValueError(
            f"Green-screen input already has an alpha channel ({green['pix_fmt']}); "
            "chromakey would discard it. Flatten it onto the key colour first"
        )
    audio = next(s for s in metadata[0]["streams"] if s["codec_type"] == "audio")
    duration = float(audio.get("duration", 0))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Narration must have a positive, known audio-stream duration")
    # Ceil to a whole frame; video/MP4 duration differs by less than one frame.
    frames = math.ceil(duration * fps - 1e-9)
    timeline = frames / fps
    graph = (
        f"[1:v:0]fps={fps},scale={width}:{height},setsar=1,setpts=PTS-STARTPTS,"
        f"format=yuva444p,chromakey={key}:{similarity}:{blend},format=rgba"
        + ("" if despill is None else f",despill=type=green:mix={despill}")
        + "[fg];"
        f"[2:v:0]fps={fps},scale={width}:{height},setsar=1,setpts=PTS-STARTPTS[bg];"
        "[bg][fg]overlay=shortest=1,format=yuv420p[v];"
        f"[0:a:0]aresample=48000,asetpts=PTS-STARTPTS,apad,atrim=duration={timeline},"
        "asplit=2[voice][control];"
        f"[3:a:0]aresample=48000,asetpts=PTS-STARTPTS,volume={bgm_gain}[music];"
        f"[music][control]sidechaincompress=threshold={duck_threshold}:"
        f"ratio={duck_ratio}:attack=5:release=100:level_sc=4[ducked];"
        f"[voice][ducked]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=0:"
        f"latency=1,atrim=duration={timeline}[a]"
    )
    # Encode privately first. Exclusive creation below also protects a racing writer.
    with tempfile.TemporaryDirectory(prefix=".audio-first-", dir=destination.parent) as tmp:
        staged = Path(tmp) / "encoded.mp4"
        command = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(paths[0])]
        for path in paths[1:]:
            command += ["-stream_loop", "-1", "-i", str(path)]
        command += [
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            str(timeline),
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(staged),
        ]
        result = run(command)
        if result.returncode:
            raise ValueError(f"Encoding failed: {result.stderr.strip()}")
        # "xb" raising means someone else owns the path: never touch it. Once it
        # succeeds the file is ours, so any later failure removes the partial copy.
        with destination.open("xb") as target:
            try:
                with staged.open("rb") as source:
                    shutil.copyfileobj(source, target)
            except BaseException:
                target.close()
                destination.unlink(missing_ok=True)
                raise
    return {
        "narration_seconds": duration,
        "timeline_seconds": timeline,
        "frames": frames,
        "fps": fps,
        "width": width,
        "height": height,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("narration", "greenscreen", "background", "bgm", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    for name, default in (
        ("similarity", 0.15),
        ("blend", 0.05),
        ("despill", 0.5),
        ("bgm-gain", 0.25),
        ("duck-threshold", 0.02),
        ("duck-ratio", 12),
    ):
        parser.add_argument("--" + name, type=float, default=default)
    parser.add_argument("--key", default="0x00FF00")
    parser.add_argument("--no-despill", action="store_true", help="skip the despill filter")
    options = vars(parser.parse_args())
    if options.pop("no_despill"):
        options["despill"] = None
    try:
        print(json.dumps(compose(**options), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
