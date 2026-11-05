from deauville_festival import config
from deauville_festival.storage.stores import SQLiteStorage, load_data


def seed_database(storage: SQLiteStorage) -> None:
    """Seeds the database with initial data if it is empty."""
    if not storage.is_initialized():
        path = config.DATA_DIR / "festival.json"
        storage.save(load_data(path))
