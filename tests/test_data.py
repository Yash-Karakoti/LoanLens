"""Verify integrity without ever changing the real raw directory."""

import json
from pathlib import Path

import pytest

import src.common as common
from src.common import ROOT, file_hash, load_data


def test_recorded_raw_shape_and_hash() -> None:
    """Real observations must match the recorded download checksum."""
    if not (ROOT / "data/raw/train.csv").exists():
        pytest.skip("Authentic dataset unavailable")
    source = json.loads((ROOT / "data/raw/source.json").read_text(encoding="utf-8"))
    assert file_hash(ROOT / "data/raw/train.csv") == source["sha256"]
    assert load_data().shape == (614, 13)


def test_tampered_copy_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only a temporary copy is altered to exercise the integrity failure."""
    if not (ROOT / "data/raw/train.csv").exists():
        pytest.skip("Authentic dataset unavailable")
    temporary_raw = tmp_path / "data/raw"
    temporary_raw.mkdir(parents=True)
    (temporary_raw / "train.csv").write_bytes((ROOT / "data/raw/train.csv").read_bytes() + b"\n")
    (temporary_raw / "source.json").write_bytes((ROOT / "data/raw/source.json").read_bytes())
    monkeypatch.setattr(common, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="hash changed"):
        common.load_data()
