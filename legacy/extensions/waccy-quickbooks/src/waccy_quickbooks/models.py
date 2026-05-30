"""Typed models for QuickBooks Online OAuth and report pulls."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QuickBooksEnvironment(str, Enum):
    """Supported Intuit API environments."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


class QuickBooksOAuthConfig(BaseModel):
    """OAuth application configuration for Intuit."""

    client_id: str
    client_secret: str
    redirect_uri: str
    environment: QuickBooksEnvironment = QuickBooksEnvironment.SANDBOX


class QuickBooksToken(BaseModel):
    """Stored QuickBooks OAuth token state."""

    access_token: str
    refresh_token: str
    realm_id: str
    token_type: str = "bearer"
    expires_at: datetime | None = None
    refresh_token_expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_access_token_expired(
        self, now: datetime | None = None, skew: timedelta = timedelta(minutes=5)
    ) -> bool:
        """Return whether the access token should be refreshed before use."""
        if self.expires_at is None:
            return False
        current_time = now or datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at <= current_time + skew


class QuickBooksReportRequest(BaseModel):
    """Report request parameters for a QBO report endpoint."""

    report_name: str
    start_date: date
    end_date: date
    accounting_method: str = "Accrual"
    summarize_column_by: str | None = None


class QuickBooksReportPull(BaseModel):
    """Raw QBO payloads needed before WACCY fixture normalization."""

    realm_id: str
    entity_name: str
    environment: QuickBooksEnvironment
    start_date: date
    end_date: date
    company_info: dict[str, Any]
    accounts: list[dict[str, Any]]
    reports: dict[str, dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
