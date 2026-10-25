from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "longform_maker"))

import fx_lib  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _shape():
    shape = Image.new("RGBA", (420, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape)
    draw.ellipse([150, 50, 270, 170], fill=(255, 210, 63, 255), outline=(40, 26, 5, 255), width=6)
    return shape


@pytest.mark.parametrize("background", [150, 235])
def test_bloom_never_darkens_the_background(background: int) -> None:
    shape = _shape()
    outside = np.asarray(shape.getchannel("A")) == 0
    glow_luma = float(np.array(fx_lib._glow_colour(shape), dtype=np.float32) @ LUMA)
    plate = Image.new("RGBA", shape.size, (background,) * 3 + (255,))

    plate.alpha_composite(fx_lib.double_bloom(shape, boost=0.5))

    lum = np.asarray(plate.convert("RGB"), dtype=np.float32) @ LUMA
    assert lum[outside].min() >= min(background, glow_luma) - 1.0
    if background == 150:
        assert lum[outside].max() > background + 5


def test_glow_colour_follows_the_bright_fill() -> None:
    assert float(np.array(fx_lib._glow_colour(_shape()), dtype=np.float32) @ LUMA) > 180


def test_bloom_of_an_empty_layer_stays_transparent() -> None:
    empty = Image.new("RGBA", (32, 32), (0, 0, 0, 0))

    assert fx_lib.double_bloom(empty).getbbox() is None
