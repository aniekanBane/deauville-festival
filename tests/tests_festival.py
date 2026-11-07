from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from deauville_festival import config, errors, storage
from deauville_festival.festival import FestivalManager
from deauville_festival.models import (
    Artist,
    LineupPerformance,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)

_SOURCE_DATA_PATH = config.DATA_DIR / "festival.json"


@pytest.fixture
def festival_data() -> dict:
    return storage.JSONFileStorage(_SOURCE_DATA_PATH).load()


@pytest.fixture
def manager(festival_data: dict) -> FestivalManager:
    return FestivalManager(**festival_data)


class TestFestivalManagerInit:
    """Tests for FestivalManager initialization."""

    def test_empty_name_raises_value_error(self, festival_data: dict) -> None:
        with pytest.raises(ValueError, match="Name cannot be empty"):
            FestivalManager(
                name="   ",
                first_day=festival_data["first_day"],
                last_day=festival_data["last_day"],
                venues=festival_data["venues"],
                artists=festival_data["artists"],
                performances=festival_data["performances"],
            )

    def test_last_day_before_or_equal_first_day_raises_value_error(
        self, festival_data: dict
    ) -> None:
        with pytest.raises(ValueError, match="Last day must be after first day"):
            FestivalManager(
                name="Festival",
                first_day=date(2027, 6, 12),
                last_day=date(2027, 6, 12),
                venues=festival_data["venues"],
                artists=festival_data["artists"],
                performances=festival_data["performances"],
            )

        with pytest.raises(ValueError, match="Last day must be after first day"):
            FestivalManager(
                name="Festival",
                first_day=date(2027, 6, 15),
                last_day=date(2027, 6, 12),
                venues=festival_data["venues"],
                artists=festival_data["artists"],
                performances=festival_data["performances"],
            )

    def test_get_festival_days(self, manager: FestivalManager) -> None:
        days = manager.get_festival_days()
        assert len(days) == 4
        assert days[0] == date(2027, 6, 10)
        assert days[-1] == date(2027, 6, 13)


class TestFestivalManagerPerformances:
    """Tests for performance details and queries on FestivalManager."""

    def test_performance_exists(self, manager: FestivalManager) -> None:
        assert manager.performance_exists("grand-casino-2027-06-10-2030") is True
        assert manager.performance_exists("nonexistent-performance-id") is False

    def test_get_performance_details_solo(self, manager: FestivalManager) -> None:
        solo = manager.get_performance_by_id("theatre-des-planches-2027-06-10-2100")
        assert solo is not None
        details = manager.get_performance_details(solo)

        assert details["id"] == solo.id
        assert details["kind"] == "solo"
        assert details["title"] == solo.title
        assert details["venue_name"] == "Théâtre des Planches"
        assert "summary" in details
        assert details["summary"].startswith("by ")
        assert details["capacity"] == 320
        assert details["artist"] == "sacha-diallo"
        assert len(details["artists"]) == 1
        assert details["artists"][0]["slug"] == "sacha-diallo"

    def test_get_performance_details_lineup(self, manager: FestivalManager) -> None:
        lineup = manager.get_performance_by_id("grand-casino-2027-06-10-2030")
        assert lineup is not None
        details = manager.get_performance_details(lineup)

        assert details["kind"] == "lineup"
        assert "hosted by" in details["summary"]
        assert details["host"] == "paul-kerbrat"
        assert len(details["acts"]) >= 2
        assert len(details["artists"]) == len(details["acts"]) + 1

    def test_get_performance_details_workshop(self, manager: FestivalManager) -> None:
        workshop = manager.get_performance_by_id("la-cabane-2027-06-11-1030")
        assert workshop is not None
        details = manager.get_performance_details(workshop)

        assert details["kind"] == "workshop"
        assert "places taken" in details["summary"]
        assert details["teacher"] == "ines-moreau"
        assert "places_left" in details
        assert details["max_participants"] == 12
        assert details["places_left"] == 9
        assert len(details["participants"]) == 3

    def test_get_performance_details_unknown_venue_raises_value_error(
        self, manager: FestivalManager
    ) -> None:
        solo = SoloPerformance(
            title="Ghost Venue Show",
            venue="ghost-venue",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="sacha-diallo",
        )
        with pytest.raises(ValueError, match="Venue ghost-venue not found"):
            manager.get_performance_details(solo)


class TestFestivalManagerValidations:
    """Tests for FestivalManager validation rules."""

    def test_get_artist_with_performances_not_found(
        self, manager: FestivalManager
    ) -> None:
        with pytest.raises(errors.NotFoundError, match="Artist 'nonexistent' not found"):
            manager.get_artist_with_performances("nonexistent")

    def test_add_performance_unknown_venue_raises_not_found(
        self, manager: FestivalManager
    ) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="unknown-venue",
            start=datetime(2027, 6, 10, 14, 0),
            duration_minutes=60,
            artist="sacha-diallo",
        )
        with pytest.raises(errors.NotFoundError, match="Venue 'unknown-venue' not found"):
            manager.add_performance(perf)

    def test_add_performance_unknown_artist_raises_not_found(
        self, manager: FestivalManager
    ) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="la-cabane",
            start=datetime(2027, 6, 10, 14, 0),
            duration_minutes=60,
            artist="unknown-artist",
        )
        with pytest.raises(errors.NotFoundError, match="Artist 'unknown-artist' not found"):
            manager.add_performance(perf)

    def test_add_performance_outside_dates_raises_conflict(
        self, manager: FestivalManager
    ) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="la-cabane",
            start=datetime(2027, 6, 1, 14, 0),
            duration_minutes=60,
            artist="sacha-diallo",
        )
        with pytest.raises(errors.ConflictError, match="outside the festival"):
            manager.add_performance(perf)

    def test_add_performance_duplicate_id_raises_conflict(
        self, manager: FestivalManager
    ) -> None:
        existing = manager.get_performance_by_id("theatre-des-planches-2027-06-10-2100")
        assert existing is not None
        perf = SoloPerformance(
            title="Duplicate ID Show",
            venue=existing.venue,
            start=existing.start,
            duration_minutes=60,
            artist="elodie-marchal",
        )
        with pytest.raises(errors.ConflictError, match="already exists"):
            manager.add_performance(perf)
