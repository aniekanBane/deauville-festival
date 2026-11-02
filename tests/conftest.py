from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival.api import app, dependencies

_SOURCE_DATA_PATH = Path(__file__).parent.parent / "data" / "festival.json"


@pytest.fixture
def test_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Returns an isolated database path and configures its seed source."""
    database_path = tmp_path / "festival.db"
    monkeypatch.setattr(dependencies, "DATA_PATH", database_path)
    database_path.with_name("festival.json").write_bytes(
        _SOURCE_DATA_PATH.read_bytes()
    )
    return database_path


@pytest.fixture
def client(test_data_path: Path):
    """Returns a FastAPI client whose lifespan initializes the isolated database."""
    with TestClient(app.app) as test_client:
        yield test_client
