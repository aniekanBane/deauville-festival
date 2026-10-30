import dataclasses
from datetime import date, datetime, timedelta
from typing import Any

from deauville_festival import errors
from deauville_festival.models import (
    Artist,
    LineupPerformance,
    Performance,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)
from deauville_festival.storage import DataStorage


@dataclasses.dataclass(kw_only=True, frozen=True)
class FestivalInfo:
    """A container for festival information."""

    name: str
    first_day: date
    last_day: date
    days: tuple[date, ...]
    venue_count: int
    artist_count: int
    performance_count: int


class FestivalManager:
    """Festival manager class"""

    def __init__(
        self,
        *,
        name: str,
        first_day: date,
        last_day: date,
        venues: list[Venue],
        artists: list[Artist],
        performances: list[Performance],
        data_store: DataStorage | None = None,
    ):
        if not (name := name.strip()):
            raise ValueError("Name cannot be empty")
        if last_day <= first_day:
            raise ValueError("Last day must be after first day")

        self._name = name
        self._first_day = first_day
        self._last_day = last_day
        self._venues: list[Venue] = venues
        self._artists: list[Artist] = artists
        self._performances: list[Performance] = performances
        self._data_store = data_store

        self._days = tuple(
            self._first_day + timedelta(days=i)
            for i in range((self._last_day - self._first_day).days + 1)
        )

    @classmethod
    def from_storage(cls, storage: DataStorage) -> "FestivalManager":
        return cls(**storage.load(), data_store=storage)

    def save(self) -> None:
        """Persist the data to the storage."""
        if self._data_store is not None:
            self._data_store.save(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Returns the dictionary representation for storage."""
        return {
            "name": self._name,
            "first_day": self._first_day,
            "last_day": self._last_day,
            "venues": self._venues,
            "artists": self._artists,
            "performances": self._performances,
        }

    def is_in_range(self, date: date) -> bool:
        """Returns True if the date is within the festival range."""
        return self._first_day <= date <= self._last_day

    def get_festival_days(self) -> tuple[date, ...]:
        """Returns the festival days."""
        return self._days

    def get_festival_info(self) -> FestivalInfo:
        """Returns a summary of the festival information."""
        return FestivalInfo(
            name=self._name,
            first_day=self._first_day,
            last_day=self._last_day,
            days=self._days,
            venue_count=len(self._venues),
            artist_count=len(self._artists),
            performance_count=len(self._performances),
        )

    def add_artist(self, artist: Artist) -> Artist:
        if self.artist_exists(artist.slug):
            raise errors.ConflictError(f"Artist '{artist.slug}' already exists.")
        self._artists.append(artist)
        self.save()
        return artist

    def add_performance(self, performance: Performance) -> Performance:
        """Adds a performance to the festival after validating all business rules."""
        self._validate_performance(performance)
        self._performances.append(performance)
        self.save()
        return performance

    def update_performance(
        self, performance_id: str, performance: Performance
    ) -> Performance:
        index = next(
            (i for i, p in enumerate(self._performances) if p.id == performance_id),
            None,
        )

        if index is None:
            raise errors.NotFoundError(f"Performance '{performance_id}' not found.")

        self._validate_performance(performance, performance_id)

        # Replace if passed
        self._performances[index] = performance
        self.save()
        return performance

    def delete_performance(self, performance_id: str) -> str:
        performance = self.get_performance_by_id(performance_id)
        if performance is None:
            raise errors.NotFoundError(f"Performance '{performance_id}' not found.")

        self._performances.remove(performance)
        self.save()
        return performance.title

    def register_participant(self, performance_id: str, participant_slug: str) -> str:
        performance = self.get_performance_by_id(performance_id)
        if performance is None:
            raise errors.NotFoundError(f"Performance '{performance_id}' not found.")
        if not isinstance(performance, WorkshopPerformance):
            raise errors.ConflictError(
                f"Performance '{performance.id}' is not a workshop."
            )
        performance.add_participant(participant_slug)
        self.save()
        return performance.title

    def performance_exists(self, performance_id: str) -> bool:
        return any(p.id == performance_id for p in self._performances)

    def get_performance_by_id(self, performance_id: str) -> Performance | None:
        return next((p for p in self._performances if p.id == performance_id), None)

    def get_performance_details(self, performance: Performance) -> dict[str, Any]:
        venue = self.get_venue_by_slug(performance.venue)
        if venue is None:
            raise ValueError(f"Venue {performance.venue} not found")

        venue_name = venue.name
        venue_capacity = venue.capacity

        artist_map = self.get_artist_slug_to_name_map()

        data: dict[str, Any] = {
            "id": performance.id,
            "kind": performance.kind,
            "title": performance.title,
            "venue": performance.venue,
            "venue_name": venue_name,
            "start": performance.start,
            "end": performance.end,
            "duration_minutes": performance.duration_minutes,
            "festival_day": performance.get_festival_day(),
            "description": performance.description,
            "artists": [
                {"slug": a, "name": artist_map[a]}
                for a in performance.get_all_artists()
            ],
        }

        if isinstance(performance, SoloPerformance):
            artist_name = artist_map[performance.artist]
            data.update(
                {
                    "summary": f"by {artist_name}",
                    "capacity": venue_capacity,
                    "artist": performance.artist,
                    "min_age": performance.min_age,
                }
            )
        elif isinstance(performance, LineupPerformance):
            host_name = artist_map[performance.host]
            acts_names = [artist_map[act] for act in performance.acts]
            data.update(
                {
                    "summary": f"hosted by {host_name}, with {', '.join(acts_names)}",
                    "capacity": venue_capacity,
                    "host": performance.host,
                    "acts": performance.acts,
                }
            )
        elif isinstance(performance, WorkshopPerformance):
            capacity = min(performance.max_participants, venue_capacity)
            data.update(
                {
                    "summary": f"with {artist_map[performance.teacher]}, "
                    f"{len(performance.participants)} / {capacity} places taken",
                    "capacity": capacity,
                    "teacher": performance.teacher,
                    "max_participants": performance.max_participants,
                    "participants": performance.participants,
                    "places_left": max(0, capacity - len(performance.participants)),
                }
            )

        return data

    def get_performance_lineup(
        self, moment: datetime
    ) -> tuple[tuple[Performance, ...], tuple[Performance, ...]]:
        """Returns (now_playing, up_next) at a given moment."""
        now_playing = sorted([p for p in self._performances if p.is_on(moment)])
        upcoming = sorted([p for p in self._performances if p.start > moment])
        up_next = upcoming[:3]

        return tuple(now_playing), tuple(up_next)

    def list_performances(
        self,
        day: date | None = None,
        venue_slug: str | None = None,
        artist_slug: str | None = None,
    ) -> tuple[Performance, ...]:
        filtered = self._get_filtered_performances(day, venue_slug, artist_slug)
        return tuple(sorted(filtered))

    def artist_exists(self, artist_slug: str) -> bool:
        return any(a.slug == artist_slug for a in self._artists)

    def get_artist_by_slug(self, artist_slug: str) -> Artist | None:
        return next((a for a in self._artists if a.slug == artist_slug), None)

    def get_artist_with_performances(
        self, artist_slug: str
    ) -> tuple[Artist, tuple[Performance, ...]]:
        artist = self.get_artist_by_slug(artist_slug)
        if artist is None:
            raise errors.NotFoundError(f"Artist '{artist_slug}' not found.")

        performances = self._get_filtered_performances(artist_slug=artist_slug)
        return artist, tuple(sorted(performances, key=lambda p: p.start))

    def list_artists(self) -> tuple[Artist, ...]:
        return tuple(sorted(self._artists, key=lambda a: a.slug))

    def get_venue_by_slug(self, venue_slug: str) -> Venue | None:
        return next((v for v in self._venues if v.slug == venue_slug), None)

    def list_venues(self) -> tuple[Venue, ...]:
        return tuple(self._venues)

    def get_venue_slug_to_name_map(self) -> dict[str, str]:
        return {venue.slug: venue.name for venue in self._venues}

    def get_artist_slug_to_name_map(self) -> dict[str, str]:
        return {artist.slug: artist.name for artist in self._artists}

    def _get_filtered_performances(
        self,
        day: date | None = None,
        venue_slug: str | None = None,
        artist_slug: str | None = None,
    ) -> list[Performance]:
        return [
            p
            for p in self._performances
            if (day is None or p.get_festival_day() == day)
            and (venue_slug is None or p.venue == venue_slug)
            and (artist_slug is None or p.involves_artist(artist_slug))
        ]

    def _validate_performance(
        self, performance: Performance, exclude_id: str | None = None
    ) -> None:
        """Validates all business rules for a performance against existing festival state."""
        venue = self._validate_venue(performance)
        self._validate_artists(performance)
        self._validate_festival_day(performance)
        self._validate_performance_id(performance, exclude_id)
        self._validate_venue_conflict(performance, venue, exclude_id)
        self._validate_artist_conflict(performance, exclude_id)

    def _validate_venue(self, performance: Performance) -> Venue:
        venue = self.get_venue_by_slug(performance.venue)
        if venue is None:
            raise errors.NotFoundError(f"Venue '{performance.venue}' not found.")

        if isinstance(performance, WorkshopPerformance):
            performance.max_participants = min(
                performance.max_participants,
                venue.capacity,
            )
        return venue

    def _validate_artists(self, performance: Performance) -> None:
        for artist in performance.get_all_artists():
            if not self.artist_exists(artist):
                raise errors.NotFoundError(f"Artist '{artist}' not found.")

    def _validate_festival_day(self, performance: Performance) -> None:
        festival_day = performance.get_festival_day()
        if not self.is_in_range(festival_day):
            raise errors.ConflictError(
                f"Performance date {festival_day} is outside the "
                f"festival ({self._first_day} to {self._last_day})."
            )

    def _validate_performance_id(
        self, performance: Performance, exclude_id: str | None
    ) -> None:
        for existing in self._performances:
            if existing.id == exclude_id:
                continue
            if existing.id == performance.id:
                raise errors.ConflictError(
                    f"A performance with id '{performance.id}' already exists."
                )

    def _validate_venue_conflict(
        self, performance: Performance, venue: Venue, exclude_id: str | None
    ) -> None:
        buffer = timedelta(minutes=30)
        for existing in self._performances:
            if existing.id == exclude_id:
                continue
            if existing.venue == performance.venue and not (
                performance.end + buffer <= existing.start
                or existing.end + buffer <= performance.start
            ):
                raise errors.ConflictError(
                    f"{venue.name} is busy with {existing.title} "
                    f"({existing.start:%Y-%m-%d %H:%M}-{existing.end:%H:%M}). "
                    "Leave 30 minutes between two shows."
                )

    def _validate_artist_conflict(
        self, performance: Performance, exclude_id: str | None
    ) -> None:
        buffer = timedelta(minutes=30)
        perf_artists = set(performance.get_all_artists())
        for existing in self._performances:
            if existing.id == exclude_id:
                continue
            common_artists = perf_artists & set(existing.get_all_artists())
            if common_artists and not (
                performance.end + buffer <= existing.start
                or existing.end + buffer <= performance.start
            ):
                artist_name_map = self.get_artist_slug_to_name_map()
                names = ", ".join(artist_name_map.get(a, a) for a in common_artists)
                raise errors.ConflictError(
                    f"{names} is busy with {existing.title} "
                    f"({existing.start:%Y-%m-%d %H:%M}-{existing.end:%H:%M}). "
                    "Leave 30 minutes between two shows."
                )
