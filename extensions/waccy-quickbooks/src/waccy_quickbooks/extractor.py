"""QuickBooks Online fixture-first extractor implementation."""

from __future__ import annotations

from datetime import date
from typing import Any

from waccy.core.models import ExtractedData, PeriodType, ReportingPeriod
from waccy.extraction.base import Extractor
from waccy.extraction.mapper import source_record_from_dict


class QuickBooksExtractor(Extractor):
    """Extractor for QuickBooks Online-shaped fixture data."""

    @property
    def name(self) -> str:
        """Extractor name."""
        return "QuickBooks Online"

    @property
    def data_source(self) -> str:
        """Data source identifier."""
        return "qbo"

    def authenticate(self, credentials: dict[str, str]) -> bool:
        """Accept fixture-mode authentication.

        Live QuickBooks OAuth is intentionally out of scope for v0.1.0.
        """
        del credentials
        return True

    def extract(self, config: dict[str, Any]) -> ExtractedData:
        """Extract data from a QuickBooks-shaped fixture or dictionary."""
        fixture = config.get("fixture") or config.get("data") or config
        if not isinstance(fixture, dict):
            raise ValueError("QuickBooks fixture extraction requires a dictionary payload.")

        raw_records = fixture.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("QuickBooks fixture extraction requires a 'records' list.")
        if not all(isinstance(record, dict) for record in raw_records):
            raise ValueError("QuickBooks fixture records must be dictionaries.")

        raw_periods = fixture.get("periods", [])
        if not isinstance(raw_periods, list):
            raise ValueError("QuickBooks fixture periods must be a list.")

        periods = [_period_from_dict(period) for period in raw_periods]
        records = [source_record_from_dict(record, self.data_source) for record in raw_records]
        raw_accounts = fixture.get("accounts", [])
        if not isinstance(raw_accounts, list):
            raise ValueError("QuickBooks fixture accounts must be a list.")
        if not all(isinstance(account, dict) for account in raw_accounts):
            raise ValueError("QuickBooks fixture accounts must be dictionaries.")
        return ExtractedData(
            entity_name=str(fixture.get("entity_name", config.get("company_id", "QuickBooks Entity"))),
            periods=periods,
            source_records=records,
            accounts=raw_accounts,
            metadata={
                "source": self.data_source,
                "mode": "fixture",
                **dict(fixture.get("metadata", {})),
            },
            quality_score=1.0,
        )


def _period_from_dict(data: dict[str, Any]) -> ReportingPeriod:
    return ReportingPeriod(
        label=str(data["label"]),
        start_date=date.fromisoformat(str(data["start_date"])),
        end_date=date.fromisoformat(str(data["end_date"])),
        period_type=PeriodType(str(data.get("period_type", "year"))),
    )
