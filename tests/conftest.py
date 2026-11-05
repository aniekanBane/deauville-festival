from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival import config
from deauville_festival.api.app import create_app
from deauville_festival.storage import JSONFileStorage, SQLiteStorage

_SOURCE_DATA_PATH = config.DATA_DIR / "festival.json"


@pytest.fixture
def test_data_path(tmp_path: Path) -> Path:
    """Returns an isolated, pre-seeded database path."""
    database_path = tmp_path / "festival.db"
    SQLiteStorage(database_path).save(JSONFileStorage(_SOURCE_DATA_PATH).load())
    return database_path


@pytest.fixture
def client(test_data_path: Path) -> Iterator[TestClient]:
    """Returns a FastAPI client backed by the isolated database."""
    with TestClient(create_app(SQLiteStorage(test_data_path))) as test_client:
        yield test_client
