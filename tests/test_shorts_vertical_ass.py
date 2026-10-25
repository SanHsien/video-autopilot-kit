from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from silent_vlog_maker.shorts_vertical import build_multicolor_ass  # noqa: E402


def _dialogue(tmp_path: Path, segs: list) -> str:
    path = tmp_path / "caps.ass"
    build_multicolor_ass([(0.0, 2.0, segs, "main")], str(path))
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("Dialogue:")][0]


def test_adjacent_latin_blocks_keep_a_word_gap(tmp_path: Path) -> None:
    line = _dialogue(tmp_path, [("video-autopilot-kit", "g"), ("demo", "y")])

    assert "kit {\\c&H0AD6FF&}demo" in line


def test_cjk_blocks_are_not_spaced(tmp_path: Path) -> None:
    line = _dialogue(tmp_path, [("前段", "w"), ("重點", "r"), ("3", "y"), ("號", "w")])

    assert "前段{\\c&H303BFF&}重點{\\c&H0AD6FF&}3{\\c&H00FFFFFF&}號" in line
