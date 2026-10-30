import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville_festival.api import app, dependencies

_SOURCE_DATA_PATH = Path(__file__).parent.parent / "data" / "festival.json"


@pytest.fixture
def test_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copies the festival data file into a temporary directory and patches `dependencies.DATA_PATH`."""
    temp_data_file = tmp_path / "festival.json"
    shutil.copy(_SOURCE_DATA_PATH, temp_data_file)
    monkeypatch.setattr(dependencies, "DATA_PATH", temp_data_file)
    return temp_data_file


@pytest.fixture
def client(test_data_path: Path) -> TestClient:
    """Returns a FastAPI `TestClient` backed by the isolated temporary data file."""
    return TestClient(app.app)
