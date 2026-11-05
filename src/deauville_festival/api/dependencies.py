from typing import Annotated

from fastapi import Depends

from deauville_festival.festival import FestivalManager
from deauville_festival.storage.stores import DataStorage


def get_festival_manager(storage: Annotated[DataStorage, Depends()]) -> FestivalManager:
    """Returns a FestivalManager instance using the provided DataStorage."""
    return FestivalManager.from_storage(storage)


FestivalManageDep = Annotated[FestivalManager, Depends(get_festival_manager)]
