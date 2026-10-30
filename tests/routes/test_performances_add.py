from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival import storage


class TestAddPerformanceSuccess:
    """Tests for successful performance creation (HTTP 201) via `POST /api/performances`."""

    def test_add_solo_performance_returns_201_and_persists(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        payload = {
            "kind": "solo",
            "title": "Morning Warmup",
            "venue": "grand-casino",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "description": "Afternoon solo show.",
            "artist": "sacha-diallo",
            "min_age": 12,
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == "solo"
        assert data["title"] == "Morning Warmup"
        assert data["venue"] == "grand-casino"
        assert data["start"] == "2027-06-10T14:00"
        assert data["duration_minutes"] == 60
        assert data["artist"] == "sacha-diallo"
        assert data["min_age"] == 12

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert "grand-casino-2027-06-10-1400" in saved_ids

    def test_add_lineup_performance_returns_201_and_persists(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        payload = {
            "kind": "lineup",
            "title": "Afternoon Lineup",
            "venue": "theatre-des-planches",
            "start": "2027-06-10T15:00",
            "duration_minutes": 60,
            "host": "paul-kerbrat",
            "acts": ["nora-lebrun", "max-pellerin"],
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == "lineup"
        assert data["title"] == "Afternoon Lineup"
        assert data["venue"] == "theatre-des-planches"
        assert data["start"] == "2027-06-10T15:00"
        assert data["host"] == "paul-kerbrat"
        assert data["acts"] == ["nora-lebrun", "max-pellerin"]

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert "theatre-des-planches-2027-06-10-1500" in saved_ids

    def test_add_workshop_performance_returns_201_and_persists(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        payload = {
            "kind": "workshop",
            "title": "Comedy Writing Lab",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 90,
            "teacher": "ines-moreau",
            "max_participants": 10,
            "participants": ["Alice B."],
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == "workshop"
        assert data["title"] == "Comedy Writing Lab"
        assert data["venue"] == "la-cabane"
        assert data["start"] == "2027-06-10T14:00"
        assert data["teacher"] == "ines-moreau"
        assert data["max_participants"] == 10
        assert data["participants"] == ["Alice B."]

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert "la-cabane-2027-06-10-1400" in saved_ids

    def test_add_workshop_clamps_max_participants_to_venue_capacity(
        self, client: TestClient
    ) -> None:
        # la-cabane has capacity 40
        payload = {
            "kind": "workshop",
            "title": "Big Workshop in Small Venue",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 90,
            "teacher": "ines-moreau",
            "max_participants": 100,
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 201
        assert response.json()["max_participants"] == 40

    def test_add_late_night_performance_before_6am_after_last_day_succeeds(
        self, client: TestClient
    ) -> None:
        """A show starting at 01:00 on 2027-06-14 belongs to festival day 2027-06-13."""
        payload = {
            "kind": "solo",
            "title": "Afterparty Encore",
            "venue": "la-cabane",
            "start": "2027-06-14T01:00",
            "duration_minutes": 60,
            "artist": "hugo-lemaire",
        }

        response = client.post("/api/performances", json=payload)
        assert response.status_code == 201

    @pytest.mark.parametrize(
        "start_str",
        [
            # Opening Gala at grand-casino is 2027-06-10 20:30-22:30.
            # 19:00 + 60m = 20:00 (exact 30m buffer before 20:30)
            "2027-06-10T19:00",
            # 23:00 is exact 30m buffer after 22:30
            "2027-06-10T23:00",
        ],
    )
    def test_exact_30_minute_buffer_is_allowed(
        self, client: TestClient, start_str: str
    ) -> None:
        payload = {
            "kind": "solo",
            "title": "Buffer Boundary Show",
            "venue": "grand-casino",
            "start": start_str,
            "duration_minutes": 60,
            "artist": "ines-moreau",
        }

        response = client.post("/api/performances", json=payload)
        assert response.status_code == 201


class TestAddPerformanceNotFound:
    """Tests for non-existent venue or artist references (HTTP 404)."""

    def test_unknown_venue_returns_404(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        initial_count = len(storage.load_data(test_data_path)["performances"])
        payload = {
            "kind": "solo",
            "title": "Lost Venue Show",
            "venue": "non-existent-venue",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "artist": "sacha-diallo",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Venue 'non-existent-venue' not found."}
        assert len(storage.load_data(test_data_path)["performances"]) == initial_count

    def test_unknown_solo_artist_returns_404(self, client: TestClient) -> None:
        payload = {
            "kind": "solo",
            "title": "Unknown Solo Artist",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "artist": "ghost-artist",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Artist 'ghost-artist' not found."}

    def test_unknown_lineup_host_or_act_returns_404(self, client: TestClient) -> None:
        payload = {
            "kind": "lineup",
            "title": "Unknown Act Show",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "host": "paul-kerbrat",
            "acts": ["nora-lebrun", "missing-act"],
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Artist 'missing-act' not found."}

    def test_unknown_workshop_teacher_returns_404(self, client: TestClient) -> None:
        payload = {
            "kind": "workshop",
            "title": "Unknown Teacher Workshop",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "teacher": "missing-teacher",
            "max_participants": 10,
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Artist 'missing-teacher' not found."}


class TestAddPerformanceConflict:
    """Tests for scheduling conflicts and festival rules (HTTP 409)."""

    @pytest.mark.parametrize(
        ("start_str", "expected_festival_day"),
        [
            # Day before festival starts
            ("2027-06-09T20:00", "2027-06-09"),
            # Before 06:00 on first_day (2027-06-10) belongs to 2027-06-09
            ("2027-06-10T05:30", "2027-06-09"),
            # At/after 06:00 on day after last_day belongs to 2027-06-14
            ("2027-06-14T06:00", "2027-06-14"),
            ("2027-06-15T20:00", "2027-06-15"),
        ],
    )
    def test_date_outside_festival_range_returns_409(
        self,
        client: TestClient,
        start_str: str,
        expected_festival_day: str,
    ) -> None:
        payload = {
            "kind": "solo",
            "title": "Out of Range Show",
            "venue": "la-cabane",
            "start": start_str,
            "duration_minutes": 60,
            "artist": "ines-moreau",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                f"Performance date {expected_festival_day} is outside the "
                "festival (2027-06-10 to 2027-06-13)."
            )
        }

    def test_duplicate_performance_id_returns_409(self, client: TestClient) -> None:
        # Opening Gala is already at grand-casino on 2027-06-10T20:30
        payload = {
            "kind": "solo",
            "title": "Same Slot Show",
            "venue": "grand-casino",
            "start": "2027-06-10T20:30",
            "duration_minutes": 60,
            "artist": "ines-moreau",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": "A performance with id 'grand-casino-2027-06-10-2030' already exists."
        }

    @pytest.mark.parametrize(
        ("start_str", "duration_minutes"),
        [
            # Opening Gala at Grand Casino is 2027-06-10 20:30-22:30
            # Overlapping during Opening Gala
            ("2027-06-10T21:00", 60),
            # Ends at 20:15 (only 15m before 20:30)
            ("2027-06-10T19:15", 60),
            # Starts at 22:59 (only 29m after 22:30)
            ("2027-06-10T22:59", 60),
        ],
    )
    def test_venue_busy_within_30_minutes_returns_409(
        self,
        client: TestClient,
        test_data_path: Path,
        start_str: str,
        duration_minutes: int,
    ) -> None:
        initial_count = len(storage.load_data(test_data_path)["performances"])
        payload = {
            "kind": "solo",
            "title": "Venue Clash Show",
            "venue": "grand-casino",
            "start": start_str,
            "duration_minutes": duration_minutes,
            "artist": "ines-moreau",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Grand Casino is busy with Opening Gala "
                "(2027-06-10 20:30-22:30). Leave 30 minutes between two shows."
            )
        }
        assert len(storage.load_data(test_data_path)["performances"]) == initial_count

    def test_artist_busy_in_solo_show_at_another_venue_returns_409(
        self, client: TestClient
    ) -> None:
        # Sacha Diallo has "Family Business" at theatre-des-planches (2027-06-10 21:00-22:15)
        payload = {
            "kind": "solo",
            "title": "Double Booked Sacha",
            "venue": "la-cabane",
            "start": "2027-06-10T22:30",  # Only 15m after 22:15
            "duration_minutes": 60,
            "artist": "sacha-diallo",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Sacha Diallo is busy with Family Business "
                "(2027-06-10 21:00-22:15). Leave 30 minutes between two shows."
            )
        }

    def test_artist_busy_as_lineup_host_or_act_returns_409(
        self, client: TestClient
    ) -> None:
        # Paul Kerbrat hosts Opening Gala at grand-casino (2027-06-10 20:30-22:30)
        payload = {
            "kind": "solo",
            "title": "Paul Solo Clash",
            "venue": "la-cabane",
            "start": "2027-06-10T22:45",  # Only 15m after 22:30
            "duration_minutes": 60,
            "artist": "paul-kerbrat",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Paul Kerbrat is busy with Opening Gala "
                "(2027-06-10 20:30-22:30). Leave 30 minutes between two shows."
            )
        }

    def test_artist_busy_as_workshop_teacher_returns_409(
        self, client: TestClient
    ) -> None:
        # Inès Moreau teaches "Improv for Beginners" at la-cabane (2027-06-11 10:30-12:30)
        payload = {
            "kind": "solo",
            "title": "Inès Midday Show",
            "venue": "grand-casino",
            "start": "2027-06-11T12:45",  # Only 15m after 12:30
            "duration_minutes": 60,
            "artist": "ines-moreau",
        }

        response = client.post("/api/performances", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Inès Moreau is busy with Improv for Beginners "
                "(2027-06-11 10:30-12:30). Leave 30 minutes between two shows."
            )
        }


class TestAddPerformanceValidation:
    """Tests for invalid performance payloads (HTTP 422)."""

    def test_unknown_kind_returns_422(self, client: TestClient) -> None:
        payload = {
            "kind": "concert",
            "title": "Invalid Kind",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
        }
        response = client.post("/api/performances", json=payload)
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_duration", [0, -10, 361])
    def test_invalid_duration_returns_422(
        self, client: TestClient, invalid_duration: int
    ) -> None:
        payload = {
            "kind": "solo",
            "title": "Bad Duration",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": invalid_duration,
            "artist": "sacha-diallo",
        }
        response = client.post("/api/performances", json=payload)
        assert response.status_code == 422

    def test_lineup_duration_too_short_for_acts_returns_422(
        self, client: TestClient
    ) -> None:
        payload = {
            "kind": "lineup",
            "title": "Too Short Lineup",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 30,  # 3 acts require at least 36 minutes
            "host": "paul-kerbrat",
            "acts": ["nora-lebrun", "max-pellerin", "lea-fontaine"],
        }
        response = client.post("/api/performances", json=payload)
        assert response.status_code == 422

    def test_workshop_invalid_max_participants_returns_422(
        self, client: TestClient
    ) -> None:
        payload = {
            "kind": "workshop",
            "title": "Zero Capacity Workshop",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "teacher": "ines-moreau",
            "max_participants": 0,
        }
        response = client.post("/api/performances", json=payload)
        assert response.status_code == 422
