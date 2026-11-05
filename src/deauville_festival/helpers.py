import re
import unicodedata
from datetime import date, datetime

from deauville_festival import errors


def get_slug(name: str) -> str:
    """Returns the slug of a given name."""
    normalized = unicodedata.normalize("NFKD", name)
    plain_text = normalized.encode("ascii", "ignore").decode("ascii")

    result = ""
    for char in plain_text.lower():
        if char.isalnum():
            result += char
        elif not result.endswith("-"):
            result += "-"

    return result.rstrip("-")


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


def date_from_str(date_str: str) -> date:
    """Validates the date format (YYYY-MM-DD) and returns it if valid.

    Raises:
        InvalidDateFormatError: If the date format is invalid.
    """
    try:
        if not DATE_PATTERN.match(date_str):
            raise ValueError()

        return date.fromisoformat(date_str)
    except ValueError:
        raise errors.InvalidDateFormatError(date_str) from None


def datetime_from_str(date_time_str: str) -> datetime:
    """Validates the datetime format (YYYY-MM-DDTHH:MM) and returns it if valid.

    Raises:
        InvalidDateTimeFormatError: If the datetime format is invalid.
    """
    try:
        if not DATETIME_PATTERN.match(date_time_str):
            raise ValueError()

        return datetime.fromisoformat(date_time_str)
    except ValueError:
        raise errors.InvalidDateTimeFormatError(date_time_str) from None


def datetime_to_str(dt: datetime) -> str:
    """Returns the datetime as a string in the format YYYY-MM-DDTHH:MM."""
    return dt.strftime("%Y-%m-%dT%H:%M")


def guard_empty_str(value: str, label: str, error_message: str | None = None) -> str:
    """Raises an `InvalidError` if the string value is empty or whitespace."""
    value = value.strip()
    if not value:
        raise errors.InvalidError(
            error_message if error_message is not None else f"{label} cannot be empty."
        )

    return value


def guard_str_max_len(
    value: str,
    max_len: int,
    label: str,
    error_message: str | None = None,
) -> str:
    """Raises an `InvalidError` if the string value is longer than `max_len`."""
    if len(value) > max_len:
        raise errors.InvalidError(
            error_message
            if error_message is not None
            else f"{label} cannot be longer than {max_len} characters."
        )

    return value


def guard_value_greater_than(
    value: int,
    min_value: int,
    label: str,
    error_message: str | None = None,
) -> int:
    """Raises an `InvalidError` if the value is less than `min_value`."""
    if value < min_value:
        raise errors.InvalidError(
            error_message
            if error_message is not None
            else f"{label} must be at least {min_value}."
        )

    return value


def guard_value_range(
    value: int,
    max_value: int,
    min_value: int,
    label: str,
    error_message: str | None = None,
) -> int:
    """Raises an `InvalidError` if the value is outside [min_value, max_value]."""
    if not (min_value <= value <= max_value):
        raise errors.InvalidError(
            error_message
            if error_message is not None
            else f"{label} must be between {min_value} and {max_value}."
        )

    return value
