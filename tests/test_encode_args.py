from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from silent_vlog_maker.constants import ENCODE_ARGS_BY_PLATFORM  # noqa: E402


def test_every_platform_encode_tags_the_full_bt709_triplet() -> None:
    for platform, args in ENCODE_ARGS_BY_PLATFORM.items():
        tags = {args[i]: args[i + 1] for i in range(len(args) - 1) if args[i].startswith("-color")}
        assert tags == {"-color_primaries": "bt709", "-color_trc": "bt709",
                        "-colorspace": "bt709"}, platform


def test_tonemap_filter_uses_sdr_reference_white_npl_100() -> None:
    """維護者 2026-10-25 決定採用上游 PR #26：npl=100，不再整體壓暗 2.5 倍。"""
    from silent_vlog_maker.constants import TONEMAP_FILTER

    assert TONEMAP_FILTER.startswith("zscale=t=linear:npl=100,")
    assert "npl=250" not in TONEMAP_FILTER
    assert TONEMAP_FILTER.endswith("format=yuv420p")
