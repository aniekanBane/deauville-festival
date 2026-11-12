from fastapi.testclient import TestClient

from deauville_festival import errors
from deauville_festival.api.app import get_app


class TestPublicRoutes:
    """Tests for public API endpoints in `public_router`."""

    def test_get_festival(self, client: TestClient) -> None:
        response = client.get("/api/festival")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Deauville Festival du Rire 2027"
        assert data["first_day"] == "2027-06-10"
        assert data["last_day"] == "2027-06-13"
        assert len(data["days"]) == 4

    def test_list_venues(self, client: TestClient) -> None:
        response = client.get("/api/venues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert any(v["name"] == "Grand Casino" for v in data)

    def test_list_artists(self, client: TestClient) -> None:
        response = client.get("/api/artists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 12
        assert any(a["slug"] == "sacha-diallo" for a in data)

    def test_get_artist_success(self, client: TestClient) -> None:
        response = client.get("/api/artists/sacha-diallo")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sacha Diallo"
        assert "performances" in data
        assert len(data["performances"]) >= 1

    def test_get_artist_not_found(self, client: TestClient) -> None:
        response = client.get("/api/artists/unknown-artist")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_programme_unfiltered(self, client: TestClient) -> None:
        response = client.get("/api/programme")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 23

    def test_get_programme_filtered_by_day(self, client: TestClient) -> None:
        response = client.get("/api/programme", params={"day": "2027-06-10"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_programme_filtered_by_venue(self, client: TestClient) -> None:
        response = client.get("/api/programme", params={"venue": "grand-casino"})
        assert response.status_code == 200
        data = response.json()
        assert all(p["venue"] == "grand-casino" for p in data)

    def test_get_programme_with_invalid_venue_slug_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/programme", params={"venue": "---"})
        assert response.status_code == 422

    def test_get_performance_success(self, client: TestClient) -> None:
        response = client.get("/api/performances/grand-casino-2027-06-10-2030")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "grand-casino-2027-06-10-2030"
        assert data["kind"] == "lineup"

    def test_get_performance_not_found(self, client: TestClient) -> None:
        response = client.get("/api/performances/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Performance 'nonexistent-id' not found."

    def test_on_now_with_at_param(self, client: TestClient) -> None:
        response = client.get("/api/now", params={"at": "2027-06-10T21:00"})
        assert response.status_code == 200
        data = response.json()
        assert data["at"] == "2027-06-10T21:00"
        assert "now_playing" in data
        assert "up_next" in data

    def test_on_now_without_at_param(self, client: TestClient) -> None:
        response = client.get("/api/now")
        assert response.status_code == 200
        data = response.json()
        assert "at" in data
        assert "now_playing" in data


class TestAppModule:
    """Tests for app factory and exception handling."""

    def test_get_app(self, tmp_path, monkeypatch) -> None:
        import shutil

        from deauville_festival import config

        shutil.copy(config.DATA_DIR / "festival.json", tmp_path / "festival.json")
        monkeypatch.setattr("deauville_festival.config.DATA_DIR", tmp_path)
        app = get_app()
        assert app.title == "Deauville Festival API"

    def test_festival_exception_handler_default_status_500(
        self, client: TestClient
    ) -> None:
        class UnknownFestivalError(errors.FestivalError):
            pass

        @client.app.get("/api/test-festival-error")  # type: ignore[attr-defined]
        def route_raising_error():
            raise UnknownFestivalError("Something unknown happened")

        response = client.get("/api/test-festival-error")
        assert response.status_code == 500
        assert response.json() == {"detail": "Something unknown happened"}
