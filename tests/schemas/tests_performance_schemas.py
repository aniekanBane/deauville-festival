from datetime import date, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from deauville_festival.api.schemas import (
    LineupPerformanceRequest,
    LineupPerformanceResponse,
    PerformanceRequest,
    SoloPerformanceRequest,
    SoloPerformanceResponse,
    WorkshopPerformanceRequest,
    WorkshopPerformanceResponse,
    performance_response_type_adapter,
)


class TestLineupPerformanceRequestValidation:
    """Tests for `LineupPerformanceRequest` schema constraints."""

    def test_valid_lineup_request(self) -> None:
        req = LineupPerformanceRequest(
            kind="lineup",
            title="  Gala Night ",
            venue="theatre-des-planches",
            start=datetime(2027, 6, 10, 21, 0),
            duration_minutes=60,
            host="elodie-marchal",
            acts=["hugo-vernier", "camille-roux"],
        )
        assert req.title == "Gala Night"
        assert req.venue == "theatre-des-planches"
        assert req.host == "elodie-marchal"
        assert req.acts == ["hugo-vernier", "camille-roux"]
        assert req.duration_minutes == 60

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
        assert "List should have at least 2 items" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_duration", [0, -10, 361, 500])
    def test_duration_out_of_range_raises_validation_error(
        self, invalid_duration: int
    ) -> None:
        with pytest.raises(ValidationError):
            LineupPerformanceRequest(
                kind="lineup",
                title="Gala Night",
                venue="le-kiosque",
                start=datetime(2027, 6, 10, 21, 0),
                duration_minutes=invalid_duration,
                host="elodie-marchal",
                acts=["hugo-vernier", "camille-roux"],
            )


class TestWorkshopPerformanceRequestValidation:
    """Tests for `WorkshopPerformanceRequest` schema constraints."""

    def test_valid_workshop_with_default_empty_participants(self) -> None:
        req = WorkshopPerformanceRequest(
            kind="workshop",
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=10,
        )
        assert req.venue == "salon-d-honneur"
        assert req.teacher == "elodie-marchal"
        assert req.participants == []
        assert req.max_participants == 10

    def test_valid_workshop_with_participants(self) -> None:
        req = WorkshopPerformanceRequest(
            kind="workshop",
            title="Improv 101",
            venue="salon-d-honneur",
            start=datetime(2027, 6, 11, 14, 0),
            duration_minutes=120,
            teacher="elodie-marchal",
            max_participants=5,
            participants=["  Camille R. ", "Lucas M."],
        )
        assert req.participants == ["Camille R.", "Lucas M."]

    @pytest.mark.parametrize("invalid_max", [0, -1, -10])
    def test_max_participants_below_minimum_raises_validation_error(
        self, invalid_max: int
    ) -> None:
        with pytest.raises(ValidationError):
            WorkshopPerformanceRequest(
                kind="workshop",
                title="Improv 101",
                venue="salon-d-honneur",
                start=datetime(2027, 6, 11, 14, 0),
                duration_minutes=120,
                teacher="elodie-marchal",
                max_participants=invalid_max,
            )


class TestSoloPerformanceRequestAndCommonConstraints:
    """Tests for `SoloPerformanceRequest`, `PerformanceIn`, and `PerformanceRequest`."""

    def test_valid_solo_performance_request(self) -> None:
        req = SoloPerformanceRequest(
            kind="solo",
            title="  After Hours ",
            venue="le-kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=60,
            artist="elodie-marchal",
            min_age=16,
        )
        assert req.title == "After Hours"
        assert req.venue == "le-kiosque"
        assert req.artist == "elodie-marchal"
        assert req.min_age == 16

    def test_default_min_age_is_zero(self) -> None:
        req = SoloPerformanceRequest(
            kind="solo",
            title="After Hours",
            venue="le-kiosque",
            start=datetime(2027, 6, 12, 1, 0),
            duration_minutes=60,
            artist="elodie-marchal",
        )
        assert req.min_age == 0

    @pytest.mark.parametrize("invalid_age", [-1, -5, 19, 100])
    def test_min_age_out_of_range_raises_validation_error(
        self, invalid_age: int
    ) -> None:
        with pytest.raises(ValidationError):
            SoloPerformanceRequest(
                kind="solo",
                title="After Hours",
                venue="le-kiosque",
                start=datetime(2027, 6, 12, 1, 0),
                duration_minutes=60,
                artist="elodie-marchal",
                min_age=invalid_age,
            )

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

    @pytest.mark.parametrize(
        ("payload", "expected_cls"),
        [
            (
                {
                    "kind": "solo",
                    "title": "Solo Show",
                    "venue": "le-kiosque",
                    "start": "2027-06-10T20:00",
                    "duration_minutes": 60,
                    "artist": "elodie-marchal",
                },
                SoloPerformanceRequest,
            ),
            (
                {
                    "kind": "lineup",
                    "title": "Comedy Night",
                    "venue": "le-kiosque",
                    "start": "2027-06-10T21:00",
                    "duration_minutes": 45,
                    "host": "elodie-marchal",
                    "acts": ["hugo-vernier", "camille-roux"],
                },
                LineupPerformanceRequest,
            ),
            (
                {
                    "kind": "workshop",
                    "title": "Improv Lab",
                    "venue": "salon-d-honneur",
                    "start": "2027-06-11T14:00",
                    "duration_minutes": 120,
                    "teacher": "elodie-marchal",
                    "max_participants": 12,
                },
                WorkshopPerformanceRequest,
            ),
        ],
    )
    def test_discriminated_union_performance_request(
        self, payload: dict[str, object], expected_cls: type
    ) -> None:
        adapter: TypeAdapter[PerformanceRequest] = TypeAdapter(PerformanceRequest)
        parsed = adapter.validate_python(payload)
        assert isinstance(parsed, expected_cls)

    def test_invalid_kind_raises_validation_error(self) -> None:
        adapter: TypeAdapter[PerformanceRequest] = TypeAdapter(PerformanceRequest)
        with pytest.raises(ValidationError):
            adapter.validate_python(
                {
                    "kind": "concert",
                    "title": "Concert",
                    "venue": "le-kiosque",
                    "start": "2027-06-10T21:00",
                    "duration_minutes": 60,
                }
            )


