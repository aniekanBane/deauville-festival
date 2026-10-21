from dataclasses import dataclass, field
from datetime import datetime


@dataclass(kw_only=True)
class Venue:
    name: str
    capacity: int
    address: str


@dataclass(kw_only=True)
class Artist:
    name: str
    bio: str
    photo_url: str


@dataclass(kw_only=True)
class Performance:
    kind: str
    title: str
    venue: str
    start: datetime
    duration_minutes: int
    description: str
    min_age: int | None = None
    artist: str | None = None
    host: str | None = None
    teacher: str | None = None
    max_participants: int | None = None
    acts: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
