import abc
import dataclasses
import datetime
import json
import sqlite3
import typing
from pathlib import Path

from deauville_festival import errors, helpers
from deauville_festival.models import (
    PERFORMANCE_REGISTRY,
    Artist,
    LineupPerformance,
    Performance,
    PerformanceKind,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)


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


@typing.final
class SQLiteStorage(DataStorage):
    """Data storage in a SQLite database."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    @typing.override
    def load(self) -> dict[str, typing.Any]:
        with self._connect() as conn:
            return self._load(conn)

    def is_initialized(self) -> bool:
        """Returns whether the database contains festival data."""
        with self._connect() as conn:
            return (
                conn.execute("SELECT 1 FROM festival LIMIT 1;").fetchone() is not None
            )

    @typing.override
    def save(self, data: dict[str, typing.Any]) -> None:
        with self._connect() as conn, conn:
            self._clear(conn)
            self._save(conn, data)

    def _initialize(self) -> None:
        schema_path = Path(__file__).parent / "festival_schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
            with self._connect() as conn:
                conn.executescript(schema_sql)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _load(self, conn: sqlite3.Connection) -> dict[str, typing.Any]:
        festival = conn.execute(
            "SELECT name, first_day, last_day FROM festival LIMIT 1;"
        ).fetchone()

        if festival is None:
            raise errors.StorageError("Festival data has not been initialized.")

        venues = [
            Venue(
                name=row["name"],
                capacity=row["capacity"],
                address=row["address"],
            )
            for row in conn.execute(
                "SELECT name, capacity, address FROM venues ORDER BY rowid;"
            ).fetchall()
        ]

        artists = [
            Artist(
                name=row["name"],
                bio=row["bio"],
                photo_url=row["photo_url"],
            )
            for row in conn.execute(
                "SELECT name, bio, photo_url FROM artists ORDER BY rowid;"
            ).fetchall()
        ]

        performances = [
            self._parse_performance(row, conn)
            for row in conn.execute(
                "SELECT * FROM performances ORDER BY start, venue_slug;"
            ).fetchall()
        ]

        return {
            "name": festival["name"],
            "first_day": helpers.date_from_str(festival["first_day"]),
            "last_day": helpers.date_from_str(festival["last_day"]),
            "venues": venues,
            "artists": artists,
            "performances": performances,
        }

    def _parse_performance(
        self, row: sqlite3.Row, conn: sqlite3.Connection
    ) -> Performance:
        common = {
            "title": row["title"],
            "venue": row["venue_slug"],
            "start": helpers.datetime_from_str(row["start"]),
            "duration_minutes": row["duration_minutes"],
            "description": row["description"],
        }

        match row["kind"]:
            case "solo":
                return SoloPerformance(
                    **common,
                    artist=self._required_column(row, "artist_slug"),
                    min_age=self._required_column(row, "min_age"),
                )
            case "lineup":
                acts = conn.execute(
                    "SELECT artist_slug FROM lineup_performance_acts "
                    "WHERE performance_id = ? ORDER BY rowid;",
                    (row["performance_id"],),
                ).fetchall()
                return LineupPerformance(
                    **common,
                    host=self._required_column(row, "host_slug"),
                    acts=[act["artist_slug"] for act in acts],
                )
            case "workshop":
                return WorkshopPerformance(
                    **common,
                    teacher=self._required_column(row, "teacher_slug"),
                    max_participants=self._required_column(row, "max_participants"),
                    participants=json.loads(self._required_column(row, "participants")),
                )
            case _:
                raise errors.StorageError(f"Unknown performance kind: {row['kind']!r}.")

    def _required_column(self, row: sqlite3.Row, column: str) -> typing.Any:
        value = row[column]
        if value is None:
            raise errors.StorageError(
                f"Performance is missing required column '{column!r}' for kind {row['kind']!r}."
            )
        return value

    def _clear(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM lineup_performance_acts;")
        conn.execute("DELETE FROM performances;")
        conn.execute("DELETE FROM artists;")
        conn.execute("DELETE FROM venues;")
        conn.execute("DELETE FROM festival;")

    def _save(self, conn: sqlite3.Connection, data: dict[str, typing.Any]) -> None:
        conn.execute(
            "INSERT INTO festival (festival_id, name, first_day, last_day) VALUES (1, ?, ?, ?);",
            (
                data["name"],
                typing.cast(datetime.date, data["first_day"]).isoformat(),
                typing.cast(datetime.date, data["last_day"]).isoformat(),
            ),
        )

        for venue in typing.cast(list[Venue], data["venues"]):
            conn.execute(
                "INSERT INTO venues (slug, name, capacity, address) VALUES (?, ?, ?, ?);",
                (venue.slug, venue.name, venue.capacity, venue.address),
            )

        for artist in typing.cast(list[Artist], data["artists"]):
            conn.execute(
                "INSERT INTO artists (slug, name, bio, photo_url) VALUES (?, ?, ?, ?);",
                (artist.slug, artist.name, artist.bio, artist.photo_url),
            )

        self._insert_performance_records(conn, data)

    def _insert_performance_records(
        self, conn: sqlite3.Connection, data: dict[str, typing.Any]
    ) -> None:
        for performance in typing.cast(list[Performance], data["performances"]):
            common = (
                performance.title,
                performance.venue,
                helpers.datetime_to_str(performance.start),
                performance.duration_minutes,
                performance.description,
            )

            match performance:
                case SoloPerformance():
                    conn.execute(
                        "INSERT INTO performances (kind, title, venue_slug, start, duration_minutes, description, artist_slug, min_age) "
                        "VALUES ('solo', ?, ?, ?, ?, ?, ?, ?);",
                        (*common, performance.artist, performance.min_age),
                    )
                case LineupPerformance():
                    cursor = conn.execute(
                        "INSERT INTO performances (kind, title, venue_slug, start, duration_minutes, description, host_slug) "
                        "VALUES ('lineup', ?, ?, ?, ?, ?, ?);",
                        (*common, performance.host),
                    )
                    performance_id = cursor.lastrowid
                    for act in performance.acts:
                        conn.execute(
                            "INSERT INTO lineup_performance_acts (performance_id, artist_slug) VALUES (?, ?);",
                            (performance_id, act),
                        )
                case WorkshopPerformance():
                    conn.execute(
                        "INSERT INTO performances (kind, title, venue_slug, start, duration_minutes, description, teacher_slug, max_participants, participants) "
                        "VALUES ('workshop', ?, ?, ?, ?, ?, ?, ?, ?);",
                        (
                            *common,
                            performance.teacher,
                            performance.max_participants,
                            json.dumps(performance.participants),
                        ),
                    )
                case _:
                    raise errors.StorageError(
                        f"Unknown performance kind: {type(performance).__name__}."
                    )


@typing.final
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
                    json.load(f, object_hook=self._festival_data_json_decoder),
                )
        except FileNotFoundError:
            raise errors.StorageError(f"File not found: {self._path}.") from None
        except json.JSONDecodeError as e:
            raise errors.StorageError(
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
        self, dict_data: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        if "first_day" in dict_data:
            dict_data["first_day"] = helpers.date_from_str(dict_data["first_day"])
        if "last_day" in dict_data:
            dict_data["last_day"] = helpers.date_from_str(dict_data["last_day"])
        if "venues" in dict_data:
            dict_data["venues"] = [Venue(**venue) for venue in dict_data["venues"]]
        if "artists" in dict_data:
            dict_data["artists"] = [Artist(**artist) for artist in dict_data["artists"]]
        if "performances" in dict_data:
            dict_data["performances"] = [
                self._parse_performance(performance)
                for performance in dict_data["performances"]
            ]

        return dict_data

    def _parse_performance(self, performance: dict[str, typing.Any]) -> Performance:
        performance_data: dict[str, typing.Any] = {
            **performance,
            "start": helpers.datetime_from_str(performance["start"]),
        }
        performance_data.pop("kind", None)  # Remove 'kind' from the data dictionary
        try:
            kind = typing.cast(PerformanceKind, performance.get("kind"))
            performance_class = PERFORMANCE_REGISTRY[kind]
        except KeyError:
            raise errors.StorageError(
                f"Unknown performance kind: {performance.get('kind')!r}."
            ) from None
        return performance_class(**performance_data)


@typing.final
class FestivalDataJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for FestivalData."""

    @typing.override
    def default(self, o: object) -> typing.Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            data = dataclasses.asdict(o)
            if isinstance(o, Performance):
                data["kind"] = o.kind
            return data

        if isinstance(o, datetime.datetime):
            return helpers.datetime_to_str(o)

        if isinstance(o, datetime.date):
            return o.isoformat()

        return super().default(o)


def load_data(path: Path) -> dict[str, typing.Any]:
    """Loads festival data from a storage."""
    storage = SQLiteStorage(path) if path.suffix == ".db" else JSONFileStorage(path)
    return storage.load()


def save_data(data: dict[str, typing.Any], path: Path) -> None:
    """Saves festival data to a JSON file."""
    JSONFileStorage(path).save(data)