class TestPerformanceResponseSchemas:
    """Tests for `PerformanceResponse` discriminated union and serialization."""

    def test_solo_performance_response_datetime_serialization(self) -> None:
        resp = SoloPerformanceResponse(
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
                SoloPerformanceResponse.ArtistInfo(
                    slug="elodie-marchal", name="Élodie Marchal"
                )
            ],
            artist="elodie-marchal",
            min_age=16,
        )
        dumped = resp.model_dump(mode="json")
        assert dumped["start"] == "2027-06-12T01:00"
        assert dumped["end"] == "2027-06-12T02:00"
        assert dumped["kind"] == "solo"
        assert dumped["artist"] == "elodie-marchal"
        assert "host" not in dumped
        assert "teacher" not in dumped

    def test_lineup_performance_response_serialization(self) -> None:
        resp = LineupPerformanceResponse(
            id="grand-casino-2027-06-10-2030",
            kind="lineup",
            title="Opening Gala",
            venue="grand-casino",
            venue_name="Grand Casino",
            start=datetime(2027, 6, 10, 20, 30),
            end=datetime(2027, 6, 10, 22, 0),
            duration_minutes=90,
            festival_day=date(2027, 6, 10),
            capacity=400,
            artists=[
                LineupPerformanceResponse.ArtistInfo(
                    slug="paul-kerbrat", name="Paul Kerbrat"
                )
            ],
            host="paul-kerbrat",
            acts=["sacha-diallo", "ines-moreau"],
        )
        dumped = resp.model_dump(mode="json")
        assert dumped["kind"] == "lineup"
        assert dumped["host"] == "paul-kerbrat"
        assert dumped["acts"] == ["sacha-diallo", "ines-moreau"]
        assert "artist" not in dumped
        assert "teacher" not in dumped

    def test_workshop_performance_response_serialization(self) -> None:
        resp = WorkshopPerformanceResponse(
            id="salon-d-honneur-2027-06-11-1400",
            kind="workshop",
            title="Improv Lab",
            venue="salon-d-honneur",
            venue_name="Salon d'Honneur",
            start=datetime(2027, 6, 11, 14, 0),
            end=datetime(2027, 6, 11, 16, 0),
            duration_minutes=120,
            festival_day=date(2027, 6, 11),
            capacity=20,
            artists=[
                WorkshopPerformanceResponse.ArtistInfo(
                    slug="elodie-marchal", name="Élodie Marchal"
                )
            ],
            teacher="elodie-marchal",
            max_participants=20,
            participants=["Alice", "Bob"],
            places_left=18,
        )
        dumped = resp.model_dump(mode="json")
        assert dumped["kind"] == "workshop"
        assert dumped["teacher"] == "elodie-marchal"
        assert dumped["places_left"] == 18
        assert "host" not in dumped
        assert "min_age" not in dumped

    @pytest.mark.parametrize(
        ("kind", "specific_fields", "expected_cls"),
        [
            (
                "solo",
                {"artist": "elodie-marchal", "min_age": 16},
                SoloPerformanceResponse,
            ),
            (
                "lineup",
                {"host": "paul-kerbrat", "acts": ["sacha-diallo", "ines-moreau"]},
                LineupPerformanceResponse,
            ),
            (
                "workshop",
                {
                    "teacher": "elodie-marchal",
                    "max_participants": 20,
                    "participants": [],
                    "places_left": 20,
                },
                WorkshopPerformanceResponse,
            ),
        ],
    )
    def test_performance_response_adapter_discriminated_union(
        self, kind: str, specific_fields: dict[str, object], expected_cls: type
    ) -> None:
        base_data: dict[str, object] = {
            "id": "venue-2027-06-10-2000",
            "kind": kind,
            "title": "Test Show",
            "venue": "le-kiosque",
            "venue_name": "Le Kiosque",
            "start": datetime(2027, 6, 10, 20, 0),
            "end": datetime(2027, 6, 10, 21, 0),
            "duration_minutes": 60,
            "festival_day": date(2027, 6, 10),
            "description": "Desc",
            "summary": "Summary",
            "capacity": 100,
            "artists": [{"slug": "artist-1", "name": "Artist 1"}],
        }
        base_data.update(specific_fields)
        parsed = performance_response_type_adapter.validate_python(base_data)
        assert isinstance(parsed, expected_cls)
