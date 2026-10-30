import abc
import dataclasses
import functools
import typing
from datetime import date, datetime, time, timedelta

from deauville_festival import errors, helpers

__all__ = [
    "Venue",
    "Artist",
    "Performance",
    "PerformanceKind",
    "SoloPerformance",
    "LineupPerformance",
    "WorkshopPerformance",
]


@dataclasses.dataclass(kw_only=True)
class Venue:
    """Represents a venue at the festival."""

    name: str
    capacity: int
    address: str

    def __post_init__(self) -> None:
        self.name = _required_value(self.name, "venue name")
        self.address = _required_value(self.address, "venue address")
        if not helpers.get_slug(self.name):
            raise errors.InvalidError("Venue name must contain letters or digits.")
        if self.capacity < 1:
            raise errors.InvalidError("Capacity must be a positive integer.")

    @property
    def slug(self) -> str:
        """Returns a slug for the venue name."""
        return helpers.get_slug(self.name)

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Venue):
            return False
        return self.slug == other.slug

    @typing.override
    def __hash__(self) -> int:
        return hash(self.slug)

    @typing.override
    def __str__(self) -> str:
        return f"{self.slug}: {self.name} ({self.address}), {self.capacity} seats"


@dataclasses.dataclass(kw_only=True)
class Artist:
    """Represents an artist performing at the festival."""

    name: str
    bio: str
    photo_url: str

    def __post_init__(self) -> None:
        self.name = _required_value(self.name, "artist name")
        self.bio = self.bio.strip()
        self.photo_url = self.photo_url.strip()
        if not helpers.get_slug(self.name):
            raise errors.InvalidError("Artist name must contain letters or digits.")

    @property
    def slug(self) -> str:
        """Returns a slug for the artist name."""
        return helpers.get_slug(self.name)

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Artist):
            return False
        return self.slug == other.slug

    @typing.override
    def __hash__(self) -> int:
        return hash(self.slug)

    @typing.override
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


PerformanceKind = typing.Literal["solo", "lineup", "workshop"]
"""Represents the different types of performance kinds."""


def _required_value(value: str, label: str) -> str:
    """Normalizes a required string and rejects blank values."""
    return helpers.guard_empty_str(value, label)


@functools.total_ordering
@dataclasses.dataclass(kw_only=True)
class Performance(abc.ABC):
    """Represents a performance at the festival."""

    DURATION_MINUTES_MAX: typing.ClassVar[int] = 360
    DURATION_MINUTES_MIN: typing.ClassVar[int] = 1

    kind: PerformanceKind
    title: str
    venue: str
    start: datetime
    duration_minutes: int
    description: str = ""

    def __post_init__(self) -> None:
        self.title = _required_value(self.title, "performance title")
        self.venue = _required_value(self.venue, "venue slug")
        self.description = self.description.strip()
        if not (
            self.DURATION_MINUTES_MIN
            <= self.duration_minutes
            <= self.DURATION_MINUTES_MAX
        ):
            raise errors.InvalidError(
                f"Duration must be between {self.DURATION_MINUTES_MIN} "
                f"and {self.DURATION_MINUTES_MAX} minutes."
            )

    @property
    def id(self) -> str:
        """Returns a unique identifier for the performance."""
        return f"{self.venue}-{self.start:%Y-%m-%d-%H%M}"

    @property
    def end(self) -> datetime:
        """Returns the end time of the performance."""
        return self.start + timedelta(minutes=self.duration_minutes)

    def is_on(self, at: datetime) -> bool:
        """Returns True if the performance is on at the given datetime."""
        return self.start <= at < self.end

    def get_festival_day(self) -> date:
        """Returns the festival day for the performance.

        A festival day starts at 6:00 AM and ends at 5:59 AM the next day.
        If a performance starts before 6:00 AM, it is considered part of the previous festival day.
        """
        festival_day = self.start.date()
        if self.start.time() < time(hour=6):
            festival_day -= timedelta(days=1)

        return festival_day

    @abc.abstractmethod
    def get_all_artists(self) -> tuple[str, ...]:
        """Returns the slugs of all the artists in the performance."""
        ...

    @abc.abstractmethod
    def involves_artist(self, artist_slug: str) -> str | None:
        """Returns the role of the artist in the performance."""
        ...

    def __lt__(self, other: "Performance") -> bool:
        return (self.start, self.venue) < (other.start, other.venue)

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Performance):
            return False
        if type(self) is not type(other):
            return False
        return self.id == other.id

    @typing.override
    def __hash__(self) -> int:
        return hash(self.id)


