from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from deauville_festival.api.dependencies import FestivalManageDep
from deauville_festival.api.schemas import (
    AddArtistRequest,
    ArtistDetailResponse,
    ArtistSummaryResponse,
    FestivalResponse,
    NowResponse,
    PerformanceRequest,
    PerformanceResponse,
    RegisterParticipantRequest,
    RegisterParticipantResponse,
    RequiredStr,
    SlugStr,
    VenueResponse,
    performance_response_type_adapter,
)
from deauville_festival.models import PERFORMANCE_REGISTRY, Artist

public_router = APIRouter(prefix="/api", tags=["Public (Read-only)"])


@public_router.get("/festival", operation_id="GetFestivalInfo")
def festival(manager: FestivalManageDep) -> FestivalResponse:
    """Returns basic information about the festival."""
    return FestivalResponse.model_validate(
        manager.get_festival_info(), from_attributes=True
    )


@public_router.get("/venues", operation_id="ListVenues")
def list_venues(manager: FestivalManageDep) -> list[VenueResponse]:
    """Returns a list of all venues."""
    return [
        VenueResponse.model_validate(venue, from_attributes=True)
        for venue in manager.list_venues()
    ]


@public_router.get("/artists", operation_id="ListArtists")
def list_artists(manager: FestivalManageDep) -> list[ArtistSummaryResponse]:
    """Returns a list of all artists."""
    return [
        ArtistSummaryResponse.model_validate(artist, from_attributes=True)
        for artist in manager.list_artists()
    ]


@public_router.get(
    "/artists/{artist_slug}",
    operation_id="GetArtist",
    responses={404: {"description": "Artist not found."}},
)
def get_artist(
    artist_slug: Annotated[RequiredStr, Path()], manager: FestivalManageDep
) -> ArtistDetailResponse:
    """Returns an artist and their performances."""
    artist, performances = manager.get_artist_with_performances(artist_slug)
    performance_details = [
        performance_response_type_adapter.validate_python(
            manager.get_performance_details(p)
        )
        for p in performances
    ]

    return ArtistDetailResponse(
        slug=artist.slug,
        name=artist.name,
        bio=artist.bio,
        photo_url=artist.photo_url,
        performances=performance_details,
    )


@public_router.get("/programme", operation_id="GetProgramme")
def get_programme(
    manager: FestivalManageDep,
    day: Annotated[date | None, Query(description="Filter by festival day.")] = None,
    venue: Annotated[SlugStr | None, Query(description="Filter by venue slug.")] = None,
) -> list[PerformanceResponse]:
    """Returns the festival programme."""
    return [
        performance_response_type_adapter.validate_python(
            manager.get_performance_details(p)
        )
        for p in manager.list_performances(day, venue)
    ]


@public_router.get(
    "/performances/{performance_id}",
    operation_id="GetPerformance",
    responses={404: {"description": "Performance not found."}},
)
def get_performance(
    performance_id: Annotated[RequiredStr, Path()], manager: FestivalManageDep
) -> PerformanceResponse:
    """Returns a performance by its identifier."""
    performance = manager.get_performance_by_id(performance_id)
    return performance_response_type_adapter.validate_python(
        manager.get_performance_details(performance)
    )


@public_router.get("/now", operation_id="OnNow")
def on_now(
    manager: FestivalManageDep,
    at: Annotated[datetime | None, Query(description="Moment in time.")] = None,
) -> NowResponse:
    """Returns the performances that are currently happening along with the performances (3 at most)."""
    moment = at or datetime.now()
    now_playing, up_next = manager.get_performance_lineup(moment)

    return NowResponse(
        at=moment,
        now_playing=[
            performance_response_type_adapter.validate_python(
                manager.get_performance_details(p)
            )
            for p in now_playing
        ],
        up_next=[
            performance_response_type_adapter.validate_python(
                manager.get_performance_details(p)
            )
            for p in up_next
        ],
    )


admin_router = APIRouter(prefix="/api", tags=["Admin (Write)"])


@admin_router.post(
    "/artists",
    operation_id="AddArtist",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Artist already exists."},
        422: {"description": "Invalid request."},
    },
)
def add_artist(
    request: AddArtistRequest, manager: FestivalManageDep
) -> ArtistSummaryResponse:
    """Adds a new artist to the festival."""
    artist = Artist(**request.model_dump())
    artist = manager.add_artist(artist)
    return ArtistSummaryResponse.model_validate(artist, from_attributes=True)


@admin_router.post(
    "/performances",
    operation_id="AddPerformance",
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Artist(s) or venue not found."},
        409: {"description": "Venue or artist(s) busy, date out of range."},
        422: {"description": "Invalid request."},
    },
)
def add_performance(
    request: PerformanceRequest, manager: FestivalManageDep
) -> PerformanceResponse:
    """Adds a new performance to the festival."""
    performance_data = request.model_dump(exclude={"kind"})

    performance_class = PERFORMANCE_REGISTRY[request.kind]
    performance = performance_class(**performance_data)

    performance = manager.add_performance(performance)

    return performance_response_type_adapter.validate_python(
        manager.get_performance_details(performance)
    )


@admin_router.put(
    "/performances/{performance_id}",
    operation_id="UpdatePerformance",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Performance, artist(s) or venue not found."},
        409: {"description": "Venue or artist(s) busy, date out of range."},
        422: {"description": "Invalid request."},
    },
)
def update_performance(
    performance_id: Annotated[RequiredStr, Path()],
    request: PerformanceRequest,
    manager: FestivalManageDep,
) -> PerformanceResponse:
    """Updates an existing performance by its identifier."""
    performance_data = request.model_dump(exclude={"kind"})

    performance_class = PERFORMANCE_REGISTRY[request.kind]
    performance = performance_class(**performance_data)

    performance = manager.update_performance(performance_id, performance)

    return performance_response_type_adapter.validate_python(
        manager.get_performance_details(performance)
    )


@admin_router.delete(
    "/performances/{performance_id}",
    operation_id="DeletePerformance",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Performance not found."}},
)
def delete_performance(
    performance_id: Annotated[RequiredStr, Path()], manager: FestivalManageDep
) -> None:
    """Deletes a performance by its identifier."""
    manager.delete_performance(performance_id)


@admin_router.post(
    "/performances/{performance_id}/participants",
    operation_id="RegisterParticipant",
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Performance not found."},
        409: {"description": "Participant already registered or workshop is full."},
        422: {"description": "Invalid request or performance is not a workshop."},
    },
)
def register_participant(
    performance_id: Annotated[RequiredStr, Path()],
    request: RegisterParticipantRequest,
    manager: FestivalManageDep,
) -> RegisterParticipantResponse:
    """Adds a participant to a workshop."""
    workshop = manager.register_participant(performance_id, request.name)
    return RegisterParticipantResponse(
        title=workshop.title, places_left=workshop.places_left
    )
