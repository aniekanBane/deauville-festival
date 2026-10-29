import dataclasses
from datetime import date, datetime, time, timedelta
from typing import ClassVar, Literal

from helpers import get_slug


@dataclasses.dataclass(kw_only=True)
class Venue:
    name: str
    capacity: int
    address: str

    @property
    def slug(self) -> str:
        """Returns a slug for the venue name."""
        return get_slug(self.name)


@dataclasses.dataclass(kw_only=True)
class Artist:
    name: str
    bio: str
    photo_url: str

    @property
    def slug(self) -> str:
        """Returns a slug for the artist name."""
        return get_slug(self.name)


PerformanceKind = Literal["solo", "lineup", "workshop"]
"""Represents the different types of performance kinds."""


@dataclasses.dataclass(kw_only=True)
class Performance:
    """Represents a performance at the festival."""

    DURATION_MINUTES_MAX: ClassVar[int] = 360
    DURATION_MINUTES_MIN: ClassVar[int] = 1

    kind: PerformanceKind
    title: str
    venue: str
    start: datetime
    duration_minutes: int
    description: str = ""
    artist: str | None = None
    min_age: int | None = None
    host: str | None = None
    acts: list[str] | None = None
    teacher: str | None = None
    max_participants: int | None = None
    participants: list[str] | None = None

    @property
    def id(self) -> str:
        """Returns a unique identifier for the performance."""
        return f"{self.venue}-{self.start:%Y-%m-%d-%H%M}"

    @property
    def end(self) -> datetime:
        """Returns the end time of the performance."""
        return self.start + timedelta(minutes=self.duration_minutes)

    def get_festival_day(self) -> date:
        """Returns the festival day for the performance.

        A festival day starts at 6:00 AM and ends at 5:59 AM the next day.
        If a performance starts before 6:00 AM, it is considered part of the previous festival day.
        """
        festival_day = self.start.date()
        if self.start.time() < time(hour=6):
            festival_day -= timedelta(days=1)

        return festival_day
