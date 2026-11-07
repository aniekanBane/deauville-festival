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
    "PERFORMANCE_REGISTRY",
]


@dataclasses.dataclass(kw_only=True)
@typing.final
class Venue:
    """Represents a venue at the festival."""

    NAME_MAX_LEN: typing.ClassVar[int] = 128
    ADDRESS_MAX_LEN: typing.ClassVar[int] = 255
    CAPACITY_MIN_VALUE: typing.ClassVar[int] = 1

    name: str
    capacity: int
    address: str

    def __post_init__(self) -> None:
        self.name = self.validate_name(self.name)
        self.address = self.validate_address(self.address)
        self.capacity = self.validate_capacity(self.capacity)

    @property
    def slug(self) -> str:
        """Returns a slug for the venue name."""
        return helpers.get_slug(self.name)

    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validates the venue name."""
        label = "Venue name"
        name = helpers.guard_str_max_len(
            helpers.guard_empty_str(name, label), cls.NAME_MAX_LEN, label
        )
        if not helpers.get_slug(name):
            raise errors.InvalidError(f"{label} must contain letters or digits.")

        return name

    @classmethod
    def validate_address(cls, address: str) -> str:
        """Validates the venue address."""
        label = "Venue address"
        return helpers.guard_str_max_len(
            helpers.guard_empty_str(address, label), cls.ADDRESS_MAX_LEN, label
        )

    @classmethod
    def validate_capacity(cls, capacity: int) -> int:
        """Validates the venue capacity."""
        return helpers.guard_value_greater_than(
            capacity, cls.CAPACITY_MIN_VALUE, "Venue capacity"
        )

    @typing.override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Venue) and self.slug == other.slug

    @typing.override
    def __hash__(self) -> int:
        return hash(self.slug)

    @typing.override
    def __str__(self) -> str:
        return f"{self.slug}: {self.name} ({self.address}), {self.capacity} seats"


@dataclasses.dataclass(kw_only=True)
@typing.final
class Artist:
    """Represents an artist performing at the festival."""

    NAME_MAX_LEN: typing.ClassVar[int] = 65
    BIO_MAX_LEN: typing.ClassVar[int] = 1024
    PHOTO_URL_MAX_LEN: typing.ClassVar[int] = 255

    name: str
    bio: str = ""
    photo_url: str = ""

    def __post_init__(self) -> None:
        self.name = self.validate_name(self.name)
        self.bio = self.validate_bio(self.bio)
        self.photo_url = self.validate_photo_url(self.photo_url)

    @property
    def slug(self) -> str:
        """Returns a slug for the artist name."""
        return helpers.get_slug(self.name)

    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validates the artist name."""
        label = "Artist name"
        name = helpers.guard_str_max_len(
            helpers.guard_empty_str(name, label), cls.NAME_MAX_LEN, label
        )
        if not helpers.get_slug(name):
            raise errors.InvalidError(f"{label} must contain letters or digits.")

        return name

    @classmethod
    def validate_bio(cls, bio: str) -> str:
        """Validates the artist bio."""
        label = "Artist bio"
        bio = bio.strip()
        if bio:
            return helpers.guard_str_max_len(bio, cls.BIO_MAX_LEN, label)

        return bio

    @classmethod
    def validate_photo_url(cls, photo_url: str) -> str:
        """Validates the artist photo URL."""
        label = "Artist photo URL"
        photo_url = photo_url.strip()
        if photo_url:
            return helpers.guard_str_max_len(photo_url, cls.PHOTO_URL_MAX_LEN, label)

        return photo_url

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
"""Represents the different types of performances."""


