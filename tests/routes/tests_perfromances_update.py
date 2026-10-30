from pathlib import Path

from fastapi.testclient import TestClient

from deauville_festival import storage


class TestUpdatePerformanceSuccess:
    """Tests for successful performance updates (HTTP 200) via `PUT /api/performances/{id}`."""

    def test_update_performance_in_place_same_slot_succeeds(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # "Family Business" is at theatre-des-planches on 2027-06-10T21:00 (75 mins)
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business: Director's Cut",
            "venue": "theatre-des-planches",
            "start": "2027-06-10T21:00",
            "duration_minutes": 90,
            "description": "Extended edition.",
            "artist": "sacha-diallo",
            "min_age": 12,
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Family Business: Director's Cut"
        assert data["duration_minutes"] == 90
        assert data["min_age"] == 12

        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        assert perf_id in saved_perfs
        assert saved_perfs[perf_id].title == "Family Business: Director's Cut"
        assert saved_perfs[perf_id].duration_minutes == 90

    def test_move_performance_to_new_venue_and_time_replaces_old_id(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        old_id = "theatre-des-planches-2027-06-10-2100"
        new_id = "la-cabane-2027-06-10-1800"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "la-cabane",
            "start": "2027-06-10T18:00",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
            "min_age": 0,
        }

        response = client.put(f"/api/performances/{old_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["venue"] == "la-cabane"
        assert data["start"] == "2027-06-10T18:00"

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert old_id not in saved_ids
        assert new_id in saved_ids

    def test_shift_performance_overlapping_its_own_previous_window_succeeds(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # Shifting Family Business from 21:00 to 21:15 should not conflict with its old self
        old_id = "theatre-des-planches-2027-06-10-2100"
        new_id = "theatre-des-planches-2027-06-10-2115"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "theatre-des-planches",
            "start": "2027-06-10T21:15",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
            "min_age": 0,
        }

        response = client.put(f"/api/performances/{old_id}", json=payload)

        assert response.status_code == 200
        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert old_id not in saved_ids
        assert new_id in saved_ids

    def test_update_workshop_caps_max_participants_to_venue_capacity(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # La Cabane has capacity 40
        perf_id = "la-cabane-2027-06-11-1030"
        payload = {
            "kind": "workshop",
            "title": "Improv for Beginners",
            "venue": "la-cabane",
            "start": "2027-06-11T10:30",
            "duration_minutes": 120,
            "teacher": "ines-moreau",
            "max_participants": 100,
            "participants": ["Camille R.", "Yanis B.", "Lou M."],
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 200
        assert response.json()["max_participants"] == 40
        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        assert saved_perfs[perf_id].max_participants == 40


class TestUpdatePerformanceNotFound:
    """Tests for 404 Not Found errors on `PUT /api/performances/{id}`."""

    def test_nonexistent_performance_id_returns_404(
        self, client: TestClient
    ) -> None:
        payload = {
            "kind": "solo",
            "title": "Ghost Show",
            "venue": "la-cabane",
            "start": "2027-06-10T14:00",
            "duration_minutes": 60,
            "artist": "sacha-diallo",
        }

        response = client.put(
            "/api/performances/la-cabane-2027-06-10-9999", json=payload
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Performance 'la-cabane-2027-06-10-9999' not found."
        }

    def test_unknown_target_venue_returns_404_and_preserves_original(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "unknown-venue",
            "start": "2027-06-10T21:00",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Venue 'unknown-venue' not found."}

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert perf_id in saved_ids

    def test_unknown_artist_returns_404_and_preserves_original(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "theatre-des-planches",
            "start": "2027-06-10T21:00",
            "duration_minutes": 75,
            "artist": "unknown-artist",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 404
        assert response.json() == {"detail": "Artist 'unknown-artist' not found."}

        saved_ids = {p.id for p in storage.load_data(test_data_path)["performances"]}
        assert perf_id in saved_ids


class TestUpdatePerformanceConflictAndAtomicity:
    """Tests for 409 Conflicts and rollback guarantees on `PUT /api/performances/{id}`."""

    def test_moving_onto_busy_venue_slot_returns_409_and_leaves_performance_unchanged(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # Move Family Business (theatre-des-planches 2027-06-10 21:00) onto
        # Grand Casino at 2027-06-10 21:00 where Opening Gala (20:30-22:30) is playing
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "grand-casino",
            "start": "2027-06-10T21:00",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Grand Casino is busy with Opening Gala "
                "(2027-06-10 20:30-22:30). Leave 30 minutes between two shows."
            )
        }

        # Original performance must remain untouched where it was
        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        assert perf_id in saved_perfs
        assert saved_perfs[perf_id].venue == "theatre-des-planches"

    def test_moving_onto_exact_same_id_as_another_performance_returns_409(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "grand-casino",
            "start": "2027-06-10T20:30",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": "A performance with id 'grand-casino-2027-06-10-2030' already exists."
        }
        assert perf_id in {
            p.id for p in storage.load_data(test_data_path)["performances"]
        }

    def test_moving_to_slot_where_artist_is_busy_returns_409_and_preserves_original(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # Nora Lebrun is in Opening Gala (2027-06-10 20:30-22:30).
        # Assigning her to Family Business at theatre-des-planches (2027-06-10 21:00) conflicts.
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "theatre-des-planches",
            "start": "2027-06-10T21:00",
            "duration_minutes": 75,
            "artist": "nora-lebrun",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Nora Lebrun is busy with Opening Gala "
                "(2027-06-10 20:30-22:30). Leave 30 minutes between two shows."
            )
        }

        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        assert saved_perfs[perf_id].artist == "sacha-diallo"  # type: ignore[attr-defined]

    def test_moving_outside_festival_dates_returns_409(
        self, client: TestClient
    ) -> None:
        perf_id = "theatre-des-planches-2027-06-10-2100"
        payload = {
            "kind": "solo",
            "title": "Family Business",
            "venue": "theatre-des-planches",
            "start": "2027-06-15T21:00",
            "duration_minutes": 75,
            "artist": "sacha-diallo",
        }

        response = client.put(f"/api/performances/{perf_id}", json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "detail": (
                "Performance date 2027-06-15 is outside the "
                "festival (2027-06-10 to 2027-06-13)."
            )
        }

