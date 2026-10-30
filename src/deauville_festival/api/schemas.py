from collections import Counter
from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    StringConstraints,
    field_serializer,
    model_validator,
)

from deauville_festival import helpers
from deauville_festival.models import PerformanceKind


class FestivalResponse(BaseModel):
    """Represents basic information about the festival."""

    name: str = Field(description="The name of the festival.")
    first_day: date = Field(description="The first day of the festival.")
    last_day: date = Field(description="The last day of the festival.")
    days: list[date] = Field(description="All the dates of the festival.")


class VenueResponse(BaseModel):
    """Represents a venue."""

    slug: str = Field(description="A URL-friendly version of the venue name.")
    name: str = Field(description="The display name of the venue.")
    capacity: int = Field(description="The maximum seating capacity of the venue.")
    address: str = Field(description="The location of the venue.")


class ArtistOut(BaseModel):
    """Represents the basic information about an artist."""

    slug: str = Field(description="A URL-friendly version of the artist's name.")
    name: str = Field(description="The name of the artist.")
    photo_url: str = Field(default="", description="The URL of the artist's photo.")


class ArtistSummaryResponse(ArtistOut):
    """Represents a summary of an artist."""


class ArtistDetailResponse(ArtistOut):
    """Represents an artist."""

    bio: str = Field(default="", description="A short biography of the artist.")
    performances: list["PerformanceResponse"] = Field(
        description="The performances featuring this artist."
    )


class PerformanceResponse(BaseModel):
    """Represents detailed information about a performance."""

    id: str = Field(description="The unique identifier of the performance.")
    kind: PerformanceKind = Field(
        description="The type of performance ('solo', 'lineup', or 'workshop')."
    )
    title: str = Field(description="The title of the performance.")
    venue: str = Field(description="The slug of the venue hosting the performance.")
    venue_name: str = Field(
        description="The name of the venue hosting the performance."
    )
    start: datetime = Field(description="The start date and time of the performance.")
    end: datetime = Field(description="The end date and time of the performance.")
    duration_minutes: int = Field(
        description="The duration of the performance in minutes."
    )
    festival_day: date = Field(
        description="The festival day the performance belongs to."
    )
    description: str = Field(
        default="", description="A description of the performance."
    )
    summary: str = Field(default="", description="A short summary of the performance.")
    capacity: int = Field(ge=1, description="The capacity of the performance.")
    artists: list["ArtistInfo"] = Field(
        description="The list of artists involved in the performance."
    )
    artist: str | None = Field(
        default=None, description="The artist's slug (for solo performances)."
    )
    min_age: int | None = Field(
        default=None, description="Minimum age requirement (for solo performances)."
    )
    host: str | None = Field(
        default=None, description="The host's artist slug (for lineup performances)."
    )
    acts: list[str] | None = Field(
        default=None,
        description="The list of act artist slugs (for lineup performances).",
    )
    teacher: str | None = Field(
        default=None,
        description="The teacher's artist slug (for workshop performances).",
    )
    max_participants: int | None = Field(
        default=None,
        description="Maximum number of participants (for workshop performances).",
    )
    participants: list[str] | None = Field(
        default=None,
        description="List of registered participant names (for workshop performances).",
    )
    places_left: int | None = Field(
        default=None,
        description="Number of remaining places available (for workshop performances).",
    )

    @field_serializer("start", "end")
    def serialize_datetime(self, dt: datetime) -> str:
        """Serializes a datetime object to a string in the format YYYY-MM-DDTHH:MM."""
        return helpers.datetime_to_str(dt)

    class ArtistInfo(BaseModel):
        """Represents an artist involved in a performance."""

        slug: str = Field(description="The URL-friendly slug of the artist.")
        name: str = Field(description="The name of the artist.")


class NowResponse(BaseModel):
    """Represents what is on stage now and up next."""

    at: datetime = Field(description="The current show time.")
    now_playing: list[PerformanceResponse] = Field(
        description="The performances happening now."
    )
    up_next: list[PerformanceResponse] = Field(
        description="The next 3 upcoming performances."
    )

    @field_serializer("at")
    def serialize_at(self, dt: datetime) -> str:
        """Serializes a datetime object to a string in the format YYYY-MM-DDTHH:MM."""
        return helpers.datetime_to_str(dt)


RequiredStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
"""A string that is required (non-empty)."""

SlugStr = Annotated[RequiredStr, AfterValidator(helpers.get_slug)]
"""A required string that is normalized to a slug."""


class AddArtistRequest(BaseModel):
    """Represents an artist input."""

    name: RequiredStr = Field(max_length=64, description="The name of the artist")
    bio: str = Field(
        default="", max_length=255, description="A short biography of the artist."
    )
    photo_url: str = Field(
        default="", max_length=200, description="The URL of the artist's photo."
    )