@dataclasses.dataclass(kw_only=True, eq=False)
class SoloPerformance(Performance):
    """Represents a solo performance at the festival."""

    MIN_AGE_LOWER: typing.ClassVar[int] = 0
    MIN_AGE_UPPER: typing.ClassVar[int] = 18

    artist: str
    min_age: int = 0
    kind: PerformanceKind = "solo"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.artist = _required_value(self.artist, "artist slug")
        if not (self.MIN_AGE_LOWER <= self.min_age <= self.MIN_AGE_UPPER):
            raise errors.InvalidError(
                f"Minimum age must be between {self.MIN_AGE_LOWER} and {self.MIN_AGE_UPPER}."
            )

    @typing.override
    def get_all_artists(self) -> tuple[str, ...]:
        return (self.artist,)

    @typing.override
    def involves_artist(self, artist_slug: str) -> str | None:
        return "artist" if self.artist == artist_slug else None


@dataclasses.dataclass(kw_only=True, eq=False)
class LineupPerformance(Performance):
    """Represents a lineup performance at the festival."""

    ACTS_MIN: typing.ClassVar[int] = 2
    """Minimum number of acts in a lineup performance."""

    host: str
    acts: list[str]
    kind: PerformanceKind = "lineup"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.host = _required_value(self.host, "host artist slug")
        self.acts = [_required_value(act, "act artist slug") for act in self.acts]
        if self.host in self.acts:
            raise errors.InvalidError("The host cannot be an act.")
        if len(self.acts) < self.ACTS_MIN:
            raise errors.InvalidError(
                f"Lineup performances must have at least {self.ACTS_MIN} acts."
            )
        if len(set(self.acts)) != len(self.acts):
            raise errors.InvalidError("Lineup performances cannot have duplicate acts.")
        min_duration = (len(self.acts) * 10) + ((len(self.acts) - 1) * 3)
        if self.duration_minutes < min_duration:
            raise errors.InvalidError("Duration is too short for the number of acts.")

    @typing.override
    def get_all_artists(self) -> tuple[str, ...]:
        return self.host, *self.acts

    @typing.override
    def involves_artist(self, artist_slug: str) -> str | None:
        if self.host == artist_slug:
            return "host"
        if artist_slug in self.acts:
            return "act"
        return None


@dataclasses.dataclass(kw_only=True, eq=False)
class WorkshopPerformance(Performance):
    """Represents a workshop performance at the festival."""

    teacher: str
    max_participants: int
    participants: list[str] = dataclasses.field(default_factory=list)
    kind: PerformanceKind = "workshop"

    @property
    def remaining_capacity(self) -> int:
        return self.max_participants - len(self.participants)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.teacher = _required_value(self.teacher, "teacher artist slug")
        self.participants = [
            _required_value(participant, "participant name")
            for participant in self.participants
        ]
        if self.max_participants < 1:
            raise errors.InvalidError("Max participants must be positive.")
        normalized_participants = [
            participant.casefold() for participant in self.participants
        ]
        if len(set(normalized_participants)) != len(normalized_participants):
            raise errors.InvalidError("Cannot have duplicate participants.")
        if len(self.participants) > self.max_participants:
            raise errors.InvalidError(
                "Cannot have more participants than max capacity."
            )

    def add_participant(self, participant: str) -> None:
        participant = _required_value(participant, "participant name")
        if any(p.lower() == participant.lower() for p in self.participants):
            raise errors.ConflictError("Participant already registered.")
        if self.remaining_capacity == 0:
            raise errors.InvalidError("Workshop is full.")
        self.participants.append(participant)

    @typing.override
    def get_all_artists(self) -> tuple[str, ...]:
        return (self.teacher,)

    @typing.override
    def involves_artist(self, artist_slug: str) -> str | None:
        return "teacher" if self.teacher == artist_slug else None
