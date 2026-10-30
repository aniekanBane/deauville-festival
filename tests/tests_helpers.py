from datetime import date, datetime

import pytest

from deauville_festival import errors, helpers


class TestGetSlug:
    """Tests for `helpers.get_slug`."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Le Kiosque", "le-kiosque"),
            ("Théâtre des Planches", "theatre-des-planches"),
            ("Élodie  Marchal !", "elodie-marchal"),
            ("Studio 42", "studio-42"),
            ("le-casino", "le-casino"),
            ("Rock & Roll: Part 1!", "rock-roll-part-1"),
            ("Café de l'Étoile---2027", "cafe-de-l-etoile-2027"),
            ("", ""),
        ],
    )
    def test_get_slug_returns_expected_slug(self, name: str, expected: str) -> None:
        assert helpers.get_slug(name) == expected


class TestDateFromStr:
    """Tests for `helpers.date_from_str`."""

    @pytest.mark.parametrize(
        ("date_str", "expected"),
        [
            ("2027-06-10", date(2027, 6, 10)),
            ("2027-01-01", date(2027, 1, 1)),
            ("2028-02-29", date(2028, 2, 29)),
        ],
    )
    def test_valid_date_str_returns_date(self, date_str: str, expected: date) -> None:
        assert helpers.date_from_str(date_str) == expected

    @pytest.mark.parametrize(
        "invalid_date_str",
        [
            "",
            "not-a-date",
            "10-06-2027",
            "2027/06/10",
            "2027-13-01",
            "2027-02-29",
            "2027-06-31",
        ],
    )
    def test_invalid_date_str_raises_invalid_date_format_error(
        self, invalid_date_str: str
    ) -> None:
        with pytest.raises(errors.InvalidDateFormatError) as exc_info:
            helpers.date_from_str(invalid_date_str)

        assert str(exc_info.value) == (
            f"'{invalid_date_str}' is not a valid date. Use YYYY-MM-DD format."
        )


class TestDatetimeFromStr:
    """Tests for `helpers.datetime_from_str`."""

    @pytest.mark.parametrize(
        ("datetime_str", "expected"),
        [
            ("2027-06-12T01:00", datetime(2027, 6, 12, 1, 0)),
            ("2027-06-10T21:30", datetime(2027, 6, 10, 21, 30)),
            ("2027-06-13T00:00", datetime(2027, 6, 13, 0, 0)),
        ],
    )
    def test_valid_datetime_str_returns_datetime(
        self, datetime_str: str, expected: datetime
    ) -> None:
        assert helpers.datetime_from_str(datetime_str) == expected

    @pytest.mark.parametrize(
        "invalid_datetime_str",
        [
            "",
            "not-a-datetime",
            "12-06-2027T01:00",
            "2027/06/12T01:00",
            "2027-06-12T25:00",
            "2027-06-12T12:60",
            "2027-02-29T10:00",
        ],
    )
    def test_invalid_datetime_str_raises_invalid_datetime_format_error(
        self, invalid_datetime_str: str
    ) -> None:
        with pytest.raises(errors.InvalidDateTimeFormatError) as exc_info:
            helpers.datetime_from_str(invalid_datetime_str)

        assert str(exc_info.value) == (
            f"'{invalid_datetime_str}' is not a valid date and time. "
            "Use YYYY-MM-DDTHH:MM format."
        )


class TestDatetimeToStr:
    """Tests for `helpers.datetime_to_str`."""

    @pytest.mark.parametrize(
        ("dt", "expected"),
        [
            (datetime(2027, 6, 12, 1, 0), "2027-06-12T01:00"),
            (datetime(2027, 6, 10, 21, 30), "2027-06-10T21:30"),
            (datetime(2027, 1, 5, 0, 5), "2027-01-05T00:05"),
        ],
    )
    def test_datetime_to_str_formats_correctly(
        self, dt: datetime, expected: str
    ) -> None:
        assert helpers.datetime_to_str(dt) == expected

    def test_datetime_roundtrip(self) -> None:
        original = datetime(2027, 6, 11, 19, 45)
        formatted = helpers.datetime_to_str(original)
        assert helpers.datetime_from_str(formatted) == original


class TestGuardEmptyStr:
    """Tests for `helpers.guard_empty_str`."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("After Hours", "After Hours"),
            ("  Le Kiosque  ", "Le Kiosque"),
            ("\t\nThéâtre des Planches\n ", "Théâtre des Planches"),
        ],
    )
    def test_valid_string_returns_stripped_value(
        self, value: str, expected: str
    ) -> None:
        assert helpers.guard_empty_str(value, "title") == expected

    @pytest.mark.parametrize(
        "empty_value",
        [
            "",
            " ",
            "   ",
            "\t",
            "\n",
            " \t\n\r ",
        ],
    )
    def test_empty_or_whitespace_string_raises_invalid_error(
        self, empty_value: str
    ) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            helpers.guard_empty_str(empty_value, "venue slug")

        assert str(exc_info.value) == "Value for venue slug cannot be empty."
