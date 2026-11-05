from pathlib import Path

from fastapi.testclient import TestClient

from deauville_festival import storage


class TestDeletePerformance:
    """Tests for `DELETE /api/performances/{id}`."""

    def test_existing_performance_is_deleted_and_persisted(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        performance_id = "grand-casino-2027-06-10-2030"

        response = client.delete(f"/api/performances/{performance_id}")

        assert response.status_code == 204
        assert response.content == b""

        saved_ids = {
            performance.id
            for performance in storage.SQLiteStorage(test_data_path).load()[
                "performances"
            ]
        }
        assert performance_id not in saved_ids

    def test_unknown_performance_returns_404(
        self, client: TestClient
    ) -> None:
        performance_id = "nonexistent-performance"

        response = client.delete(f"/api/performances/{performance_id}")

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Performance '{performance_id}' not found."
        }
