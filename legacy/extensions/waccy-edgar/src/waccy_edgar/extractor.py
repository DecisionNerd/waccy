"""SEC EDGAR fixture-first extractor implementation."""

from __future__ import annotations

from datetime import date
from typing import Any

from waccy.core.models import ExtractedData, PeriodType, ReportingPeriod
from waccy.extraction.base import Extractor
from waccy.extraction.mapper import source_record_from_dict


class EdgarExtractor(Extractor):
    """Extractor for SEC EDGAR-shaped fixture data."""

    @property
    def name(self) -> str:
        """Extractor name."""
        return "SEC EDGAR"

    @property
    def data_source(self) -> str:
        """Data source identifier."""
        return "edgar"

    def authenticate(self, credentials: dict[str, str]) -> bool:
        """Authenticate with SEC EDGAR fixture mode."""
        del credentials
        return True

    def extract(self, config: dict[str, Any]) -> ExtractedData:
        """Extract data from an EDGAR-shaped fixture or dictionary."""
        if "fixture" in config:
            fixture = config["fixture"]
        elif "data" in config:
            fixture = config["data"]
        else:
            fixture = config
        if not isinstance(fixture, dict):
            raise ValueError("EDGAR fixture extraction requires a dictionary payload.")

        raw_records = fixture.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("EDGAR fixture extraction requires a 'records' list.")
        if not all(isinstance(record, dict) for record in raw_records):
            raise ValueError("EDGAR fixture records must be dictionaries.")

        raw_periods = fixture.get("periods", [])
        if not isinstance(raw_periods, list):
            raise ValueError("EDGAR fixture periods must be a list.")
        if not all(isinstance(period, dict) for period in raw_periods):
            raise ValueError("EDGAR fixture periods must be dictionaries.")

        periods = [_period_from_dict(period) for period in raw_periods]
        records = [source_record_from_dict(record, self.data_source) for record in raw_records]
        return ExtractedData(
            entity_name=str(fixture.get("entity_name", config.get("ticker", "EDGAR Entity"))),
            periods=periods,
            source_records=records,
            metadata={
                "source": self.data_source,
                "mode": "fixture",
                "ticker": config.get("ticker"),
                **dict(fixture.get("metadata", {})),
            },
            quality_score=1.0,
        )


def _period_from_dict(data: dict[str, Any]) -> ReportingPeriod:
    missing_keys = {"label", "start_date", "end_date"} - data.keys()
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"EDGAR fixture period is missing required keys: {missing}. Period: {data!r}")

    return ReportingPeriod(
        label=str(data["label"]),
        start_date=date.fromisoformat(str(data["start_date"])),
        end_date=date.fromisoformat(str(data["end_date"])),
        period_type=PeriodType(str(data.get("period_type", "year"))),
    )
