import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from deauville_festival import errors
from deauville_festival.models import (
    Artist,
    LineupPerformance,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)
from deauville_festival.storage import FestivalDataJSONEncoder, load_data, save_data


@pytest.fixture
def sample_festival_data() -> dict[str, Any]:
    """Returns a valid sample festival data dictionary with model instances."""
    return {
        "name": "Deauville Festival du Rire",
        "first_day": date(2027, 6, 10),
        "last_day": date(2027, 6, 13),
        "venues": [
            Venue(
                name="Théâtre des Planches",
                capacity=420,
                address="Place du Casino, Deauville",
            ),
            Venue(
                name="Le Kiosque",
                capacity=120,
                address="Promenade des Planches",
            ),
        ],
        "artists": [
            Artist(
                name="Élodie Marchal",
                bio="Stand-up comedian.",
                photo_url="https://example.com/elodie.jpg",
            ),
            Artist(
                name="Hugo Vernier",
                bio="Improviser.",
                photo_url="https://example.com/hugo.jpg",
            ),
            Artist(
                name="Camille Roux",
                bio="Satirist.",
                photo_url="https://example.com/camille.jpg",
            ),
        ],
        "performances": [
            SoloPerformance(
                title="Opening Night",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 10, 20, 0),
                duration_minutes=60,
                description="Opening solo show.",
                artist="elodie-marchal",
                min_age=12,
            ),
            LineupPerformance(
                title="Gala du Rire",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 11, 21, 0),
                duration_minutes=90,
                description="Lineup gala.",
                host="elodie-marchal",
                acts=["hugo-vernier", "camille-roux"],
            ),
            WorkshopPerformance(
                title="Improv Workshop",
                venue="le-kiosque",
                start=datetime(2027, 6, 12, 14, 0),
                duration_minutes=120,
                description="Learn improv.",
                teacher="hugo-vernier",
                max_participants=15,
                participants=["Alice", "Bob"],
            ),
        ],
    }


