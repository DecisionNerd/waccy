"""Data validation for WACCY financial datasets."""

from __future__ import annotations

from waccy.core.models import (
    ExtractedData,
    IssueSeverity,
    MappedFinancialDataset,
    MappingStatus,
    ValidatedFinancialDataset,
    ValidationIssue,
)


def validate_extracted_data(data: ExtractedData) -> bool:
    """Validate extracted data has at least one usable source record or transaction."""
    return bool(data.source_records or data.transactions)


def validate_mapped_dataset(mapped_dataset: MappedFinancialDataset) -> ValidatedFinancialDataset:
    """Validate a mapped financial dataset and return diagnostics."""
    issues: list[ValidationIssue] = []
    seen_periods: set[str] = set()
    for period in mapped_dataset.periods:
        if period.label in seen_periods:
            issues.append(
                ValidationIssue(
                    code="duplicate_period",
                    message=f"Duplicate reporting period {period.label!r}.",
                    period_label=period.label,
                )
            )
        seen_periods.add(period.label)
        if period.start_date > period.end_date:
            issues.append(
                ValidationIssue(
                    code="invalid_period_range",
                    message=f"Period {period.label!r} starts after it ends.",
                    period_label=period.label,
                )
            )

    period_labels = {period.label for period in mapped_dataset.periods}
    for record in mapped_dataset.records:
        if record.source_record.period_label not in period_labels:
            issues.append(
                ValidationIssue(
                    code="missing_period",
                    message=(
                        f"Record {record.source_record.source.source_id!r} references missing "
                        f"period {record.source_record.period_label!r}."
                    ),
                    period_label=record.source_record.period_label,
                    account_id=record.account_id,
                )
            )
        if record.status == MappingStatus.UNMAPPED:
            issues.append(
                ValidationIssue(
                    code="unmapped_account",
                    message=f"Unmapped account {record.source_record.source_account_name!r}.",
                    severity=IssueSeverity.ERROR,
                    period_label=record.source_record.period_label,
                )
            )
        elif record.status == MappingStatus.AMBIGUOUS:
            issues.append(
                ValidationIssue(
                    code="ambiguous_mapping",
                    message=f"Ambiguous account {record.source_record.source_account_name!r}.",
                    severity=IssueSeverity.WARNING,
                    period_label=record.source_record.period_label,
                )
            )
        elif record.status == MappingStatus.OVERRIDDEN:
            issues.append(
                ValidationIssue(
                    code="mapping_overridden",
                    message=f"Mapping overridden for {record.source_record.source_account_name!r}.",
                    severity=IssueSeverity.INFO,
                    period_label=record.source_record.period_label,
                    account_id=record.account_id,
                )
            )

    if not mapped_dataset.records:
        issues.append(
            ValidationIssue(
                code="empty_dataset",
                message="No financial records are available for validation.",
            )
        )

    return ValidatedFinancialDataset(mapped_dataset=mapped_dataset, issues=issues)
