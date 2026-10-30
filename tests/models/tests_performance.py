from datetime import date, datetime

import pytest

from deauville_festival import errors
from deauville_festival.models import (
    LineupPerformance,
    Performance,
    SoloPerformance,
    WorkshopPerformance,
)


class TestPerformanceBase:
    """Tests for `Performance` abstract base class behavior and common methods."""

    def test_cannot_instantiate_abstract_performance_directly(self) -> None:
        with pytest.raises(TypeError):
            Performance(  # type: ignore[abstract]
                kind="solo",
                title="Abstract Show",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 20, 0),
                duration_minutes=60,
            )

    def test_strips_whitespace_and_sets_default_description(self) -> None:
        perf = SoloPerformance(
            title="  Late Night Laughs \n",
            venue="  le-kiosque\t",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=60,
            artist="  elodie-marchal ",
        )
        assert perf.title == "Late Night Laughs"
        assert perf.venue == "le-kiosque"
        assert perf.description == ""
        assert perf.artist == "elodie-marchal"
        assert perf.kind == "solo"

    def test_strips_whitespace_from_description(self) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=60,
            description="  A hilarious evening. \n",
            artist="elodie-marchal",
        )
        assert perf.description == "A hilarious evening."

    @pytest.mark.parametrize("valid_duration", [1, 60, 180, 360])
    def test_valid_duration_minutes(self, valid_duration: int) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=valid_duration,
            artist="elodie-marchal",
        )
        assert perf.duration_minutes == valid_duration

    @pytest.mark.parametrize("invalid_duration", [-30, 0, 361, 500])
    def test_invalid_duration_minutes_raises_invalid_error(
        self, invalid_duration: int
    ) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            SoloPerformance(
                title="Show",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=invalid_duration,
                artist="elodie-marchal",
            )

        assert str(exc_info.value) == "Duration must be between 1 and 360 minutes."

    def test_id_property(self) -> None:
        perf = SoloPerformance(
            title="After Hours",
            venue="le-kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf.id == "le-kiosque-2027-06-12-0100"

    def test_end_property(self) -> None:
        perf = SoloPerformance(
            title="After Hours",
            venue="le-kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=90,
            artist="elodie-marchal",
        )
        assert perf.end == datetime(2027, 6, 12, 2, 30)

    @pytest.mark.parametrize(
        ("moment", "expected"),
        [
            (datetime(2027, 6, 10, 19, 59), False),
            (datetime(2027, 6, 10, 20, 0), True),
            (datetime(2027, 6, 10, 20, 30), True),
            (datetime(2027, 6, 10, 20, 59), True),
            (datetime(2027, 6, 10, 21, 0), False),
            (datetime(2027, 6, 10, 21, 30), False),
        ],
    )
    def test_is_on(self, moment: datetime, expected: bool) -> None:
        perf = SoloPerformance(
            title="Evening Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf.is_on(moment) is expected

    @pytest.mark.parametrize(
        ("start", "expected_day"),
        [
            (datetime(2027, 6, 11, 20, 0), date(2027, 6, 11)),
            (datetime(2027, 6, 11, 6, 0), date(2027, 6, 11)),
            (datetime(2027, 6, 12, 0, 0), date(2027, 6, 11)),
            (datetime(2027, 6, 12, 0, 30), date(2027, 6, 11)),
            (datetime(2027, 6, 12, 5, 59), date(2027, 6, 11)),
            (datetime(2027, 6, 12, 6, 0), date(2027, 6, 12)),
        ],
    )
    def test_get_festival_day(self, start: datetime, expected_day: date) -> None:
        perf = SoloPerformance(
            title="Night Show",
            venue="le-kiosque",
            start=start,
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf.get_festival_day() == expected_day


class TestPerformanceComparisonAndEquality:
    """Tests for `Performance` sorting (`__lt__`), equality (`__eq__`), and hashing."""

    def test_ordering_by_start_then_venue(self) -> None:
        earlier = SoloPerformance(
            title="Early",
            venue="theatre-des-planches",
            start=datetime(2027, 6, 10, 18, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        later_venue_a = SoloPerformance(
            title="Later A",
            venue="le-casino",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        later_venue_b = SoloPerformance(
            title="Later B",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="hugo-vernier",
        )

        assert earlier < later_venue_a < later_venue_b
        assert sorted([later_venue_b, earlier, later_venue_a]) == [
            earlier,
            later_venue_a,
            later_venue_b,
        ]

    def test_same_type_and_same_id_are_equal(self) -> None:
        perf_a = SoloPerformance(
            title="Show A",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        perf_b = SoloPerformance(
            title="Different Title",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=90,
            artist="hugo-vernier",
        )
        assert perf_a == perf_b
        assert hash(perf_a) == hash(perf_b)
        assert len({perf_a, perf_b}) == 1

    def test_different_ids_are_not_equal(self) -> None:
        perf_a = SoloPerformance(
            title="Show A",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        perf_b = SoloPerformance(
            title="Show A",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf_a != perf_b

    def test_different_performance_subclasses_with_same_id_are_not_equal(self) -> None:
        solo = SoloPerformance(
            title="Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        workshop = WorkshopPerformance(
            title="Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            teacher="elodie-marchal",
            max_participants=20,
        )
        assert solo.id == workshop.id
        assert solo != workshop

    @pytest.mark.parametrize(
        "other",
        [
            "le-kiosque-2027-06-10-2000",
            None,
            42,
            {"id": "le-kiosque-2027-06-10-2000"},
        ],
    )
    def test_not_equal_to_non_performance_object(self, other: object) -> None:
        perf = SoloPerformance(
            title="Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf != other


class TestSoloPerformance:
    """Tests for `SoloPerformance`."""

    @pytest.mark.parametrize("valid_age", [0, 12, 16, 18])
    def test_valid_min_age(self, valid_age: int) -> None:
        perf = SoloPerformance(
            title="Solo Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
            min_age=valid_age,
        )
        assert perf.min_age == valid_age

    @pytest.mark.parametrize("invalid_age", [-5, -1, 19, 21])
    def test_invalid_min_age_raises_invalid_error(self, invalid_age: int) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            SoloPerformance(
                title="Solo Show",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 20, 0),
                duration_minutes=60,
                artist="elodie-marchal",
                min_age=invalid_age,
            )

        assert str(exc_info.value) == "Minimum age must be between 0 and 18."

    def test_get_all_artists_and_involves_artist(self) -> None:
        perf = SoloPerformance(
            title="Solo Show",
            venue="le-kiosque",
            start=datetime(2027, 6, 10, 20, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert perf.get_all_artists() == ("elodie-marchal",)
        assert perf.involves_artist("elodie-marchal") == "artist"
        assert perf.involves_artist("hugo-vernier") is None


class TestLineupPerformance:
    """Tests for `LineupPerformance`."""

    def test_valid_lineup_performance(self) -> None:
        perf = LineupPerformance(
            title="Gala Night",
            venue="theatre-des-planches",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=90,
            host="  elodie-marchal ",
            acts=["hugo-vernier", "camille-roux"],
        )
        assert perf.kind == "lineup"
        assert perf.host == "elodie-marchal"
        assert perf.acts == ["hugo-vernier", "camille-roux"]

    def test_host_in_acts_raises_invalid_error(self) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            LineupPerformance(
                title="Gala Night",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=90,
                host="elodie-marchal",
                acts=["elodie-marchal", "hugo-vernier"],
            )

        assert str(exc_info.value) == "The host cannot be an act."

    def test_duplicate_acts_raise_invalid_error(self) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            LineupPerformance(
                title="Gala Night",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=90,
                host="elodie-marchal",
                acts=["hugo-vernier", "hugo-vernier"],
            )
        assert str(exc_info.value) == "Lineup performances cannot have duplicate acts."

    @pytest.mark.parametrize("acts", [[], ["hugo-vernier"]])
    def test_fewer_than_two_acts_raises_invalid_error(self, acts: list[str]) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            LineupPerformance(
                title="Gala Night",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=90,
                host="elodie-marchal",
                acts=acts,
            )

        assert str(exc_info.value) == "Lineup performances must have at least 2 acts."

    def test_get_all_artists_and_involves_artist(self) -> None:
        perf = LineupPerformance(
            title="Gala Night",
            venue="theatre-des-planches",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=90,
            host="elodie-marchal",
            acts=["hugo-vernier", "camille-roux"],
        )
        assert perf.get_all_artists() == (
            "elodie-marchal",
            "hugo-vernier",
            "camille-roux",
        )
        assert perf.involves_artist("elodie-marchal") == "host"
        assert perf.involves_artist("hugo-vernier") == "act"
        assert perf.involves_artist("camille-roux") == "act"
        assert perf.involves_artist("unknown-artist") is None


class TestWorkshopPerformance:
    """Tests for `WorkshopPerformance`."""

    def test_valid_workshop_creation_and_remaining_capacity(self) -> None:
        perf = WorkshopPerformance(
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="  elodie-marchal ",
            max_participants=15,
        )
        assert perf.kind == "workshop"
        assert perf.teacher == "elodie-marchal"
        assert perf.participants == []
        assert perf.remaining_capacity == 15

    @pytest.mark.parametrize("invalid_max", [-1, 0])
    def test_non_positive_max_participants_raises_invalid_error(
        self, invalid_max: int
    ) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            WorkshopPerformance(
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=invalid_max,
            )

        assert str(exc_info.value) == "Max participants must be positive."

    def test_duplicate_initial_participants_raise_invalid_error(self) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            WorkshopPerformance(
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=3,
                participants=["Camille R.", " camille r. "],
            )
        assert str(exc_info.value) == "Cannot have duplicate participants."

    def test_initial_participants_exceeding_max_raises_invalid_error(self) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            WorkshopPerformance(
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=1,
                participants=["Alice", "Bob"],
            )

        assert str(exc_info.value) == "Cannot have more participants than max capacity."

    def test_add_participant_updates_participants_and_remaining_capacity(self) -> None:
        perf = WorkshopPerformance(
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=2,
        )
        perf.add_participant("Camille R.")
        assert perf.participants == ["Camille R."]
        assert perf.remaining_capacity == 1

        perf.add_participant("Lucas M.")
        assert perf.participants == ["Camille R.", "Lucas M."]
        assert perf.remaining_capacity == 0

    @pytest.mark.parametrize(
        "duplicate_name", ["Camille R.", "camille r.", "CAMILLE R."]
    )
    def test_add_duplicate_participant_case_insensitive_raises_conflict_error(
        self, duplicate_name: str
    ) -> None:
        perf = WorkshopPerformance(
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=5,
            participants=["Camille R."],
        )
        with pytest.raises(errors.ConflictError) as exc_info:
            perf.add_participant(duplicate_name)

        assert str(exc_info.value) == "Participant already registered."

    def test_add_participant_when_full_raises_invalid_error(self) -> None:
        perf = WorkshopPerformance(
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=1,
            participants=["Camille R."],
        )
        with pytest.raises(errors.InvalidError) as exc_info:
            perf.add_participant("Lucas M.")

        assert str(exc_info.value) == "Workshop is full."

    def test_get_all_artists_and_involves_artist(self) -> None:
        perf = WorkshopPerformance(
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=10,
        )
        assert perf.get_all_artists() == ("elodie-marchal",)
        assert perf.involves_artist("elodie-marchal") == "teacher"
        assert perf.involves_artist("hugo-vernier") is None
