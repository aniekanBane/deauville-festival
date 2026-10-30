from datetime import date, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from deauville_festival.api.schemas import (
    LineupPerformanceRequest,
    PerformanceInResponse,
    PerformanceRequest,
    PerformanceResponse,
    SoloPerformanceRequest,
    WorkshopPerformanceRequest,
)


class TestLineupPerformanceRequestValidation:
    """Tests for `LineupPerformanceRequest` and its `@model_validator` logic."""

    @pytest.mark.parametrize(
        ("acts", "min_duration"),
        [
            (["hugo-vernier", "camille-roux"], 23),
            (["hugo-vernier", "camille-roux", "lucas-moreau"], 36),
            (["act-1", "act-2", "act-3", "act-4"], 49),
        ],
    )
    def test_valid_lineup_at_minimum_duration(
        self, acts: list[str], min_duration: int
    ) -> None:
        req = LineupPerformanceRequest(
            kind="lineup",
            title="  Gala Night ",
            venue="Théâtre des Planches",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=min_duration,
            host="Élodie Marchal",
            acts=acts,
        )
        assert req.title == "Gala Night"
        assert req.venue == "theatre-des-planches"
        assert req.host == "elodie-marchal"
        assert req.acts == acts
        assert req.duration_minutes == min_duration

    @pytest.mark.parametrize("acts", [[], ["hugo-vernier"]])
    def test_fewer_than_two_acts_raises_validation_error(self, acts: list[str]) -> None:
        with pytest.raises(ValidationError) as exc_info:
            LineupPerformanceRequest(
                kind="lineup",
                title="Gala Night",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=60,
                host="elodie-marchal",
                acts=acts,
            )

        assert "Lineup performances must have at least two acts." in str(exc_info.value)

    @pytest.mark.parametrize(
        "duplicate_acts",
        [
            ["hugo-vernier", "hugo-vernier"],
            ["Hugo Vernier", "hugo-vernier", "camille-roux"],
        ],
    )
    def test_duplicate_acts_raises_validation_error(
        self, duplicate_acts: list[str]
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            LineupPerformanceRequest(
                kind="lineup",
                title="Gala Night",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=60,
                host="elodie-marchal",
                acts=duplicate_acts,
            )

        assert "Lineup performances cannot have duplicate acts." in str(exc_info.value)

    def test_host_in_acts_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            LineupPerformanceRequest(
                kind="lineup",
                title="Gala Night",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=60,
                host="Élodie Marchal",
                acts=["elodie-marchal", "hugo-vernier"],
            )

        assert "The host cannot be one of the acts in a lineup." in str(exc_info.value)

    @pytest.mark.parametrize(
        ("acts", "too_short_duration", "expected_min"),
        [
            (["hugo-vernier", "camille-roux"], 22, 23),
            (["hugo-vernier", "camille-roux", "lucas-moreau"], 35, 36),
        ],
    )
    def test_duration_shorter_than_required_for_acts_raises_validation_error(
        self, acts: list[str], too_short_duration: int, expected_min: int
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            LineupPerformanceRequest(
                kind="lineup",
                title="Gala Night",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=too_short_duration,
                host="elodie-marchal",
                acts=acts,
            )

        expected_msg = (
            f"Lineup performances must be at least {expected_min} minutes long "
            f"for {len(acts)} acts. 10 minutes per act, plus 3 minutes between acts."
        )
        assert expected_msg in str(exc_info.value)


class TestWorkshopPerformanceRequestValidation:
    """Tests for `WorkshopPerformanceRequest` and its `@model_validator` logic."""

    def test_valid_workshop_with_default_empty_participants(self) -> None:
        req = WorkshopPerformanceRequest(
            kind="workshop",
            title="Improv 101",
            venue="Salon d'Honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="Élodie Marchal",
            max_participants=10,
        )
        assert req.venue == "salon-d-honneur"
        assert req.teacher == "elodie-marchal"
        assert req.participants == []

    def test_valid_workshop_with_participants_up_to_max(self) -> None:
        req = WorkshopPerformanceRequest(
            kind="workshop",
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=2,
            participants=["  Camille R. ", "Lucas M."],
        )
        assert req.participants == ["Camille R.", "Lucas M."]

    def test_participants_exceeding_max_participants_raises_validation_error(
        self,
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            WorkshopPerformanceRequest(
                kind="workshop",
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=2,
                participants=["Camille R.", "Lucas M.", "Sarah B."],
            )

        assert (
            "The number of participants cannot exceed the maximum number of participants."
            in str(exc_info.value)
        )

    @pytest.mark.parametrize(
        "duplicate_participants",
        [
            ["Camille R.", "Camille R."],
            ["Camille R.", "camille r."],
            ["  Camille R. ", "CAMILLE R."],
        ],
    )
    def test_duplicate_participants_case_insensitive_raises_validation_error(
        self, duplicate_participants: list[str]
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            WorkshopPerformanceRequest(
                kind="workshop",
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=5,
                participants=duplicate_participants,
            )

        assert "Cannot have duplicate participants." in str(exc_info.value)


class TestSoloPerformanceRequestAndCommonConstraints:
    """Tests for `SoloPerformanceRequest`, `PerformanceIn`, and `PerformanceRequest`."""

    def test_valid_solo_performance_request(self) -> None:
        req = SoloPerformanceRequest(
            kind="solo",
            title="  After Hours ",
            venue="Le Kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=60,
            artist="Élodie Marchal",
            min_age=16,
        )
        assert req.title == "After Hours"
        assert req.venue == "le-kiosque"
        assert req.artist == "elodie-marchal"
        assert req.min_age == 16

    def test_extra_fields_are_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SoloPerformanceRequest(
                kind="solo",
                title="After Hours",
                venue="le-kiosque",
                start=datetime(2027, 6, 12, 1, 0),
                duration_minutes=60,
                artist="elodie-marchal",
                unexpected_field="nope",  # type: ignore[call-arg]
            )

    def test_discriminated_union_performance_request(self) -> None:
        adapter: TypeAdapter[PerformanceRequest] = TypeAdapter(PerformanceRequest)
        parsed = adapter.validate_python(
            {
                "kind": "lineup",
                "title": "Comedy Night",
                "venue": "le-kiosque",
                "start": "2027-06-10T21:00",
                "duration_minutes": 45,
                "host": "elodie-marchal",
                "acts": ["hugo-vernier", "camille-roux"],
            }
        )
        assert isinstance(parsed, LineupPerformanceRequest)

    def test_performance_response_datetime_serializers(self) -> None:
        in_resp = PerformanceInResponse(
            kind="solo",
            title="After Hours",
            venue="le-kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=60,
            artist="elodie-marchal",
            min_age=16,
        )
        dumped_in = in_resp.model_dump()
        assert dumped_in["start"] == "2027-06-12T01:00"

        full_resp = PerformanceResponse(
            id="le-kiosque-2027-06-12-0100",
            kind="solo",
            title="After Hours",
            venue="le-kiosque",
            venue_name="Le Kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            end=datetime(2027, 6, 12, 2, 0),
            duration_minutes=60,
            festival_day=date(2027, 6, 11),
            capacity=120,
            artists=[
                PerformanceResponse.ArtistInfo(
                    slug="elodie-marchal", name="Élodie Marchal"
                )
            ],
            artist="elodie-marchal",
            min_age=16,
        )
        dumped_full = full_resp.model_dump()
        assert dumped_full["start"] == "2027-06-12T01:00"
        assert dumped_full["end"] == "2027-06-12T02:00"
