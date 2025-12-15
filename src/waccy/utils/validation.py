"""Validation utility functions."""

from datetime import date


def validate_date_range(start: date, end: date) -> bool:
    """Validate that start date is before end date."""
    return start <= end


def validate_amount(amount: float | int) -> bool:
    """Validate that amount is a valid number."""
    return isinstance(amount, (int, float)) and not (isinstance(amount, float) and amount != amount)  # Check for NaN

