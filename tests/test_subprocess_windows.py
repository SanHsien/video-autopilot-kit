from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

import av_util  # noqa: E402


def test_av_util_decodes_utf8_child_output_on_cp950_windows() -> None:
    expected = "中文路徑：測試.mp4"
    result = av_util.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.stdout.buffer.write({expected!r}.encode('utf-8'))",
        ]
    )

    assert result.returncode == 0
    assert result.stdout == expected


def test_captured_text_subprocesses_declare_utf8_error_handling() -> None:
    missing = []
    paths = sorted(
        list((ROOT / "src").rglob("*.py"))
        + list((ROOT / "examples").rglob("*.py"))
        + list((ROOT / "tools").rglob("*.py"))
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if (
                node.func.attr != "run"
                or not isinstance(owner, ast.Name)
                or owner.id != "subprocess"
            ):
                continue
            keywords = {item.arg for item in node.keywords if item.arg}
            if "capture_output" not in keywords or not ({"text", "encoding"} & keywords):
                continue
            if not {"encoding", "errors"}.issubset(keywords):
                missing.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert not missing, (
        "captured subprocess text lacks explicit UTF-8 decoding: " + ", ".join(missing)
    )
