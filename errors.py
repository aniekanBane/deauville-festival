"""Custom errors/exceptions."""


class InvalidDateFormatError(ValueError):
    """Custom exception for invalid date format."""

    def __init__(self, date_str: str) -> None:
        super().__init__(f"'{date_str}' is not a valid date. Use YYYY-MM-DD format.")


class InvalidDateTimeFormatError(ValueError):
    """Custom exception for invalid date and time format."""

    def __init__(self, date_time_str: str) -> None:
        super().__init__(
            f"'{date_time_str}' is not a valid date and time. "
            "Use YYYY-MM-DDTHH:MM format."
        )
