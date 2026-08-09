"""Path 1 桌面介面的可測核心。

GUI 只負責收集欄位、背景執行與顯示結果；本模組負責驗證路徑、接回既有
Programmatic pipeline，以及在 PyInstaller 模式下啟用隨附的 ffmpeg/ffprobe。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
for _path in (SRC, SRC / "longform_maker", SRC / "capcut_helpers"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

APP_VERSION = "0.13.0"
SUPPORTED_BANDS = {"wide", "top", "mid", "bottom"}


@dataclass(frozen=True)
class OperationResult:
    """單次 GUI 工作的標準結果。"""

    ok: bool
    message: str
    output_dir: Path | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


def configure_bundled_tools(bundle_root: Path | None = None) -> Path | None:
    """若是封裝版，將隨附的 ffmpeg/ffprobe 目錄置於 PATH 最前面。"""

    if bundle_root is None:
        frozen_root = getattr(sys, "_MEIPASS", None)
        if not frozen_root:
            return None
        bundle_root = Path(frozen_root)
    bin_dir = Path(bundle_root) / "bin"
    suffix = ".exe" if os.name == "nt" else ""
    required = [bin_dir / f"ffmpeg{suffix}", bin_dir / f"ffprobe{suffix}"]
    if not all(path.is_file() for path in required):
        return None
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    if str(bin_dir) not in parts:
        os.environ["PATH"] = os.pathsep.join([str(bin_dir), *parts])
    return bin_dir


def default_settings_path() -> Path:
    """回傳不在 repo 內的 Windows-first GUI 設定路徑。"""

    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "video-autopilot-kit" / "path1-gui.json"
    return Path.home() / ".video-autopilot-kit" / "path1-gui.json"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    target = Path(path) if path else default_settings_path()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(values: Mapping[str, Any], path: Path | None = None) -> Path:
    target = Path(path) if path else default_settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(values), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, target)
    return target


def _existing_path(value: object, label: str, *, directory: bool = False) -> Path:
    raw = str(value or "").strip().strip('"')
    if not raw:
        raise ValueError(f"請選擇{label}")
    path = Path(raw).expanduser().resolve()
    valid = path.is_dir() if directory else path.is_file()
    if not valid:
        kind = "資料夾" if directory else "檔案"
        raise ValueError(f"{label}{kind}不存在：{path}")
    return path


def validate_short_project(project_dir: object, action: str) -> Path:
    if action not in {"scan", "build"}:
        raise ValueError(f"未知 Shorts 工作：{action}")
    project = _existing_path(project_dir, "Shorts 專案", directory=True)
    if action == "build" and not (project / "_plan.py").is_file():
        raise ValueError("專案內沒有 _plan.py；請先執行素材掃描，再填完企劃")
    return project


def run_short_job(
    action: str,
    project_dir: object,
    bgm_dir: object = None,
    *,
    module: object = None,
) -> OperationResult:
    project = validate_short_project(project_dir, action)
    if module is None:
        import shorts_autopilot as module  # type: ignore[no-redef]

    if action == "scan":
        details = module.scan(project.name, inbox=str(project.parent))
        return OperationResult(
            True,
            "素材掃描完成；請開啟 _plan.py 填寫畫面事實與字幕後再建置。",
            project / "_work",
            details,
        )

    bgm = _existing_path(bgm_dir, "BGM 素材庫", directory=True)
    details = module.build(
        project.name,
        inbox=str(project.parent),
        bgm_root=str(bgm),
    )
    ok = bool(details.get("all_green", False))
    message = "Shorts 建置與自動 QA 完成。" if ok else "成片已產生，但自動 QA 未全綠。"
    return OperationResult(ok, message, project / "_out", details)


def parse_teardown_options(
    target: object,
    band: object,
    threshold: object,
) -> tuple[Path, str, float]:
    raw = str(target or "").strip().strip('"')
    if not raw:
        raise ValueError("請選擇競品影片或資料夾")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"競品目標不存在：{path}")
    parsed_band = str(band or "wide").strip().lower()
    if parsed_band not in SUPPORTED_BANDS:
        raise ValueError("字幕區域只接受 wide、top、mid、bottom")
    try:
        parsed_threshold = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError("場景切換門檻必須是數字") from exc
    if not 0 < parsed_threshold < 1:
        raise ValueError("場景切換門檻必須介於 0 到 1")
    return path, parsed_band, parsed_threshold


def run_teardown_job(
    target: object,
    band: str,
    threshold: float,
    *,
    module: object = None,
) -> OperationResult:
    path = Path(target).resolve()
    videos = [path] if path.is_file() else sorted(
        candidate for candidate in path.rglob("*") if candidate.suffix.lower() == ".mp4"
    )
    if not videos:
        raise ValueError(f"找不到 MP4：{path}")
    if module is None:
        import teardown as module  # type: ignore[no-redef]
    for video in videos:
        module.teardown(str(video), band, threshold)
        print()
    return OperationResult(
        True,
        f"競品量測完成，共處理 {len(videos)} 支影片。",
        path.parent if path.is_file() else path,
        {"videos": len(videos)},
    )


def parse_screen_clean_options(
    source: object,
    output: object,
    crop: object,
    head_trim: object,
    tail_trim: object,
) -> tuple[Path, Path, str, float, float]:
    source_path = _existing_path(source, "螢幕錄影")
    output_raw = str(output or "").strip().strip('"')
    if not output_raw:
        raise ValueError("請指定清理後輸出檔")
    output_path = Path(output_raw).expanduser().resolve()
    if output_path.suffix.lower() != ".mp4":
        raise ValueError("清理後輸出必須是 .mp4")
    pieces = str(crop or "").strip().split(":")
    if len(pieces) != 4 or any(not piece.isdigit() for piece in pieces):
        raise ValueError("裁切範圍必須是 W:H:X:Y 四個非負整數")
    width, height, _x, _y = (int(piece) for piece in pieces)
    if width <= 0 or height <= 0:
        raise ValueError("裁切範圍 W:H:X:Y 的寬高必須大於 0")
    try:
        head = float(head_trim)
        tail = float(tail_trim)
    except (TypeError, ValueError) as exc:
        raise ValueError("頭尾裁切秒數必須是數字") from exc
    if head < 1 or tail < 1:
        raise ValueError("為避免錄影 UI 外洩，頭尾都必須至少 1 秒")
    return source_path, output_path, str(crop), head, tail


def run_screen_clean_job(
    source: Path,
    output: Path,
    crop: str,
    head_trim: float,
    tail_trim: float,
    *,
    module: object = None,
) -> OperationResult:
    if module is None:
        from longform_maker import screen_clean as module  # type: ignore[no-redef]
    output.parent.mkdir(parents=True, exist_ok=True)
    module.clean_screen_recording(
        str(source),
        str(output),
        crop,
        head_trim=head_trim,
        tail_trim=tail_trim,
    )
    return OperationResult(True, "螢幕錄影清理完成。", output.parent, {"output": str(output)})


def run_delivery_qa_job(
    video: object,
    *,
    check_audio: bool,
    module: object = None,
) -> OperationResult:
    path = _existing_path(video, "交付影片")
    evidence = path.parent / f"{path.stem}_path1_qa"
    evidence.mkdir(parents=True, exist_ok=True)
    if module is None:
        from capcut_helpers import delivery_qa as module  # type: ignore[no-redef]
    report = module.final_delivery_qa(
        str(path),
        audio=bool(check_audio),
        contact_out=str(evidence / "contact_sheet.jpg"),
        sheets_dir=str(evidence / "fullframe"),
    )
    ok = bool(report.get("deliver_ok", False))
    message = "交付 QA 機械項全綠；仍需逐張檢查全幀圖。" if ok else "交付 QA 已阻擋，請依日誌修正。"
    return OperationResult(ok, message, evidence, report)


def dependency_status() -> dict[str, dict[str, Any]]:
    """取得 GUI 首頁可顯示的最小依賴狀態，不執行昂貴健康測試。"""

    status: dict[str, dict[str, Any]] = {}
    for command in ("ffmpeg", "ffprobe"):
        path = shutil.which(command)
        version = ""
        if path:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                )
                version = (result.stdout or result.stderr).splitlines()[0]
            except (OSError, subprocess.SubprocessError, IndexError):
                version = "版本讀取失敗"
        status[command] = {"ok": bool(path), "path": path or "", "version": version}
    for key, import_name in (("numpy", "numpy"), ("Pillow", "PIL")):
        try:
            package = __import__(import_name)
            version = getattr(package, "__version__", "已安裝")
            status[key] = {"ok": True, "path": "內嵌 Python 套件", "version": version}
        except ImportError:
            status[key] = {"ok": False, "path": "", "version": "未安裝"}
    return status


configure_bundled_tools()
