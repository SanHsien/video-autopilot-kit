"""
silent_vlog_maker.effects — R17 cinematic + R20 KenBurns + xfade transitions.

ffmpeg filter chain builders for visual polish.
"""
from .constants import CINEMATIC_CURVES


# ─────────────────────────────────────────────────────────────────────
# R20: KenBurns animation for still photos (M14 — 2026-05-18 v10 學到)
# ─────────────────────────────────────────────────────────────────────
# 照片不能死板。要 zoom-in / pan / zoom-out 動畫。用 ffmpeg zoompan filter

def kenburns_zoom_in(duration_sec: float, fps: int = 30, target_scale: str = "1080:1920",
                    zoom_max: float = 1.15) -> str:
    """Slow zoom-in over duration. Returns filter string for portrait/landscape.

    Usage in filter_complex:
        [N:v]format=yuv420p,{kenburns_zoom_in(5.0)},setpts=PTS-STARTPTS[vN]
    """
    frames = int(duration_sec * fps)
    # 前置 scale/crop 跟著 target_scale 走 — 之前寫死 1920:1080，直式 1080:1920
    # 會被 zoompan 拉成變形（2026-06-10 audit）
    tw, th = target_scale.split(":")
    # zoompan 的 s 必須寫 WxH（冒號會被當成選項分隔→ffmpeg 直接拒絕）；
    # zoom 以畫面中心為錨、平均分攤到每一幀，不再提早頂到上限停住
    return (
        f"scale={tw}:{th}:force_original_aspect_ratio=increase,"
        f"crop={tw}:{th},"
        f"zoompan=z='1+({zoom_max}-1)*on/{max(1, frames - 1)}':"
        f"x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={tw}x{th}:fps={fps}"
    )


def kenburns_pan_right(duration_sec: float, fps: int = 30, target_scale: str = "1920:1080") -> str:
    """Pan-right + slight zoom over duration."""
    frames = int(duration_sec * fps)
    # x 在 zoompan 合法範圍 [0, iw-iw/zoom] 內由左掃到右 — 舊式子起點超界被 clamp
    # 且隨時間遞減（實際是向左/不動），從未真正 pan right（2026-06-10 audit）
    tw, th = (int(value) for value in target_scale.split(":"))
    span = max(1, frames - 1)
    # 前置畫布跟著 target 比例留 1.25x 餘裕（舊的寫死 2400:1350 會把直式壓扁）
    return (
        f"scale={tw * 5 // 4}:{th * 5 // 4}:force_original_aspect_ratio=increase,"
        f"crop={tw * 5 // 4}:{th * 5 // 4},"
        f"zoompan=z='1+0.1*on/{span}':"
        f"x='(iw-iw/zoom)*on/{span}':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={tw}x{th}:fps={fps}"
    )


def kenburns_static(duration_sec: float, target_scale: str = "1920:1080") -> str:
    """No animation — for fast-cut photo montage."""
    return (
        f"scale={target_scale}:force_original_aspect_ratio=decrease,"
        f"pad={target_scale}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )


# ─────────────────────────────────────────────────────────────────────
# R17 helper: Cinematic curves application
# ─────────────────────────────────────────────────────────────────────

def apply_cinematic_grade(enabled: bool = True) -> str:
    """Return cinematic curves filter chain (or empty if disabled).

    Apply AFTER tonemap (R10) to add subtle film-look to SDR output:
    - Lift shadows (warmer)
    - Roll-off highlights
    - Slight teal-orange shift (cinematic standard)
    - Subtle desat + contrast lift

    Compose into per-clip filter:
        chain = f"[i:v]trim={start}:{end},setpts=PTS-STARTPTS,{TONEMAP_FILTER}"
        if cinematic:
            chain += f",{apply_cinematic_grade()}"
        chain += f",drawtext=..."
    """
    return CINEMATIC_CURVES if enabled else ""


# ─────────────────────────────────────────────────────────────────────
# R17 helper: xfade crossfade between clips
# ─────────────────────────────────────────────────────────────────────

def build_xfade_concat(num_clips: int, clip_durations: list[float],
                       xfade_duration: float = 0.4,
                       transition: str = "fade") -> str:
    """Build xfade-based concat (smoother than hard cut concat).

    Args:
        num_clips: number of [vN] streams (indexed v0..v{N-1})
        clip_durations: per-clip durations in order
        xfade_duration: crossfade length (typical 0.3-0.5s)
        transition: xfade type — fade / dissolve / fadeblack / slideup / circleopen

    Returns:
        Filter chain string. Use as alternative to standard concat.

    Note: xfade requires same fps/timebase. Use after tonemap/grade.
    Output is N-1 chained xfades.
    """
    # First fade: v0 + v1 → vx1 at offset (dur0 - xfade)
    # Then vx1 + v2 → vx2 at offset (dur0 + dur1 - 2*xfade)
    # etc.

    parts = []
    cumulative = 0.0
    prev_label = "v0"

    for i in range(1, num_clips):
        offset = cumulative + clip_durations[i - 1] - xfade_duration
        cumulative = offset  # next offset baseline

        next_label = f"vx{i}" if i < num_clips - 1 else "outv"
        parts.append(
            f"[{prev_label}][v{i}]xfade=transition={transition}:"
            f"duration={xfade_duration}:offset={offset}[{next_label}]"
        )
        prev_label = next_label

    return ";".join(parts)
