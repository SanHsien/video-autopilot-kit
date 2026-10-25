from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "longform_maker"))

import script_gate  # noqa: E402


@pytest.fixture(autouse=True)
def _restore_vocab():
    yield
    script_gate.reset_vocab()


def test_vocab_loads_from_a_pathlib_path(tmp_path: Path) -> None:
    path = tmp_path / "vocab.json"
    path.write_text(json.dumps({"hard_ban": ["禁詞"], "_note": "ignored"}), encoding="utf-8")

    counts = script_gate.load_vocab(path)

    assert counts["hard_ban"] == 1
    assert script_gate.HARD_BAN == ["禁詞"]


@pytest.mark.parametrize(
    "vocab",
    [
        {"hard_ban": "regex"},
        {"spoken_ok": "ok"},
        {"substitute": ["a", "b"]},
        {"need_pair": ["api"]},
    ],
)
def test_wrongly_typed_vocab_layers_are_rejected(vocab: dict) -> None:
    with pytest.raises(ValueError, match="load_vocab"):
        script_gate.load_vocab(vocab)


def test_non_dict_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="load_vocab"):
        script_gate.load_vocab(["hard_ban"])


def test_single_string_need_pair_is_one_partner() -> None:
    script_gate.load_vocab({"need_pair": {"API": "介面"}})

    assert script_gate.NEED_PAIR == {"api": ["介面"]}