@functools.total_ordering
@dataclasses.dataclass(kw_only=True, eq=False)
class Performance(abc.ABC):
    """Represents a performance at the festival."""

    TITLE_MAX_LEN: typing.ClassVar[int] = 128
    DURATION_MINUTES_MAX_VALUE: typing.ClassVar[int] = 360
    DURATION_MINUTES_MIN_VALUE: typing.ClassVar[int] = 1
    DESCRIPTION_MAX_LEN: typing.ClassVar[int] = 1024

    title: str
    venue: str
    start: datetime
    duration_minutes: int
    description: str = ""

    def __post_init__(self) -> None:
        self.title = self.validate_title(self.title)
        self.venue = self.validate_venue(self.venue)
        self.description = self.validate_description(self.description)
        self.duration_minutes = self.validate_duration_minutes(self.duration_minutes)

    @property
    @abc.abstractmethod
    def kind(self) -> PerformanceKind: ...

    @property
    @typing.final
    def id(self) -> str:
        """Returns a unique identifier for the performance."""
        return f"{self.venue}-{self.start:%Y-%m-%d-%H%M}"

    @property
    @typing.final
    def end(self) -> datetime:
        """Returns the end time of the performance."""
        return self.start + timedelta(minutes=self.duration_minutes)

    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validates the performance title."""
        label = "Performance title"
        return helpers.guard_str_max_len(
            helpers.guard_empty_str(title, label), cls.TITLE_MAX_LEN, label
        )

    @classmethod
    def validate_venue(cls, venue_slug: str) -> str:
        """Validates the performance venue."""
        return helpers.guard_empty_str(venue_slug, "Venue slug")

    @classmethod
    def validate_duration_minutes(cls, duration_minutes: int) -> int:
        """Validates the performance duration in minutes."""
        return helpers.guard_value_range(
            value=duration_minutes,
            min_value=cls.DURATION_MINUTES_MIN_VALUE,
            max_value=cls.DURATION_MINUTES_MAX_VALUE,
            label="Performance duration",
        )

    @classmethod
    def validate_description(cls, description: str) -> str:
        """Validates the performance description."""
        label = "Performance description"
        description = description.strip()
        if description:
            return helpers.guard_str_max_len(
                description, cls.DESCRIPTION_MAX_LEN, label
            )

        return description

    @abc.abstractmethod
    def get_all_artists(self) -> tuple[str, ...]:
        """Returns the slugs of all the artists in the performance."""
        ...

    @abc.abstractmethod
    def involves_artist(self, artist_slug: str) -> str | None:
        """Returns the role of the artist in the performance."""
        ...

    @typing.final
    def is_on(self, at: datetime) -> bool:
        """Returns True if the performance is on at the given datetime."""
        return self.start <= at < self.end

    @typing.final
    def get_festival_day(self) -> date:
        """Returns the festival day for the performance.

        A festival day starts at 6:00 AM and ends at 5:59 AM the next day.
        If a performance starts before 6:00 AM, it is considered part of the previous festival day.
        """
        festival_day = self.start.date()
        if self.start.time() < time(hour=6):
            festival_day -= timedelta(days=1)

        return festival_day

    @typing.final
    def __gt__(self, other: "Performance") -> bool:
        return (self.start, self.venue) > (other.start, other.venue)

    @typing.final
    def __lt__(self, other: "Performance") -> bool:
        return (self.start, self.venue) < (other.start, other.venue)

    @typing.override
    @typing.final
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Performance)
            and type(other) is type(self)
            and self.id == other.id
        )

    @typing.override
    @typing.final
    def __hash__(self) -> int:
        return hash(self.id)


@dataclasses.dataclass(kw_only=True, eq=False)
@typing.final
class SoloPerformance(Performance):
    """Represents a solo performance at the festival."""

    MIN_AGE_LOWER: typing.ClassVar[int] = 0
    MIN_AGE_UPPER: typing.ClassVar[int] = 18

    artist: str
    min_age: int = MIN_AGE_LOWER

    @typing.override
    def __post_init__(self) -> None:
        super().__post_init__()
        self.artist = self.validate_artist(self.artist)
        self.min_age = self.validate_min_age(self.min_age)

    @property
    @typing.override
    def kind(self) -> PerformanceKind:
        return "solo"

    @classmethod
    def validate_artist(cls, artist_slug: str) -> str:
        """Validates the artist slug for the solo performance."""
        return helpers.guard_empty_str(artist_slug, "Artist slug")

    @classmethod
    def validate_min_age(cls, min_age: int) -> int:
        """Validates the minimum age for the solo performance."""
        return helpers.guard_value_range(
            value=min_age,
            max_value=cls.MIN_AGE_UPPER,
            min_value=cls.MIN_AGE_LOWER,
            label="Minimum age",
        )

    @typing.override
    def get_all_artists(self) -> tuple[str, ...]:
        return (self.artist,)

    @typing.override
    def involves_artist(self, artist_slug: str) -> str | None:
        return "artist" if self.artist == artist_slug else None


@dataclasses.dataclass(kw_only=True, eq=False)
@typing.final
class LineupPerformance(Performance):
    """Represents a lineup performance at the festival."""

    ACTS_MIN_LEN: typing.ClassVar[int] = 2
    """Minimum number of acts in a lineup performance."""
    ACT_DURATION_MINUTES: typing.ClassVar[int] = 10
    """Minimum duration of each act in a lineup performance."""
    ACT_GAP_MINUTES: typing.ClassVar[int] = 3
    """Minimum gap between acts in a lineup performance."""

    host: str
    acts: list[str]

    @typing.override
    def __post_init__(self) -> None:
        super().__post_init__()
        self.host = self.validate_host(self.host)
        self.acts = self.validate_acts(self.acts)

    @property
    @typing.override
    def kind(self) -> PerformanceKind:
        return "lineup"

    @classmethod
    def validate_host(cls, host_slug: str) -> str:
        """Validates the host artist slug for the lineup performance."""
        return helpers.guard_empty_str(host_slug, "Host slug")

    @classmethod
    def validate_act(cls, act: str) -> str:
        """Validates a single act artist slug for the lineup performance."""
        return helpers.guard_empty_str(act, "Act artist slug")

    def validate_acts(self, acts: list[str]) -> list[str]:
        """Validates the list of act artist slugs for the lineup performance."""
        if len(acts) < self.ACTS_MIN_LEN:
            raise errors.InvalidError(
                f"Lineup performances must have at least {self.ACTS_MIN_LEN} acts."
            )

        validated_acts = [self.validate_act(act) for act in acts]
        if len(set(validated_acts)) != len(validated_acts):
            raise errors.InvalidError("Lineup performances cannot have duplicate acts.")

        if self.host in validated_acts:
            raise errors.InvalidError("The host cannot be an act.")

        min_duration = (len(validated_acts) * self.ACT_DURATION_MINUTES) + (
            (len(validated_acts) - 1) * self.ACT_GAP_MINUTES
        )
        if self.duration_minutes < min_duration:
            raise errors.InvalidError(
                "Duration is too short for the number of acts. "
                f"Must be at least {min_duration} minutes for {len(acts)} acts. "
                f"{self.ACT_DURATION_MINUTES} minutes per act, plus {self.ACT_GAP_MINUTES} minutes between acts."
            )

        return validated_acts

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
@typing.final
class WorkshopPerformance(Performance):
    """Represents a workshop performance at the festival."""

    MAX_PARTICIPANTS_MIN_VALUE: typing.ClassVar[int] = 1

    teacher: str
    max_participants: int
    participants: list[str] = dataclasses.field(default_factory=list)

    @typing.override
    def __post_init__(self) -> None:
        super().__post_init__()
        self.teacher = self.validate_teacher(self.teacher)
        self.max_participants = self.validate_max_participants(self.max_participants)
        self.participants = self.validate_participants(self.participants)
        normalized_participants = [
            helpers.get_slug(participant) for participant in self.participants
        ]
        if len(set(normalized_participants)) != len(normalized_participants):
            raise errors.InvalidError("Cannot have duplicate participants.")

    @property
    @typing.override
    def kind(self) -> PerformanceKind:
        return "workshop"

    @property
    def places_left(self) -> int:
        return self.max_participants - len(self.participants)

    @classmethod
    def validate_teacher(cls, teacher: str) -> str:
        """Validates the teacher slug for the workshop performance."""
        return helpers.guard_empty_str(teacher, "Teacher")

    @classmethod
    def validate_max_participants(cls, max_participants: int) -> int:
        """Validates the maximum number of participants for the workshop performance."""
        return helpers.guard_value_greater_than(
            max_participants,
            cls.MAX_PARTICIPANTS_MIN_VALUE,
            "Maximum participants",
        )

    def validate_participants(self, participants: list[str]) -> list[str]:
        """Validates the list of participants for the workshop performance."""
        if len(participants) > self.max_participants:
            raise errors.InvalidError(
                "Cannot have more participants than max capacity."
            )
        return [self.validate_participant(participant) for participant in participants]

    @classmethod
    def validate_participant(cls, participant: str) -> str:
        """Validates a single participant for the workshop performance."""
        return helpers.guard_empty_str(participant, "Participant name")

    def add_participant(self, participant: str) -> None:
        participant = self.validate_participant(participant)
        if self.has_participant(participant):
            raise errors.ConflictError("Participant already registered.")

        if self.places_left == 0:
            raise errors.ConflictError("Workshop is full.")

        self.participants.append(participant)

    @typing.override
    def get_all_artists(self) -> tuple[str, ...]:
        return (self.teacher,)

    @typing.override
    def involves_artist(self, artist_slug: str) -> str | None:
        return "teacher" if self.teacher == artist_slug else None

    def has_participant(self, participant: str) -> bool:
        """Returns True if the participant is registered for the workshop."""
        return any(
            helpers.get_slug(p) == helpers.get_slug(participant)
            for p in self.participants
        )


PERFORMANCE_REGISTRY: typing.Final[dict[PerformanceKind, type[Performance]]] = {
    "solo": SoloPerformance,
    "lineup": LineupPerformance,
    "workshop": WorkshopPerformance,
}
