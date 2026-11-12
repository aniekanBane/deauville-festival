from datetime import datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from deauville_festival.api.schemas import DateTimeStr, RequiredStr, SlugStr


class TestRequiredStr:
    """Tests for the RequiredStr type."""

    adapter: TypeAdapter[RequiredStr] = TypeAdapter(RequiredStr)

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("hello", "hello"),
            ("  hello  ", "hello"),
            ("  hello world  \n\t", "hello world"),
        ],
    )
    def test_valid_required_str(self, input_val: str, expected: str) -> None:
        assert self.adapter.validate_python(input_val) == expected

    @pytest.mark.parametrize("invalid_val", ["", "   ", "\t\n", "   \t  "])
    def test_empty_or_whitespace_str_raises_validation_error(
        self, invalid_val: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            self.adapter.validate_python(invalid_val)
        assert "String should have at least 1 character" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_type", [123, None, [], {}])
    def test_non_string_raises_validation_error(self, invalid_type: object) -> None:
        with pytest.raises(ValidationError):
            self.adapter.validate_python(invalid_type)


class TestSlugStr:
    """Tests for the SlugStr type."""

    adapter: TypeAdapter[SlugStr] = TypeAdapter(SlugStr)

    @pytest.mark.parametrize(
        "valid_slug",
        [
            "grand-casino",
            "le-kiosque",
            "act-1",
            "123-abc",
            "elodie-marchal",
            "salon-d-honneur",
            "solo",
        ],
    )
    def test_valid_slug(self, valid_slug: str) -> None:
        assert self.adapter.validate_python(valid_slug) == valid_slug

    @pytest.mark.parametrize(
        "invalid_slug",
        [
            "Grand Casino",
            "grand_casino",
            "-leading-hyphen",
            "trailing-hyphen-",
            "double--hyphen",
            "---",
            "!!!",
            "   -   ",
            "hello world",
            "accentué",
        ],
    )
    def test_invalid_slug_raises_validation_error(self, invalid_slug: str) -> None:
        with pytest.raises(ValidationError) as exc_info:
            self.adapter.validate_python(invalid_slug)
        assert "Value must be a valid url slug." in str(exc_info.value)

    @pytest.mark.parametrize("empty_slug", ["", "   ", "\t"])
    def test_empty_slug_raises_validation_error(self, empty_slug: str) -> None:
        with pytest.raises(ValidationError):
            self.adapter.validate_python(empty_slug)


class TestDateTimeStrSerialization:
    """Tests for the DateTimeStr serialization and deserialization."""

    adapter: TypeAdapter[DateTimeStr] = TypeAdapter(DateTimeStr)

    def test_serialization_to_string(self) -> None:
        dt = datetime(2027, 6, 10, 20, 30)
        assert self.adapter.dump_python(dt) == "2027-06-10T20:30"
        assert self.adapter.dump_json(dt) == b'"2027-06-10T20:30"'

    def test_deserialization_from_valid_string(self) -> None:
        parsed = self.adapter.validate_python("2027-06-10T20:30")
        assert parsed == datetime(2027, 6, 10, 20, 30)

    def test_validation_from_datetime_instance(self) -> None:
        dt = datetime(2027, 6, 10, 20, 30)
        assert self.adapter.validate_python(dt) == dt

    @pytest.mark.parametrize(
        "invalid_datetime", ["", "not-a-datetime", "2027-13-45", "invalid"]
    )
    def test_invalid_datetime_raises_validation_error(
        self, invalid_datetime: str
    ) -> None:
        with pytest.raises(ValidationError):
            self.adapter.validate_python(invalid_datetime)
