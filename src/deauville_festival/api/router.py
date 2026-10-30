from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from deauville_festival.api.dependencies import FestivalManageDep
from deauville_festival.api.schemas import (
    AddArtistRequest,
    ArtistDetailResponse,
    ArtistSummaryResponse,
    FestivalResponse,
    NowResponse,
    PerformanceInResponse,
    PerformanceRequest,
    PerformanceResponse,
    RegisterParticipantRequest,
    RequiredStr,
    VenueResponse,
)
from deauville_festival.models import (
    Artist,
    LineupPerformance,
    SoloPerformance,
    WorkshopPerformance,
)

router = APIRouter()


@router.get("/api/festival", operation_id="GetFestivalInfo")
def festival(manager: FestivalManageDep) -> FestivalResponse:
    """Returns basic information about the festival."""
    return FestivalResponse.model_validate(
        manager.get_festival_info(), from_attributes=True
    )


@router.get("/api/venues", operation_id="ListVenues")
def list_venues(manager: FestivalManageDep) -> list[VenueResponse]:
    """Returns a list of all venues."""
    return [
        VenueResponse.model_validate(venue, from_attributes=True)
        for venue in manager.list_venues()
    ]


@router.get("/api/artists", operation_id="ListArtists")
def list_artists(manager: FestivalManageDep) -> list[ArtistSummaryResponse]:
    """Returns a list of all artists."""
    return [
        ArtistSummaryResponse.model_validate(artist, from_attributes=True)
        for artist in manager.list_artists()
    ]


@router.get(
    "/api/artists/{artist_slug}",
    operation_id="GetArtist",
    response_model=ArtistDetailResponse,
    responses={404: {"description": "Artist not found."}},
)
def get_artist(artist_slug: RequiredStr, manager: FestivalManageDep) -> Any:
    """Returns an artist and their performances."""
    artist, performances = manager.get_artist_with_performances(artist_slug)
    performance_details = [
        PerformanceResponse.model_validate(manager.get_performance_details(p))
        for p in performances
    ]

    return ArtistDetailResponse(
        slug=artist.slug,
        name=artist.name,
        bio=artist.bio,
        photo_url=artist.photo_url,
        performances=performance_details,
    )


@router.get("/api/programme", operation_id="GetProgramme")
def get_programme(
    manager: FestivalManageDep,
    day: date | None = None,
    venue: str | None = None,
) -> list[PerformanceResponse]:
    """Returns the festival programme."""
    return [
        PerformanceResponse.model_validate(manager.get_performance_details(p))
        for p in manager.list_performances(day, venue)
    ]


@router.get(
    "/api/performances/{performance_id}",
    operation_id="GetPerformance",
    response_model=PerformanceResponse,
    responses={404: {"description": "Performance not found."}},
)
def get_performance(performance_id: str, manager: FestivalManageDep) -> Any:
    """Returns a performance by its ID."""
    performance = manager.get_performance_by_id(performance_id.strip())
    if performance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Performance not found."
        )

    return PerformanceResponse.model_validate(
        manager.get_performance_details(performance)
    )


@router.get("/api/now", operation_id="OnNow")
def on_now(manager: FestivalManageDep, at: datetime | None = None) -> NowResponse:
    """Returns the performances that are currently happening."""
    moment = at or datetime.now()
    now_playing, up_next = manager.get_performance_lineup(moment)

    return NowResponse(
        at=moment,
        now_playing=tuple(manager.get_performance_details(p) for p in now_playing),
        up_next=tuple(manager.get_performance_details(p) for p in up_next),
    )


@router.post(
    "/api/artists",
    operation_id="AddArtist",
    status_code=status.HTTP_201_CREATED,
    response_model=ArtistSummaryResponse,
    tags=["Admin"],
)
def add_artist(request: AddArtistRequest, manager: FestivalManageDep) -> Any:
    artist = Artist(**request.model_dump())
    artist = manager.add_artist(artist)
    return ArtistSummaryResponse.model_validate(artist, from_attributes=True)


@router.post(
    "/api/performances",
    operation_id="AddPerformance",
    status_code=status.HTTP_201_CREATED,
    response_model=PerformanceInResponse,
    tags=["Admin"],
    responses={
        404: {"description": "Artist or venue not found."},
        409: {"description": "Conflict (venue or artist busy, date out of range)."},
        422: {"description": "Invalid performance details."},
    },
)
def add_performance(request: PerformanceRequest, manager: FestivalManageDep) -> Any:
    """Adds a new performance to the festival."""
    match request.kind:
        case "solo":
            performance = SoloPerformance(**request.model_dump())
        case "lineup":
            performance = LineupPerformance(**request.model_dump())
        case "workshop":
            performance = WorkshopPerformance(**request.model_dump())

    performance = manager.add_performance(performance)
    return PerformanceInResponse.model_validate(performance, from_attributes=True)


@router.put(
    "/api/performances/{performance_id}",
    operation_id="UpdatePerformance",
    status_code=status.HTTP_200_OK,
    response_model=PerformanceInResponse,
    tags=["Admin"],
)
def update_performance(
    performance_id: str, request: PerformanceRequest, manager: FestivalManageDep
) -> Any:
    """Updates an existing performance by its ID."""
    match request.kind:
        case "solo":
            performance = SoloPerformance(**request.model_dump())
        case "lineup":
            performance = LineupPerformance(**request.model_dump())
        case "workshop":
            performance = WorkshopPerformance(**request.model_dump())
    performance = manager.update_performance(performance_id, performance)
    return PerformanceInResponse.model_validate(
        manager.get_performance_details(performance), from_attributes=True
    )


@router.delete(
    "/api/performances/{performance_id}",
    operation_id="DeletePerformance",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_performance(performance_id: str, manager: FestivalManageDep) -> None:
    """Deletes a performance by its ID."""
    manager.delete_performance(performance_id)


@router.post(
    "/api/performances/{performance_id}/participants",
    operation_id="RegisterParticipant",
    status_code=status.HTTP_201_CREATED,
)
def register_participant(
    performance_id: str, request: RegisterParticipantRequest, manager: FestivalManageDep
) -> Any:
    """Removes a participant from a performance."""
    workshop = manager.register_participant(performance_id, request.name)
    return {"workshop": workshop}