class TestLoadData:
    """Tests for `storage.load_data`."""

    def test_load_valid_festival_json(self, tmp_path: Path) -> None:
        file_path = tmp_path / "festival.json"
        raw_data = {
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
                    "photo_url": "https://example.com/elodie.jpg",
                },
                {
                    "name": "Hugo Vernier",
                    "bio": "Improviser.",
                    "photo_url": "https://example.com/hugo.jpg",
                },
                {
                    "name": "Camille Roux",
                    "bio": "Satirist.",
                    "photo_url": "https://example.com/camille.jpg",
                },
            ],
            "performances": [
                {
                    "kind": "solo",
                    "title": "After Hours",
                    "venue": "le-kiosque",
                    "start": "2027-06-10T21:00",
                    "duration_minutes": 60,
                    "description": "Solo show",
                    "artist": "elodie-marchal",
                    "min_age": 16,
                },
                {
                    "kind": "lineup",
                    "title": "Comedy Club",
                    "venue": "le-kiosque",
                    "start": "2027-06-11T21:00",
                    "duration_minutes": 90,
                    "description": "Lineup show",
                    "host": "elodie-marchal",
                    "acts": ["hugo-vernier", "camille-roux"],
                },
                {
                    "kind": "workshop",
                    "title": "Stand-up 101",
                    "venue": "le-kiosque",
                    "start": "2027-06-12T14:00",
                    "duration_minutes": 120,
                    "description": "Workshop",
                    "teacher": "hugo-vernier",
                    "max_participants": 10,
                    "participants": ["Camille R."],
                },
            ],
        }
        file_path.write_text(json.dumps(raw_data), encoding="utf-8")

        loaded = load_data(file_path)

        assert loaded["name"] == "Deauville Festival du Rire"
        assert loaded["first_day"] == date(2027, 6, 10)
        assert loaded["last_day"] == date(2027, 6, 13)
        assert len(loaded["venues"]) == 1
        assert isinstance(loaded["venues"][0], Venue)
        assert loaded["venues"][0].slug == "le-kiosque"

        assert len(loaded["artists"]) == 3
        assert all(isinstance(a, Artist) for a in loaded["artists"])

        performances = loaded["performances"]
        assert len(performances) == 3
        assert isinstance(performances[0], SoloPerformance)
        assert performances[0].start == datetime(2027, 6, 10, 21, 0)
        assert performances[0].min_age == 16
        assert isinstance(performances[1], LineupPerformance)
        assert performances[1].acts == ["hugo-vernier", "camille-roux"]
        assert isinstance(performances[2], WorkshopPerformance)
        assert performances[2].participants == ["Camille R."]

    def test_load_missing_file_prints_message_and_raises_file_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_data(missing_path)

        captured = capsys.readouterr()
        assert f"File not found: {missing_path}." in captured.out

    def test_load_invalid_json_raises_value_error_with_line_number(
        self, tmp_path: Path
    ) -> None:
        invalid_json_path = tmp_path / "broken.json"
        invalid_json_path.write_text(
            '{\n  "name": "Festival",\n  broken\n}', encoding="utf-8"
        )

        with pytest.raises(ValueError) as exc_info:
            load_data(invalid_json_path)

        assert str(exc_info.value) == (
            f"Invalid JSON in file: {invalid_json_path} (line 3)."
        )

    def test_load_unknown_performance_kind_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "unknown_kind.json"
        raw_data = {
            "performances": [
                {
                    "kind": "concert",
                    "title": "Mystery Show",
                    "venue": "le-kiosque",
                    "start": "2027-06-10T20:00",
                    "duration_minutes": 60,
                }
            ]
        }
        file_path.write_text(json.dumps(raw_data), encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            load_data(file_path)

        assert str(exc_info.value) == "Unknown performance kind: 'concert'."

    def test_load_invalid_model_data_propagates_invalid_error(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "invalid_venue.json"
        raw_data = {
            "venues": [
                {
                    "name": "Le Kiosque",
                    "capacity": -10,
                    "address": "Promenade des Planches",
                }
            ]
        }
        file_path.write_text(json.dumps(raw_data), encoding="utf-8")

        with pytest.raises(errors.InvalidError):
            load_data(file_path)


class TestFestivalDataJSONEncoder:
    """Tests for `storage.FestivalDataJSONEncoder`."""

    def test_encodes_dataclass_date_and_datetime(self) -> None:
        venue = Venue(name="Le Kiosque", capacity=120, address="Deauville")
        payload = {
            "day": date(2027, 6, 10),
            "moment": datetime(2027, 6, 10, 21, 30, 45),
            "venue": venue,
        }

        encoded = json.loads(json.dumps(payload, cls=FestivalDataJSONEncoder))

        assert encoded == {
            "day": "2027-06-10",
            "moment": "2027-06-10T21:30",
            "venue": {
                "name": "Le Kiosque",
                "capacity": 120,
                "address": "Deauville",
            },
        }

    def test_unsupported_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            json.dumps({"unsupported": {1, 2, 3}}, cls=FestivalDataJSONEncoder)

    def test_dataclass_type_object_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            json.dumps({"cls": Venue}, cls=FestivalDataJSONEncoder)


class TestSaveData:
    """Tests for `storage.save_data` and round-trip persistence."""

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, sample_festival_data: dict[str, Any]
    ) -> None:
        nested_dir = tmp_path / "subdir"
        file_path = nested_dir / "festival.json"

        save_data(sample_festival_data, file_path)

        assert file_path.exists()
        raw_text = file_path.read_text(encoding="utf-8")
        # Verify UTF-8 characters are preserved unescaped (ensure_ascii=False)
        assert "Théâtre des Planches" in raw_text
        assert "Élodie Marchal" in raw_text

        reloaded = load_data(file_path)

        assert reloaded["name"] == sample_festival_data["name"]
        assert reloaded["first_day"] == sample_festival_data["first_day"]
        assert reloaded["last_day"] == sample_festival_data["last_day"]
        assert reloaded["venues"] == sample_festival_data["venues"]
        assert reloaded["artists"] == sample_festival_data["artists"]
        assert reloaded["performances"] == sample_festival_data["performances"]
