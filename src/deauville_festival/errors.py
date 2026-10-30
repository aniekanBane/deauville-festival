"""Custom errors/exceptions."""


class FestivalError(Exception):
    """Base exception for the festival application."""


class ConflictError(FestivalError):
    """Custom exception when a schedule conflict occurs (maps to HTTP 409)."""


class NotFoundError(FestivalError):
    """Custom exception when an entity is not found (maps to HTTP 404)."""


class InvalidError(FestivalError):
    """Custom exception when an invalid value is provided (maps to HTTP 400/422)."""


class InvalidDateFormatError(InvalidError):
    """Custom exception for invalid date format."""

    def __init__(self, date_str: str) -> None:
        super().__init__(f"'{date_str}' is not a valid date. Use YYYY-MM-DD format.")


class InvalidDateTimeFormatError(InvalidError):
    """Custom exception for invalid date and time format."""

    def __init__(self, datetime_str: str) -> None:
        super().__init__(
            f"'{datetime_str}' is not a valid date and time. "
            "Use YYYY-MM-DDTHH:MM format."
        )
