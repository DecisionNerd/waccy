"""Core data models for extracted financial data."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ExtractedTransaction(BaseModel):
    """Standard transaction format."""

    date: date
    account_id: str  # Mapped to WACCY standard
    amount: Decimal
    description: str
    source_id: str
    confidence: float = Field(ge=0.0, le=1.0)  # Mapping confidence score


class ExtractedData(BaseModel):
    """Standard extracted data format."""

    transactions: list[ExtractedTransaction]
    accounts: list[dict[str, Any]]  # Account metadata
    metadata: dict[str, Any]
    quality_score: float = Field(ge=0.0, le=1.0)

    def generate_quality_report(self) -> dict[str, Any]:
        """Generate a quality report for the extracted data."""
        # TODO: Implement quality report generation
        return {
            "completeness": 0.0,
            "avg_confidence": 0.0,
            "issues": [],
        }

