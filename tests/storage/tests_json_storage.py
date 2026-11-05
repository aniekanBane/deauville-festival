import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from deauville_festival import errors
from deauville_festival.models import Venue
from deauville_festival.storage import (
    FestivalDataJSONEncoder,
    JSONFileStorage,
    load_data,
    save_data,
)


class TestJSONFileStorage:
    """ "Tests suite for the `JSONFileStorage` class."""

    def test_load_valid_festival_json(self, tmp_path: Path) -> None:
        file_path = tmp_path / "festival.json"
        file_path.write_text(
            json.dumps(
                {
                    "name": "Deauville Festival du Rire",
                    "first_day": "2027-06-10",
                    "last_day": "2027-06-13",
                    "venues": [
                        {
                            "name": "Le Kiosque",
                            "capacity": 120,
                            "address": "Promenade des Planches",
                        }
                    ],
                    "artists": [
                        {
                            "name": "Élodie Marchal",
                            "bio": "Stand-up comedian.",
                            "photo_url": "",
                        }
                    ],
                    "performances": [],
                }
            ),
            encoding="utf-8",
        )

        loaded = JSONFileStorage(file_path).load()

        assert loaded["name"] == "Deauville Festival du Rire"
        assert loaded["first_day"] == date(2027, 6, 10)
        assert loaded["last_day"] == date(2027, 6, 13)
        assert loaded["venues"][0].slug == "le-kiosque"
        assert loaded["artists"][0].slug == "elodie-marchal"

    def test_load_missing_file_raises_storage_error(self, tmp_path: Path) -> None:
        missing_path = tmp_path / "missing.json"

        with pytest.raises(
            errors.StorageError, match=f"File not found: {missing_path}."
        ):
            load_data(missing_path)

    def test_load_invalid_json_reports_line_number(self, tmp_path: Path) -> None:
        file_path = tmp_path / "broken.json"
        file_path.write_text('{\n  "name": "Festival",\n  broken\n}', encoding="utf-8")

        with pytest.raises(errors.StorageError, match=r"line 3"):
            load_data(file_path)

    def test_load_unknown_performance_kind_raises(self, tmp_path: Path) -> None:
        file_path = tmp_path / "unknown.json"
        file_path.write_text(
            json.dumps(
                {"performances": [{"kind": "concert", "start": "2027-06-10T20:00"}]}
            ),
            encoding="utf-8",
        )

        with pytest.raises(errors.StorageError, match="Unknown performance kind"):
            load_data(file_path)

    def test_load_invalid_model_data_propagates_error(self, tmp_path: Path) -> None:
        file_path = tmp_path / "invalid.json"
        file_path.write_text(
            json.dumps(
                {
                    "venues": [
                        {
                            "name": "Le Kiosque",
                            "capacity": -1,
                            "address": "Deauville",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(errors.InvalidError):
            load_data(file_path)

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, sample_festival_data: dict[str, Any]
    ) -> None:
        file_path = tmp_path / "nested" / "festival.json"

        save_data(sample_festival_data, file_path)

        assert "Théâtre des Planches" in file_path.read_text(encoding="utf-8")
        assert load_data(file_path) == sample_festival_data


class TestFestivalDataJSONEncoder:
    """Tests suite for the `FestivalDataJSONEncoder` class."""

    def test_encodes_supported_values(self) -> None:
        payload = {
            "day": date(2027, 6, 10),
            "moment": datetime(2027, 6, 10, 21, 30, 45),
            "venue": Venue(name="Le Kiosque", capacity=120, address="Deauville"),
        }

        assert json.loads(json.dumps(payload, cls=FestivalDataJSONEncoder)) == {
            "day": "2027-06-10",
            "moment": "2027-06-10T21:30",
            "venue": {
                "name": "Le Kiosque",
                "capacity": 120,
                "address": "Deauville",
            },
        }

    def test_rejects_unsupported_values(self) -> None:
        with pytest.raises(TypeError):
            json.dumps({"unsupported": {1, 2, 3}}, cls=FestivalDataJSONEncoder)