class PerformanceIn(BaseModel, extra="forbid"):
    """Represents a performance input."""

    title: RequiredStr = Field(
        max_length=100, description="The title of the performance."
    )
    venue: SlugStr = Field(max_length=64, description="The venue slug.")
    start: datetime = Field(description="The start time of the performance.")
    duration_minutes: int = Field(
        ge=1, le=360, description="Duration in minutes (1-360)."
    )
    description: str = Field(
        default="", max_length=1024, description="A description of the performance."
    )


class SoloPerformanceRequest(PerformanceIn):
    """Represents a solo performance input."""

    kind: Literal["solo"] = Field(description="The performance kind ('solo').")
    artist: SlugStr = Field(
        max_length=64, description="The artist slug, if solo performance."
    )
    min_age: int = Field(
        default=0, ge=0, le=18, description="Minimum age requirement (0-18)."
    )


class LineupPerformanceRequest(PerformanceIn):
    """Represents a lineup performance input."""

    kind: Literal["lineup"] = Field(description="The performance kind ('lineup').")
    host: SlugStr = Field(
        max_length=64,
        description="The slug of the host (artsit) of the lineup, if lineup performance.",
    )
    acts: list[SlugStr] = Field(
        default_factory=list,
        description="List of acts' slugs if lineup performance (minimum 2).",
    )

    @model_validator(mode="after")
    def validate_lineup_kind(self) -> Self:
        no_acts = len(self.acts)
        if no_acts < 2:
            raise ValueError("Lineup performances must have at least two acts.")
        if max(Counter(self.acts).values()) > 1:
            raise ValueError("Lineup performances cannot have duplicate acts.")
        if self.host in self.acts:
            raise ValueError("The host cannot be one of the acts in a lineup.")

        # 10 minutes per act + 3 minutes between acts
        min_duration = (no_acts * 10) + ((no_acts - 1) * 3)
        if self.duration_minutes < min_duration:
            raise ValueError(
                f"Lineup performances must be at least {min_duration} minutes long "
                f"for {no_acts} acts. 10 minutes per act, plus 3 minutes between acts."
            )

        return self


class WorkshopPerformanceRequest(PerformanceIn):
    """Represents a workshop performance input."""

    kind: Literal["workshop"] = Field(description="The performance kind ('workshop').")
    teacher: SlugStr = Field(
        description="The teacher (artist) slug if workshop performance."
    )
    max_participants: int = Field(
        ge=1,
        description="Maximum number of participants for a workshop, if applicable.",
    )
    participants: list[RequiredStr] = Field(
        default_factory=list, description="List of the names of the participants."
    )

    @model_validator(mode="after")
    def validate_workshop_kind(self) -> Self:
        if len(self.participants) > self.max_participants:
            raise ValueError(
                "The number of participants cannot exceed the maximum number of participants."
            )
        names_upper = Counter([name.upper() for name in self.participants])
        if any(v > 1 for _, v in names_upper.items()):
            raise ValueError("Cannot have duplicate participants.")

        return self


PerformanceRequest = Annotated[
    SoloPerformanceRequest | LineupPerformanceRequest | WorkshopPerformanceRequest,
    Field(discriminator="kind"),
]


class PerformanceInResponse(BaseModel):
    """Response model for a performance that has be added or modified."""

    kind: PerformanceKind = Field(
        description="The type of performance ('solo', 'lineup', or 'workshop')."
    )
    title: str = Field(description="The title of the performance.")
    venue: str = Field(description="The slug of the venue hosting the performance.")
    start: datetime = Field(description="The start date and time of the performance.")
    duration_minutes: int = Field(
        description="The duration of the performance in minutes."
    )
    artist: str | None = Field(
        default=None, description="The artist's slug (for solo performances)."
    )
    min_age: int | None = Field(
        default=None, description="Minimum age requirement (for solo performances)."
    )
    host: str | None = Field(
        default=None, description="The host's artist slug (for lineup performances)."
    )
    acts: list[str] | None = Field(
        default=None,
        description="The list of act artist slugs (for lineup performances).",
    )
    teacher: str | None = Field(
        default=None,
        description="The teacher's artist slug (for workshop performances).",
    )
    max_participants: int | None = Field(
        default=None,
        description="Maximum number of participants (for workshop performances).",
    )
    participants: list[str] | None = Field(
        default=None,
        description="List of registered participant names (for workshop performances).",
    )

    @field_serializer("start")
    def serialize_datetime(self, dt: datetime) -> str:
        """Serializes a datetime object to a string in the format YYYY-MM-DDTHH:MM."""
        return helpers.datetime_to_str(dt)


class RegisterParticipantRequest(BaseModel):
    name: RequiredStr = Field(max_length=100, description="The name of the participant")
