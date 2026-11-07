from typing import Annotated, cast

from fastapi import Depends, Request

from deauville_festival.festival import FestivalManager
from deauville_festival.storage.stores import DataStorage


def get_storage(request: Request) -> DataStorage:
    return cast(DataStorage, request.app.state.storage)


StorageDep = Annotated[DataStorage, Depends(get_storage)]


def get_festival_manager(storage: StorageDep) -> FestivalManager:
    """Returns a FestivalManager instance using the provided DataStorage."""
    return FestivalManager.from_storage(storage)


FestivalManageDep = Annotated[FestivalManager, Depends(get_festival_manager)]
