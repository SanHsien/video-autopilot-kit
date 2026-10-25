from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from silent_vlog_maker.constants import SAFE_ZONE  # noqa: E402
from silent_vlog_maker.text_overlay import POSITION_PRESETS  # noqa: E402


def test_fixed_y_portrait_presets_stay_above_the_bottom_safe_line() -> None:
    for name, preset in POSITION_PRESETS.items():
        if not str(preset["y"]).isdigit():
            continue
        bottom = (int(preset["y"]) + preset["fs"] * 1.2
                  + preset.get("box_pad", 0) + preset.get("border_w", 0))
        assert bottom <= SAFE_ZONE["bottom"], (name, round(bottom))
