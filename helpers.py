import unicodedata
from datetime import date, datetime

import errors


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


def date_from_str(date_str: str) -> date:
    """Validates the date format (YYYY-MM-DD) and returns it if valid."""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise errors.InvalidDateFormatError(date_str) from None


def datetime_from_str(date_time_str: str) -> datetime:
    """Validates the date and time format (YYYY-MM-DDTHH:MM) and returns it if valid."""
    try:
        return datetime.fromisoformat(date_time_str)
    except ValueError:
        raise errors.InvalidDateTimeFormatError(date_time_str) from None


def guard_empty_str(value: str, label: str) -> str:
    """Raises a `ValueError` if the string is empty or contains only whitespace."""
    value = value.strip()
    if not value:
        raise ValueError(f"Value for {label} cannot be empty.")
    return value
