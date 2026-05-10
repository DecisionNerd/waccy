"""Date utility functions."""

from __future__ import annotations

import calendar
import re
from datetime import date

from waccy.core.models import PeriodType, ReportingPeriod


def parse_date_range(date_range: str | tuple[str, str]) -> tuple[date, date]:
    """Parse a date range string or tuple into date objects."""
    if isinstance(date_range, tuple):
        start_str, end_str = date_range
    else:
        separator = next((sep for sep in (" to ", ",", "|") if sep in date_range), None)
        if separator is None:
            raise ValueError("Date range must use ' to ', ',', or '|' between ISO dates.")
        parts = [part.strip() for part in date_range.split(separator)]
        if len(parts) != 2 or not all(parts):
            raise ValueError("Date range must contain exactly two ISO dates.")
        start_str, end_str = parts

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError as exc:
        raise ValueError("Date range values must use ISO format YYYY-MM-DD.") from exc
    if start_date > end_date:
        raise ValueError("Date range start date must be on or before the end date.")
    return start_date, end_date


def infer_reporting_period(label: str) -> ReportingPeriod:
    """Infer a reporting period from a common annual, quarterly, or monthly label."""
    clean_label = label.strip()
    annual_match = re.fullmatch(r"(\d{4})", clean_label)
    quarter_match = re.fullmatch(r"(\d{4})-?Q([1-4])", clean_label, flags=re.IGNORECASE)
    month_match = re.fullmatch(r"(\d{4})-?([0-1]\d)", clean_label)

    if annual_match:
        year = int(annual_match.group(1))
        return ReportingPeriod(
            label=clean_label,
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            period_type=PeriodType.YEAR,
        )
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        start_month = ((quarter - 1) * 3) + 1
        end_month = start_month + 2
        return ReportingPeriod(
            label=clean_label,
            start_date=date(year, start_month, 1),
            end_date=date(year, end_month, calendar.monthrange(year, end_month)[1]),
            period_type=PeriodType.QUARTER,
        )
    if month_match:
        year = int(month_match.group(1))
        month = int(month_match.group(2))
        if not 1 <= month <= 12:
            raise ValueError(f"Unsupported reporting period month in label {label!r}.")
        return ReportingPeriod(
            label=clean_label,
            start_date=date(year, month, 1),
            end_date=date(year, month, calendar.monthrange(year, month)[1]),
            period_type=PeriodType.MONTH,
        )
    raise ValueError(f"Unsupported reporting period label {label!r}.")


def generate_reporting_periods(
    date_range: str | tuple[str, str],
    period_type: PeriodType | str = PeriodType.YEAR,
) -> list[ReportingPeriod]:
    """Generate deterministic reporting periods for a date range."""
    start_date, end_date = parse_date_range(date_range)
    period_type = period_type if isinstance(period_type, PeriodType) else PeriodType(str(period_type))
    periods: list[ReportingPeriod] = []

    if period_type == PeriodType.YEAR:
        for year in range(start_date.year, end_date.year + 1):
            period = ReportingPeriod(
                label=str(year),
                start_date=max(date(year, 1, 1), start_date),
                end_date=min(date(year, 12, 31), end_date),
                period_type=PeriodType.YEAR,
            )
            periods.append(period)
        return periods

    if period_type == PeriodType.QUARTER:
        year = start_date.year
        quarter = ((start_date.month - 1) // 3) + 1
        while True:
            start_month = ((quarter - 1) * 3) + 1
            end_month = start_month + 2
            period_start = date(year, start_month, 1)
            period_end = date(year, end_month, calendar.monthrange(year, end_month)[1])
            if period_start > end_date:
                break
            periods.append(
                ReportingPeriod(
                    label=f"{year}Q{quarter}",
                    start_date=max(period_start, start_date),
                    end_date=min(period_end, end_date),
                    period_type=PeriodType.QUARTER,
                )
            )
            quarter += 1
            if quarter > 4:
                quarter = 1
                year += 1
        return periods

    year = start_date.year
    month = start_date.month
    while True:
        period_start = date(year, month, 1)
        period_end = date(year, month, calendar.monthrange(year, month)[1])
        if period_start > end_date:
            break
        periods.append(
            ReportingPeriod(
                label=f"{year}-{month:02d}",
                start_date=max(period_start, start_date),
                end_date=min(period_end, end_date),
                period_type=PeriodType.MONTH,
            )
        )
        month += 1
        if month > 12:
            month = 1
            year += 1
    return periods


def format_date(d: date, format_str: str = "%Y-%m-%d") -> str:
    """Format a date object as a string."""
    return d.strftime(format_str)


def validate_date_range(start: date, end: date) -> bool:
    """Validate that start date is before end date."""
    return start <= end
