"""Date utility functions."""

from datetime import date
from typing import Optional, Tuple


def parse_date_range(date_range: str | Tuple[str, str]) -> Tuple[date, date]:
    """Parse a date range string or tuple into date objects."""
    if isinstance(date_range, tuple):
        start_str, end_str = date_range
    else:
        # TODO: Parse string format (e.g., "2023-01-01 to 2024-12-31")
        raise NotImplementedError("String date range parsing not yet implemented")

    start_date = date.fromisoformat(start_str)
    end_date = date.fromisoformat(end_str)
    return start_date, end_date


def format_date(d: date, format_str: str = "%Y-%m-%d") -> str:
    """Format a date object as a string."""
    return d.strftime(format_str)


def validate_date_range(start: date, end: date) -> bool:
    """Validate that start date is before end date."""
    return start <= end

