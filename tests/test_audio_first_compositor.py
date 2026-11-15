"""Synthetic, offline acceptance checks; no downloaded media or Python packages."""

import array
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.audio_first_compositor import compose, probe

REPO_ROOT = Path(__file__).resolve().parents[1]


def ffmpeg(*args):
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", *map(str, args)],
        capture_output=True,
        check=True,
    )
    return result.stdout


def tone(path, frequency, duration, active=lambda t: True):
    samples = array.array(
        "h",
        (
            round(6553 * math.sin(2 * math.pi * frequency * i / 48000)) if active(i / 48000) else 0
            for i in range(round(48000 * duration))
        ),
    )
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        stream.writeframes(samples.tobytes())


@pytest.fixture
def media(tmp_path):
    if not all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe")):
        pytest.skip("ffmpeg/ffprobe missing; real-media DoD NOT verified")
    voice, fg, bg, music = [
        tmp_path / name for name in ("voice.wav", "green.mp4", "blue.mp4", "music.wav")
    ]
    tone(voice, 440, 4.013, lambda t: 1 <= t < 3)
    tone(music, 1000, 0.5)
    for path, color, extra in (
        (fg, "0x00ff00", ["-vf", "drawbox=x=48:y=32:w=64:h=64:color=red:t=fill"]),
        (bg, "blue", []),
    ):
        ffmpeg(
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=160x128:r=30:d=0.5",
            *extra,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            path,
        )
    return [voice, fg, bg, music]


def clip(path, source, *extra, codec=("-c:v", "libx264", "-pix_fmt", "yuv420p")):
    ffmpeg("-f", "lavfi", "-i", f"{source}:s=160x128:r=30:d=0.5", *extra, *codec, path)


def pixel_at(video, x, y, second=2):
    rgb = ffmpeg(
        "-ss", second, "-i", video, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    )
    return tuple(rgb[(y * 160 + x) * 3 : (y * 160 + x) * 3 + 3])


def decode_pcm(video):
    pcm = array.array(
        "f", ffmpeg("-i", video, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-")
    )
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm


def ducking_db(video):
    """BGM (1 kHz) level before narration relative to during narration."""
    pcm = decode_pcm(video)
    return 20 * math.log10(
        spectral_amplitude(pcm, 0.3, 0.8, 1000) / spectral_amplitude(pcm, 1.5, 2.5, 1000)
    )


def spectral_amplitude(samples, start, end, frequency):
    section = samples[round(start * 48000) : round(end * 48000)]
    real = sum(v * math.cos(2 * math.pi * frequency * i / 48000) for i, v in enumerate(section))
    imag = sum(v * math.sin(2 * math.pi * frequency * i / 48000) for i, v in enumerate(section))
    return 2 * math.hypot(real, imag) / len(section)


def test_synthetic_acceptance(media, tmp_path):
    output = tmp_path / "result.mp4"
    result = compose(*media, output, width=160, height=128)
    metadata = probe(output)
    (video,) = [s for s in metadata["streams"] if s["codec_type"] == "video"]
    (audio,) = [s for s in metadata["streams"] if s["codec_type"] == "audio"]
    container = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_format", "-of", "json", str(output)]
        )
    )["format"]
    assert abs(float(container["duration"]) - result["narration_seconds"]) <= 1 / 30
    assert abs(float(video["duration"]) - result["narration_seconds"]) <= 1 / 30
    # AAC priming/padding may extend the audio stream; it must still stay within one frame.
    assert abs(float(audio["duration"]) - result["narration_seconds"]) <= 1 / 30
    assert int(video["nb_frames"]) == result["frames"] == 121
    assert video["r_frame_rate"] == "30/1"
    assert (video["width"], video["height"]) == (160, 128)
    assert (video["codec_name"], video["pix_fmt"], audio["codec_name"]) == (
        "h264",
        "yuv420p",
        "aac",
    )
    ffmpeg("-xerror", "-i", output, "-f", "null", "-")
    pixels = {}
    for name, x, y, expected in (
        ("foreground", 80, 64, (255, 0, 0)),
        ("background", 16, 16, (0, 0, 255)),
    ):
        pixel = pixel_at(output, x, y)
        assert all(abs(a - b) <= 20 for a, b in zip(pixel, expected)), pixel
        pixels[name] = pixel
    pcm = decode_pcm(output)
    quiet = spectral_amplitude(pcm, 0.3, 0.8, 1000)
    speech = spectral_amplitude(pcm, 1.5, 2.5, 1000)
    recovered = spectral_amplitude(pcm, 3.5, 3.9, 1000)
    reduction = 20 * math.log10(quiet / speech)
    assert reduction >= 6
    assert reduction == pytest.approx(ducking_db(output))
    assert abs(20 * math.log10(recovered / quiet)) < 1
    assert spectral_amplitude(pcm, 1.5, 2.5, 440) > 0.1
    evidence = {
        **result,
        "container_seconds": container["duration"],
        "video_seconds": video["duration"],
        "audio_seconds": audio["duration"],
        "video_frames": video["nb_frames"],
        "bgm_1khz_amplitude": {"quiet": quiet, "speech": speech, "recovered": recovered},
        "recovery_db": 20 * math.log10(recovered / quiet),
        "voice_440hz_amplitude": spectral_amplitude(pcm, 1.5, 2.5, 440),
        "pixels": pixels,
        "ducking_db": reduction,
        "peak": max(map(abs, pcm)),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    print("AUDIO_FIRST_EVIDENCE=" + json.dumps(evidence))
    # Optional retained artifact must be explicitly outside the repository.
    if os.environ.get("AUDIO_FIRST_ARTIFACT_DIR"):
        folder = Path(os.environ["AUDIO_FIRST_ARTIFACT_DIR"]).resolve()
        assert not folder.is_relative_to(REPO_ROOT)
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "audio-first-synthetic.mp4").open("xb") as target:
            target.write(output.read_bytes())


