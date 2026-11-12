import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    PlainSerializer,
    StringConstraints,
    TypeAdapter,
)

from deauville_festival import helpers
from deauville_festival.models import (
    Artist,
    LineupPerformance,
    Performance,
    PerformanceKind,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)


class FestivalResponse(BaseModel):
    """Represents the basic information about the festival."""

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
    bio: str = Field(default="", description="A short biography of the artist.")
    photo_url: str = Field(default="", description="The URL of the artist's photo.")


class ArtistSummaryResponse(ArtistOut):
    """Represents a summary of an artist."""


class ArtistDetailResponse(ArtistOut):
    """Represents an artist."""

    performances: list["PerformanceResponse"] = Field(
        description="The performances featuring this artist."
    )


DateTimeStr = Annotated[datetime, PlainSerializer(helpers.datetime_to_str)]


class PerformanceOut(BaseModel):
    """Represents a performance."""

    id: str = Field(description="The unique identifier of the performance.")
    kind: PerformanceKind = Field(
        description="The type of performance ('solo', 'lineup', or 'workshop')."
    )
    title: str = Field(description="The title of the performance.")
    venue: str = Field(description="The slug of the venue hosting the performance.")
    venue_name: str = Field(
        description="The name of the venue hosting the performance."
    )
    start: DateTimeStr = Field(
        description="The start date and time of the performance."
    )
    end: DateTimeStr = Field(description="The end date and time of the performance.")
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

    class ArtistInfo(BaseModel):
        """Represents an artist involved in a performance."""

        slug: str = Field(description="The URL-friendly slug of the artist.")
        name: str = Field(description="The name of the artist.")


class SoloPerformanceResponse(PerformanceOut):
    """Represents a solo performance."""

    kind: Literal["solo"]  # pyright: ignore[reportIncompatibleVariableOverride]
    artist: str = Field(description="The artist's slug.")
    min_age: int = Field(description="Minimum age requirement.")


class LineupPerformanceResponse(PerformanceOut):
    """Represents a lineup performance."""

    kind: Literal["lineup"]  # pyright: ignore[reportIncompatibleVariableOverride]
    host: str = Field(description="The host's artist slug.")
    acts: list[str] = Field(description="The list of act artist slugs.")


class WorkshopPerformanceResponse(PerformanceOut):
    """Represents a workshop performance."""

    kind: Literal["workshop"]  # pyright: ignore[reportIncompatibleVariableOverride]
    teacher: str = Field(description="The teacher's artist slug.")
    max_participants: int = Field(description="Maximum number of participants.")
    participants: list[str] = Field(description="List of registered participant names.")
    places_left: int = Field(description="Number of remaining places available.")


PerformanceResponse = Annotated[
    SoloPerformanceResponse | LineupPerformanceResponse | WorkshopPerformanceResponse,
    Field(discriminator="kind"),
]

performance_response_type_adapter = TypeAdapter(PerformanceResponse)


class NowResponse(BaseModel):
    """Represents what is on stage now and up next."""

    at: DateTimeStr = Field(description="The current show time.")
    now_playing: list[PerformanceResponse] = Field(
        description="The performances happening now."
    )
    up_next: list[PerformanceResponse] = Field(
        description="The next 3 upcoming performances."
    )


RequiredStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
"""A string that is required (non-empty)."""

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(value: str) -> str:
    """Validates the slug format (alphanumeric characters and hyphens) and returns it if valid.

    Returns:
        The slug of the given name.

    Raises:
        InvalidError: If the slug format is invalid.
    """
    if not SLUG_PATTERN.match(value):
        raise ValueError("Value must be a valid url slug.")

    return value


SlugStr = Annotated[RequiredStr, AfterValidator(validate_slug)]
"""A required string that is normalized to a slug."""


class AddArtistRequest(BaseModel):
    """Represents an artist input."""

    name: RequiredStr = Field(
        max_length=Artist.NAME_MAX_LEN, description="The name of the artist"
    )
    bio: str = Field(
        default="",
        max_length=Artist.BIO_MAX_LEN,
        description="A short biography of the artist.",
    )
    photo_url: str = Field(
        default="",
        max_length=Artist.PHOTO_URL_MAX_LEN,
        description="The URL of the artist's photo.",
    )


class PerformanceIn(BaseModel, extra="forbid"):
    """Represents a performance input."""

    title: RequiredStr = Field(
        max_length=Performance.TITLE_MAX_LEN,
        description="The title of the performance.",
    )
    venue: SlugStr = Field(max_length=Venue.NAME_MAX_LEN, description="The venue slug.")
    start: datetime = Field(description="The start time of the performance.")
    duration_minutes: int = Field(
        ge=Performance.DURATION_MINUTES_MIN_VALUE,
        le=Performance.DURATION_MINUTES_MAX_VALUE,
        description="Duration in minutes.",
    )
    description: str = Field(
        default="",
        max_length=Performance.DESCRIPTION_MAX_LEN,
        description="A description of the performance.",
    )


class SoloPerformanceRequest(PerformanceIn):
    """Represents a solo performance input."""

    kind: Literal["solo"] = Field(description="The performance kind ('solo').")
    artist: SlugStr = Field(
        max_length=Artist.NAME_MAX_LEN,
        description="The artist slug, if solo performance.",
    )
    min_age: int = Field(
        default=SoloPerformance.MIN_AGE_LOWER,
        ge=SoloPerformance.MIN_AGE_LOWER,
        le=SoloPerformance.MIN_AGE_UPPER,
        description="Minimum age requirement.",
    )


class LineupPerformanceRequest(PerformanceIn):
    """Represents a lineup performance input."""

    kind: Literal["lineup"] = Field(description="The performance kind ('lineup').")
    host: SlugStr = Field(
        max_length=Artist.NAME_MAX_LEN,
        description="The slug of the host (artist) of the lineup, if lineup performance.",
    )
    acts: list[SlugStr] = Field(
        min_length=LineupPerformance.ACTS_MIN_LEN,
        description="List of acts' slugs if lineup performance",
    )


class WorkshopPerformanceRequest(PerformanceIn):
    """Represents a workshop performance input."""

    kind: Literal["workshop"] = Field(description="The performance kind ('workshop').")
    teacher: SlugStr = Field(
        max_length=Artist.NAME_MAX_LEN,
        description="The teacher (artist) slug if workshop performance.",
    )
    max_participants: int = Field(
        ge=WorkshopPerformance.MAX_PARTICIPANTS_MIN_VALUE,
        description="Maximum number of participants for a workshop, if applicable.",
    )
    participants: list[RequiredStr] = Field(
        default_factory=list, description="List of the names of the participants."
    )


PerformanceRequest = Annotated[
    SoloPerformanceRequest | LineupPerformanceRequest | WorkshopPerformanceRequest,
    Field(discriminator="kind"),
]


class RegisterParticipantRequest(BaseModel):
    """Request model for registering a participant to a workshop."""

    name: RequiredStr = Field(max_length=100, description="The name of the participant")


class RegisterParticipantResponse(BaseModel):
    """Response model for when a participant is registered to a workshop."""

    title: str = Field(description="The title of the performance.")
    places_left: int = Field(description="The number of places left in the workshop.")
