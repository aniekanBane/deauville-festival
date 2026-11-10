import typing
from pathlib import Path

import pytest

from deauville_festival import errors
from deauville_festival.storage import SQLiteStorage


class TestSQLiteStorage:
    """Tests suite for the `SQLiteStorage` class."""

    def test_new_database_is_not_initialized(self, tmp_path: Path) -> None:
        storage = SQLiteStorage(tmp_path / "festival.db")

        assert not storage.is_initialized()
        with pytest.raises(errors.StorageError, match="not been initialized"):
            storage.load()

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, sample_festival_data: dict[str, typing.Any]
    ) -> None:
        storage = SQLiteStorage(tmp_path / "festival.db")

        storage.save(sample_festival_data)

        assert storage.is_initialized()
        assert storage.load() == sample_festival_data

    def test_save_replaces_existing_data(
        self, tmp_path: Path, sample_festival_data: dict[str, typing.Any]
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

    def test_unknown_performance_kind_in_database_raises_storage_error(
        self, tmp_path: Path
    ) -> None:
        from deauville_festival import errors

        storage = SQLiteStorage(tmp_path / "festival.db")
        fake_row = {
            "kind": "magic",
            "title": "Title",
            "venue_slug": "venue",
            "start": "2027-06-10T20:00",
            "duration_minutes": 60,
            "description": "",
        }
        with pytest.raises(
            errors.StorageError, match="Unknown performance kind: 'magic'"
        ):
            storage._parse_performance(fake_row, None)  # type: ignore[arg-type]

    def test_missing_required_column_raises_storage_error(self, tmp_path: Path) -> None:
        from deauville_festival import errors

        storage = SQLiteStorage(tmp_path / "festival.db")
        fake_row = {"kind": "solo", "artist_slug": None}
        with pytest.raises(errors.StorageError, match="missing required column"):
            storage._required_column(fake_row, "artist_slug")  # type: ignore[arg-type]

    def test_unknown_performance_subclass_save_raises_storage_error(
        self, tmp_path: Path, sample_festival_data: dict[str, typing.Any]
    ) -> None:
        from dataclasses import dataclass

        from deauville_festival import errors
        from deauville_festival.models import Performance

        @dataclass
        class CustomPerformance(Performance):
            @property
            @typing.override
            def kind(self):
                return "custom"

            @typing.override
            def get_all_artists(self):
                return ()

            @typing.override
            def involves_artist(self, slug):
                return None

        custom = CustomPerformance(
            title="Custom Show",
            venue="le-kiosque",
            start=sample_festival_data["performances"][0].start,
            duration_minutes=60,
        )
        invalid_data = {**sample_festival_data, "performances": [custom]}

        db_path = tmp_path / "festival.db"
        storage = SQLiteStorage(db_path)
        with pytest.raises(
            errors.StorageError, match="Unknown performance kind: CustomPerformance"
        ):
            storage.save(invalid_data)