@pytest.mark.parametrize(
    "options",
    [
        {"fps": 0},
        {"width": 159},
        {"similarity": float("nan")},
        {"bgm_gain": float("inf")},
        {"key": "green;null"},
        {"duck_ratio": 0},
        {"despill": -1},
    ],
)
def test_invalid_settings_fail_before_io(tmp_path, options):
    with pytest.raises(ValueError):
        compose(*([tmp_path / "missing"] * 4), tmp_path / "out.mp4", **options)
    assert not (tmp_path / "out.mp4").exists()


def test_existing_output_and_input_preserved(media, tmp_path):
    before = [p.read_bytes() for p in media]
    output = tmp_path / "existing.mp4"
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        compose(*media, output)
    with pytest.raises(FileExistsError):
        compose(*media, media[1])
    assert output.read_bytes() == b"keep"
    assert [p.read_bytes() for p in media] == before


def test_wrong_stream_and_corrupt_input(media, tmp_path):
    output = tmp_path / "invalid.mp4"
    with pytest.raises(ValueError, match="requires an audio stream"):
        compose(media[1], *media[1:], output)
    with pytest.raises(ValueError, match="requires a video stream"):
        compose(media[0], media[0], *media[2:], output)
    corrupt = tmp_path / "corrupt.wav"
    corrupt.write_bytes(b"not audio")
    with pytest.raises(ValueError, match="Cannot probe"):
        compose(corrupt, *media[1:], output)
    assert not output.exists()


def test_failed_encode_does_not_publish(media, tmp_path, monkeypatch):
    import src.audio_first_compositor as module

    original_run = module.run

    def fail_encode(command):
        if command[0] == "ffmpeg":
            return subprocess.CompletedProcess(command, 1, "", "simulated encoder failure")
        return original_run(command)

    monkeypatch.setattr(module, "run", fail_encode)
    with pytest.raises(ValueError, match="Encoding failed"):
        compose(*media, tmp_path / "failed.mp4")
    assert not (tmp_path / "failed.mp4").exists()
    assert not list(tmp_path.glob(".audio-first-*"))


