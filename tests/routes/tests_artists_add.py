from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival import storage


class TestAddArtistSuccess:
    """Tests for successful artist creation via `POST /api/artists`."""

    def test_add_artist_with_all_fields_returns_201_and_persists(
        self, client: TestClient, test_data_path: Path
    ) -> None:
        payload = {
            "name": "Claire Dumont",
            "bio": "Stand-up comedian from Paris.",
            "photo_url": "https://example.com/claire.jpg",
        }

        response = client.post("/api/artists", json=payload)

        assert response.status_code == 201
        assert response.json() == {
            "slug": "claire-dumont",
            "name": "Claire Dumont",
            "photo_url": "https://example.com/claire.jpg",
        }

        # Verify persistence to the temporary JSON file
        saved_data = storage.load_data(test_data_path)
        saved_artists = {artist.slug: artist for artist in saved_data["artists"]}
        assert "claire-dumont" in saved_artists
        assert saved_artists["claire-dumont"].name == "Claire Dumont"
        assert saved_artists["claire-dumont"].bio == "Stand-up comedian from Paris."
        assert (
            saved_artists["claire-dumont"].photo_url == "https://example.com/claire.jpg"
        )

    def test_add_artist_with_only_name_uses_defaults(self, client: TestClient) -> None:
        response = client.post("/api/artists", json={"name": "Camille Roux"})

        assert response.status_code == 201
        assert response.json() == {
            "slug": "camille-roux",
            "name": "Camille Roux",
            "photo_url": "",
        }

    def test_add_artist_strips_surrounding_whitespace_from_name(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/artists",
            json={
                "name": "   Chloé Mercier  \n",
                "bio": "  Bio with spaces  ",
                "photo_url": "  https://example.com/photo.jpg  ",
            },
        )

        assert response.status_code == 201
        assert response.json() == {
            "slug": "chloe-mercier",
            "name": "Chloé Mercier",
            "photo_url": "https://example.com/photo.jpg",
        }


class TestAddArtistConflict:
    """Tests for duplicate artist conflicts (HTTP 409) on `POST /api/artists`."""

    @pytest.mark.parametrize(
        ("duplicate_name", "expected_slug"),
        [
            ("Hugo Lemaire", "hugo-lemaire"),
            ("hugo-lemaire", "hugo-lemaire"),
            ("  INÈS  MOREAU ! ", "ines-moreau"),
            ("Ines Moreau", "ines-moreau"),
            ("Élodie Marchal", "elodie-marchal"),
        ],
    )
    def test_add_existing_artist_slug_returns_409_conflict(
        self,
        client: TestClient,
        test_data_path: Path,
        duplicate_name: str,
        expected_slug: str,
    ) -> None:
        initial_count = len(storage.load_data(test_data_path)["artists"])

        response = client.post(
            "/api/artists",
            json={"name": duplicate_name, "bio": "Duplicate artist"},
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": f"Artist '{expected_slug}' already exists."
        }
        assert len(storage.load_data(test_data_path)["artists"]) == initial_count


class TestAddArtistValidation:
    """Tests for invalid payloads (HTTP 422) on `POST /api/artists`."""

    def test_missing_name_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/artists", json={"bio": "No name provided"})
        assert response.status_code == 422

    @pytest.mark.parametrize("empty_name", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_name_returns_422(
        self, client: TestClient, empty_name: str
    ) -> None:
        response = client.post("/api/artists", json={"name": empty_name})
        assert response.status_code == 422

    def test_name_exceeding_max_length_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/artists", json={"name": "A" * 65})
        assert response.status_code == 422

    def test_bio_exceeding_max_length_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/artists",
            json={"name": "Valid Name", "bio": "B" * 256},
        )
        assert response.status_code == 422

    def test_photo_url_exceeding_max_length_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/artists",
            json={
                "name": "Valid Name",
                "photo_url": "https://example.com/" + ("p" * 190),
            },
        )
        assert response.status_code == 422
