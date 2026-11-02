from pathlib import Path
from typing import Annotated

from fastapi import Depends

from deauville_festival.festival import FestivalManager
from deauville_festival.storage import DataStorage, SQLiteStorage

DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "festival.db"
)


def get_storage() -> DataStorage:
    return SQLiteStorage(DATA_PATH)


StorageDep = Annotated[DataStorage, Depends(get_storage)]


def get_manager(storage: StorageDep) -> FestivalManager:
    return FestivalManager.from_storage(storage)


FestivalManageDep = Annotated[FestivalManager, Depends(get_manager)]