def test_cli_missing_input(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src" / "audio_first_compositor.py"),
            *([str(tmp_path / "absent")] * 4),
            str(tmp_path / "out.mp4"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ERROR: Input not found (narration)" in result.stderr
    assert result.stderr.isascii()
    assert not (tmp_path / "out.mp4").exists()


@pytest.mark.parametrize("duration", ["0", "nan", "inf", "-1", None])
def test_unknown_narration_duration_rejected(tmp_path, monkeypatch, duration):
    import src.audio_first_compositor as module

    source = tmp_path / "source.wav"
    source.write_bytes(b"preserve")
    streams = [{"codec_type": "audio"}, {"codec_type": "video"}]
    if duration is not None:
        streams[0]["duration"] = duration
    monkeypatch.setattr(module, "probe", lambda _: {"streams": streams})
    with pytest.raises(ValueError, match="duration"):
        compose(*([source] * 4), tmp_path / "out.mp4")
    assert source.read_bytes() == b"preserve"
    assert not (tmp_path / "out.mp4").exists()


def test_racing_output_is_not_overwritten(tmp_path, monkeypatch):
    import src.audio_first_compositor as module

    source = tmp_path / "source.wav"
    source.write_bytes(b"preserve")
    output = tmp_path / "out.mp4"
    monkeypatch.setattr(
        module,
        "probe",
        lambda _: {
            "streams": [{"codec_type": "audio", "duration": "1.013"}, {"codec_type": "video"}]
        },
    )

    def racing_encode(command):
        Path(command[-1]).write_bytes(b"encoded")
        output.write_bytes(b"other writer")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(module, "run", racing_encode)
    with pytest.raises(FileExistsError):
        compose(*([source] * 4), output)
    assert output.read_bytes() == b"other writer"
    assert source.read_bytes() == b"preserve"
    assert not list(tmp_path.glob(".audio-first-*"))


def test_greenscreen_with_alpha_is_rejected(media, tmp_path):
    """A transparent-background clip would come out black, not composited."""
    transparent = tmp_path / "alpha.mov"
    clip(transparent, "color=c=black@0.0", "-vf", "format=argb", codec=("-c:v", "qtrle"))
    (stream,) = probe(transparent)["streams"]
    assert stream["pix_fmt"] == "argb"
    output = tmp_path / "alpha-out.mp4"
    with pytest.raises(ValueError, match="alpha channel"):
        compose(media[0], transparent, *media[2:], output, width=160, height=128)
    assert not output.exists()
    assert not list(tmp_path.glob(".audio-first-*"))


def test_despill_changes_green_tinted_foreground(media, tmp_path):
    """0x90D060 survives the key; only despill can pull its green channel down."""
    tinted = tmp_path / "tinted.mp4"
    clip(
        tinted,
        "color=c=0x00ff00",
        "-vf",
        "drawbox=x=48:y=32:w=64:h=64:color=0x90D060:t=fill",
    )
    pixels = {}
    for name, despill in (("off", None), ("mix0", 0), ("default", 0.5), ("mix1", 1)):
        output = tmp_path / f"despill-{name}.mp4"
        compose(media[0], tinted, *media[2:], output, width=160, height=128, despill=despill)
        pixels[name] = pixel_at(output, 80, 64)
        assert all(abs(a - b) <= 20 for a, b in zip(pixel_at(output, 16, 16), (0, 0, 255)))
    print("AUDIO_FIRST_DESPILL=" + json.dumps(pixels))
    assert all(abs(a - b) <= 12 for a, b in zip(pixels["off"], (0x90, 0xD0, 0x60))), pixels
    for name in ("mix0", "default", "mix1"):
        assert pixels["off"][1] - pixels[name][1] >= 30, pixels
    # mix weighs red against blue, so it changes the result but 0 does not disable it.
    assert abs(pixels["mix0"][1] - pixels["mix1"][1]) >= 10, pixels


def test_duck_ratio_controls_reduction(media, tmp_path):
    reductions = {}
    for ratio in (2, 12):
        output = tmp_path / f"ratio-{ratio}.mp4"
        compose(*media, output, width=160, height=128, duck_ratio=ratio)
        reductions[ratio] = ducking_db(output)
    print("AUDIO_FIRST_DUCK_RATIO=" + json.dumps(reductions))
    assert reductions[2] >= 6
    assert reductions[12] - reductions[2] >= 6, reductions


def test_missing_output_directory_fails_in_plain_ascii(media, tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "src" / "audio_first_compositor.py"),
            *map(str, media),
            str(tmp_path / "no-such-dir" / "out.mp4"),
        ],
        capture_output=True,
    )
    assert result.returncode == 1
    assert result.stderr.decode("ascii").strip() == "ERROR: Output directory does not exist"
    assert not (tmp_path / "no-such-dir").exists()


def test_publish_failure_leaves_no_empty_output(tmp_path, monkeypatch):
    """Destination was created exclusively, then the staged file could not be read."""
    import src.audio_first_compositor as module

    source = tmp_path / "source.wav"
    source.write_bytes(b"preserve")
    output = tmp_path / "out.mp4"
    monkeypatch.setattr(
        module,
        "probe",
        lambda _: {
            "streams": [{"codec_type": "audio", "duration": "1.013"}, {"codec_type": "video"}]
        },
    )
    # Encoder reports success but never writes the staged file.
    monkeypatch.setattr(
        module, "run", lambda command: subprocess.CompletedProcess(command, 0, "", "")
    )
    with pytest.raises(FileNotFoundError):
        compose(*([source] * 4), output)
    assert not output.exists()
    assert source.read_bytes() == b"preserve"
    assert not list(tmp_path.glob(".audio-first-*"))
