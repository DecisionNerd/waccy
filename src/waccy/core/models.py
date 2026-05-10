"""Core data models for WACCY's layered financial data contract."""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    """Supported reporting period granularities."""

    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MappingStatus(str, Enum):
    """Review state for a source-to-standard account mapping."""

    MAPPED = "mapped"
    AMBIGUOUS = "ambiguous"
    OVERRIDDEN = "overridden"
    UNMAPPED = "unmapped"


class IssueSeverity(str, Enum):
    """Validation issue severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SourceReference(BaseModel):
    """Pointer back to a source system record."""

    source_system: str
    source_id: str
    source_label: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportingPeriod(BaseModel):
    """A reporting period used as a model column."""

    label: str
    start_date: date
    end_date: date
    period_type: PeriodType = PeriodType.YEAR


class SourceRecord(BaseModel):
    """A source-shaped financial record before WACCY account mapping."""

    source_account_id: str
    source_account_name: str
    amount: Decimal
    period_label: str
    source: SourceReference
    unit: str = "USD"
    statement: str | None = None
    source_account_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedFinancialDataset(BaseModel):
    """Source-agnostic records with source-native account/concept identity preserved."""

    entity_name: str
    periods: list[ReportingPeriod]
    records: list[SourceRecord]
    metadata: dict[str, Any] = Field(default_factory=dict)


class MappingDiagnostic(BaseModel):
    """Explanation for a mapping decision or issue."""

    code: str
    message: str


class MappingOverride(BaseModel):
    """Caller-provided account mapping override."""

    account_id: str
    note: str = ""


class MappedFinancialRecord(BaseModel):
    """A normalized record mapped to the WACCY ontology."""

    source_record: SourceRecord
    account_id: str | None = None
    account_name: str | None = None
    status: MappingStatus
    confidence: float = Field(ge=0.0, le=1.0)
    diagnostics: list[MappingDiagnostic] = Field(default_factory=list)
    override_note: str | None = None


class MappedFinancialDataset(BaseModel):
    """Normalized financial data after source-to-standard account mapping."""

    entity_name: str
    periods: list[ReportingPeriod]
    records: list[MappedFinancialRecord]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    """A validation or reconciliation issue."""

    code: str
    message: str
    severity: IssueSeverity = IssueSeverity.ERROR
    period_label: str | None = None
    account_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidatedFinancialDataset(BaseModel):
    """Mapped financial data plus validation diagnostics."""

    mapped_dataset: MappedFinancialDataset
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return whether the dataset has no error-level issues."""
        return not any(issue.severity == IssueSeverity.ERROR for issue in self.issues)


class ExtractedTransaction(BaseModel):
    """Legacy transaction format retained for compatibility."""

    date: date
    account_id: str
    amount: Decimal
    description: str
    source_id: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedData(BaseModel):
    """Extractor output that can carry source records into the layered contract."""

    transactions: list[ExtractedTransaction] = Field(default_factory=list)
    accounts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    entity_name: str = "Unknown Entity"
    periods: list[ReportingPeriod] = Field(default_factory=list)
    source_records: list[SourceRecord] = Field(default_factory=list)

    def generate_quality_report(self) -> dict[str, Any]:
        """Generate a basic quality report for extracted data."""
        record_count = len(self.source_records) + len(self.transactions)
        mapped_transactions = [txn for txn in self.transactions if txn.account_id]
        avg_confidence = (
            sum(txn.confidence for txn in self.transactions) / len(self.transactions)
            if self.transactions
            else self.quality_score
        )
        issues = []
        if record_count == 0:
            issues.append("No source records or transactions were extracted.")
        if self.transactions and len(mapped_transactions) != len(self.transactions):
            issues.append("Some transactions are missing account mappings.")
        return {
            "completeness": 1.0 if record_count else 0.0,
            "avg_confidence": avg_confidence,
            "issues": issues,
        }


class StatementLine(BaseModel):
    """A line item in a financial statement."""

    label: str
    account_id: str | None = None
    values: dict[str, Decimal] = Field(default_factory=dict)
    is_subtotal: bool = False
    is_check: bool = False
    source_account_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinancialStatement(BaseModel):
    """A financial statement composed of ordered line items."""

    name: Literal["Income Statement", "Balance Sheet", "Cash Flow Statement"]
    periods: list[ReportingPeriod]
    lines: list[StatementLine]


class ThreeStatementModel(BaseModel):
    """Source-agnostic three-statement model output."""

    entity_name: str
    periods: list[ReportingPeriod]
    income_statement: FinancialStatement
    balance_sheet: FinancialStatement
    cash_flow_statement: FinancialStatement
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
