from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival import storage
from deauville_festival.models import WorkshopPerformance


class TestRegisterParticipantSuccess:
    """Tests for successful participant registration (HTTP 201) via `POST /api/performances/{id}/participants`."""

    def test_register_participant_returns_201_and_persists(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        # "Improv for Beginners" at la-cabane on 2027-06-11T10:30 has 3/12 participants
        workshop_id = "la-cabane-2027-06-11-1030"

        response = client.post(
            f"/api/performances/{workshop_id}/participants",
            json={"name": "  Lucas M.  "},
        )

        assert response.status_code == 201
        assert response.json() == {"workshop": "Improv for Beginners"}

        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        workshop = saved_perfs[workshop_id]
        assert isinstance(workshop, WorkshopPerformance)
        assert "Lucas M." in workshop.participants
        assert len(workshop.participants) == 4


class TestRegisterParticipantErrors:
    """Tests for error handling (404, 409, 422) on `POST /api/performances/{id}/participants`."""

    def test_unknown_performance_id_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/performances/nonexistent-workshop-id/participants",
            json={"name": "Lucas M."},
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Performance 'nonexistent-workshop-id' not found."
        }

    @pytest.mark.parametrize(
        "non_workshop_id",
        [
            # Lineup performance
            "grand-casino-2027-06-10-2030",
            # Solo performance
            "theatre-des-planches-2027-06-10-2100",
        ],
    )
    def test_register_on_non_workshop_performance_returns_409(
        self, client: TestClient, non_workshop_id: str
    ) -> None:
        response = client.post(
            f"/api/performances/{non_workshop_id}/participants",
            json={"name": "Lucas M."},
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": f"Performance '{non_workshop_id}' is not a workshop."
        }

    @pytest.mark.parametrize(
        "duplicate_name",
        [
            "Camille R.",
            "camille r.",
            "  CAMILLE R.  ",
        ],
    )
    def test_duplicate_participant_case_insensitive_returns_409(
        self,
        client: TestClient,
        test_data_path: Path,
        duplicate_name: str,
    ) -> None:
        # "Camille R." is already registered in la-cabane-2027-06-11-1030
        workshop_id = "la-cabane-2027-06-11-1030"

        response = client.post(
            f"/api/performances/{workshop_id}/participants",
            json={"name": duplicate_name},
        )

        assert response.status_code == 409
        assert response.json() == {"detail": "Participant already registered."}

        saved_perfs = {
            p.id: p for p in storage.load_data(test_data_path)["performances"]
        }
        workshop = saved_perfs[workshop_id]
        assert isinstance(workshop, WorkshopPerformance)
        assert len(workshop.participants) == 3

    def test_register_when_workshop_is_full_returns_422(
        self, client: TestClient
    ) -> None:
        # Create a workshop with max_participants=1 and 1 initial participant
        create_resp = client.post(
            "/api/performances",
            json={
                "kind": "workshop",
                "title": "One-on-One Coaching",
                "venue": "la-cabane",
                "start": "2027-06-10T10:00",
                "duration_minutes": 60,
                "teacher": "ines-moreau",
                "max_participants": 1,
                "participants": ["Alice B."],
            },
        )
        assert create_resp.status_code == 201
        workshop_id = "la-cabane-2027-06-10-1000"

        response = client.post(
            f"/api/performances/{workshop_id}/participants",
            json={"name": "Bob C."},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Workshop is full."}

    @pytest.mark.parametrize("invalid_name", ["", "   ", "\t\n", "A" * 101])
    def test_invalid_participant_name_returns_422(
        self, client: TestClient, invalid_name: str
    ) -> None:
        workshop_id = "la-cabane-2027-06-11-1030"

        response = client.post(
            f"/api/performances/{workshop_id}/participants",
            json={"name": invalid_name},
        )

        assert response.status_code == 422

