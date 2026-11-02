from pathlib import Path
from typing import Any

import pytest

from deauville_festival.storage import SQLiteStorage


class TestSQLiteStorage:
    def test_new_database_is_not_initialized(self, tmp_path: Path) -> None:
        storage = SQLiteStorage(tmp_path / "festival.db")

        assert not storage.is_initialized()
        with pytest.raises(ValueError, match="not been initialized"):
            storage.load()

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, sample_festival_data: dict[str, Any]
    ) -> None:
        storage = SQLiteStorage(tmp_path / "festival.db")

        storage.save(sample_festival_data)

        assert storage.is_initialized()
        assert storage.load() == sample_festival_data

    def test_save_replaces_existing_data(
        self, tmp_path: Path, sample_festival_data: dict[str, Any]
    ) -> None:
        storage = SQLiteStorage(tmp_path / "festival.db")
        storage.save(sample_festival_data)
        replacement = {**sample_festival_data, "name": "Replacement Festival"}

        storage.save(replacement)

        assert storage.load()["name"] == "Replacement Festival"
        assert len(storage.load()["performances"]) == 3

    def test_initialization_is_idempotent(self, tmp_path: Path) -> None:
        path = tmp_path / "festival.db"

        SQLiteStorage(path)
        SQLiteStorage(path)

        assert path.exists()