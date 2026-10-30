from pathlib import Path
from typing import Annotated

from fastapi import Depends

from deauville_festival.festival import FestivalManager
from deauville_festival.storage import DataStorage, JSONFileStorage

DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "festival.json"
)


def get_storage() -> DataStorage:
    return JSONFileStorage(DATA_PATH)


StorageDep = Annotated[DataStorage, Depends(get_storage)]


def get_manager(storage: StorageDep) -> FestivalManager:
    return FestivalManager.from_storage(storage)


FestivalManageDep = Annotated[FestivalManager, Depends(get_manager)]
