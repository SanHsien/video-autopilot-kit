from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capcut_helpers import draft_io  # noqa: E402


def _draft_replicas(project: Path) -> list[Path]:
    timeline = project / "Timelines" / "timeline-1"
    timeline.mkdir(parents=True)
    files = [
        project / "draft_content.json",
        project / "draft_info.json",
        project / "draft_content.json.bak",
        project / "draft_info.json.bak",
        project / "template-2.tmp",
        timeline / "draft_content.json",
        timeline / "draft_content.json.bak",
        timeline / "template-2.tmp",
    ]
    for path in files:
        path.write_text('{"old":true}', encoding="utf-8")
    return files


def test_utf8_bom_drafts_are_editable_and_loadable(
    tmp_path: Path, monkeypatch,
) -> None:
    project = tmp_path / "bom-project"
    project.mkdir()
    draft_file = project / "draft_content.json"
    payload = {"id": "windows-bom", "tracks": []}
    draft_file.write_bytes(json.dumps(payload).encode("utf-8-sig"))
    monkeypatch.setattr(draft_io, "draft_path", lambda _name: project)

    detected = draft_io.detect_draft_format(draft_file)

    assert detected["editable"] is True
    assert detected["encrypted"] is False
    assert draft_io.load_draft("bom-project") == payload


def test_save_and_verify_cover_every_existing_capcut_replica(
    tmp_path: Path, monkeypatch,
) -> None:
    project = tmp_path / "sync-project"
    project.mkdir()
    replicas = _draft_replicas(project)
    monkeypatch.setattr(draft_io, "draft_path", lambda _name: project)
    monkeypatch.setattr(
        draft_io,
        "discover_all_draft_jsons",
        lambda _name: replicas,
    )

    draft_io.save_draft_with_sync("sync-project", {"version": 2}, backup=False)
    expected = b'{"version":2}'

    assert all(path.read_bytes() == expected for path in replicas)
    result = draft_io.verify_sync("sync-project")
    assert result["all_synced"] is True
    assert result["files_checked"] == len(replicas)


def test_rapid_saves_keep_distinct_backups(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "backup-project"
    project.mkdir()
    root = project / "draft_content.json"
    root.write_text('{"version":1}', encoding="utf-8")
    monkeypatch.setattr(draft_io, "draft_path", lambda _name: project)
    monkeypatch.setattr(time, "strftime", lambda _format: "20260809_120000")

    draft_io.save_draft_with_sync("backup-project", {"version": 2})
    draft_io.save_draft_with_sync("backup-project", {"version": 3})

    backups = sorted((tmp_path / "_backup_backup-project").glob("*.json"))
    assert len(backups) == 2
    assert {path.read_text(encoding="utf-8") for path in backups} == {
        '{"version":1}',
        '{"version":2}',
    }
