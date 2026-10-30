import abc
import dataclasses
import json
import typing
from datetime import date, datetime
from pathlib import Path

from deauville_festival.models import (
    Artist,
    LineupPerformance,
    Performance,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)

__all__ = ["DataStorage", "JSONFileStorage"]


class DataStorage(abc.ABC):
    """Abstract base class for data storage."""

    @abc.abstractmethod
    def load(self) -> dict[str, typing.Any]:
        """Loads the festival data."""
        ...

    @abc.abstractmethod
    def save(self, data: dict[str, typing.Any]) -> None:
        """Saves the festival data."""
        ...


class JSONFileStorage(DataStorage):
    """Data storage in a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @typing.override
    def load(self) -> dict[str, typing.Any]:
        try:
            with open(self._path, encoding="utf-8") as f:
                return typing.cast(
                    dict[str, typing.Any],
                    json.load(f, object_hook=_festival_data_json_decoder),
                )
        except FileNotFoundError:
            print(f"File not found: {self._path}.")
            raise
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in file: {self._path} (line {e.lineno})."
            ) from None

    @typing.override
    def save(self, data: dict[str, typing.Any]) -> None:
        self._path.parent.mkdir(exist_ok=True)
        self._path.write_text(
            json.dumps(
                data,
                cls=FestivalDataJSONEncoder,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def _festival_data_json_decoder(
    dict_data: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    if "first_day" in dict_data and "last_day" in dict_data:
        dict_data["first_day"] = date.fromisoformat(dict_data["first_day"])
    if "last_day" in dict_data:
        dict_data["last_day"] = date.fromisoformat(dict_data["last_day"])
    if "venues" in dict_data:
        dict_data["venues"] = [Venue(**venue) for venue in dict_data["venues"]]
    if "artists" in dict_data:
        dict_data["artists"] = [Artist(**artist) for artist in dict_data["artists"]]
    if "performances" in dict_data:
        performance_classes: dict[str, type[Performance]] = {
            "solo": SoloPerformance,
            "lineup": LineupPerformance,
            "workshop": WorkshopPerformance,
        }
        decoded_performances = []
        for performance in dict_data["performances"]:
            performance_data: dict[str, typing.Any] = {
                **performance,
                "start": datetime.fromisoformat(performance["start"]),
            }
            try:
                kind = str(performance.get("kind"))
                performance_class = performance_classes[kind]
            except KeyError:
                raise ValueError(
                    f"Unknown performance kind: {performance.get('kind')!r}."
                ) from None
            decoded_performances.append(performance_class(**performance_data))
        dict_data["performances"] = decoded_performances

    return dict_data


def load_data(path: Path) -> dict[str, typing.Any]:
    """Loads the festival data from a JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            return typing.cast(
                dict[str, typing.Any],
                json.load(f, object_hook=_festival_data_json_decoder),
            )
    except FileNotFoundError:
        print(f"File not found: {path}.")
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {path} (line {e.lineno}).") from None


class FestivalDataJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for FestivalData."""

    @typing.override
    def default(self, o: object) -> typing.Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)

        if isinstance(o, datetime):
            return o.isoformat(timespec="minutes")

        if isinstance(o, date):
            return o.isoformat()

        return super().default(o)


def save_data(festival_data: dict[str, typing.Any], path: Path) -> None:
    """Saves the festival data to the JSON file."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            festival_data, f, cls=FestivalDataJSONEncoder, ensure_ascii=False, indent=2
        )
