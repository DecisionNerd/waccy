"""Formatting utility functions."""

from decimal import Decimal


def format_currency(amount: Decimal | float, currency: str = "USD") -> str:
    """Format a number as currency."""
    # TODO: Implement proper currency formatting
    # Support for different currencies, locales, etc.
    return f"{currency} {amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as a percentage."""
    return f"{value * 100:.{decimals}f}%"

