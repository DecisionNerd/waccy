"""Mapping extracted data to the WACCY standard ontology."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from waccy.core.models import (
    ExtractedData,
    MappedFinancialDataset,
    MappedFinancialRecord,
    MappingDiagnostic,
    MappingOverride,
    MappingStatus,
    NormalizedFinancialDataset,
    ReportingPeriod,
    SourceRecord,
    SourceReference,
    ValidatedFinancialDataset,
)
from waccy.core.ontology import StandardChartOfAccounts
from waccy.core.validation import validate_mapped_dataset
from waccy.utils.dates import infer_reporting_period


def _period_from_label(label: str) -> ReportingPeriod:
    return infer_reporting_period(label)


class DataMapper:
    """Maps extracted source data to WACCY standard accounts."""

    def __init__(self, ontology: StandardChartOfAccounts | None = None) -> None:
        """Initialize the mapper with standard ontology."""
        self.ontology = ontology or StandardChartOfAccounts()

    def normalize(self, extracted_data: ExtractedData) -> NormalizedFinancialDataset:
        """Normalize extractor output into the source-agnostic financial dataset."""
        records = list(extracted_data.source_records)
        if not records and extracted_data.transactions:
            records = [
                SourceRecord(
                    source_account_id=txn.account_id,
                    source_account_name=txn.account_id,
                    amount=txn.amount,
                    period_label=str(txn.date.year),
                    statement=None,
                    source=SourceReference(
                        source_system=str(extracted_data.metadata.get("source", "unknown")),
                        source_id=txn.source_id,
                        source_label=txn.description,
                    ),
                )
                for txn in extracted_data.transactions
            ]

        periods_by_label = {period.label: period for period in extracted_data.periods}
        for record in records:
            periods_by_label.setdefault(record.period_label, _period_from_label(record.period_label))

        return NormalizedFinancialDataset(
            entity_name=extracted_data.entity_name,
            periods=sorted(periods_by_label.values(), key=lambda period: period.start_date),
            records=records,
            metadata=extracted_data.metadata,
        )

    def map_dataset(
        self,
        dataset: NormalizedFinancialDataset,
        overrides: dict[str, str | MappingOverride] | None = None,
    ) -> MappedFinancialDataset:
        """Map normalized source records to WACCY standard accounts."""
        overrides = overrides or {}
        mapped_records: list[MappedFinancialRecord] = []
        for record in dataset.records:
            override = self._find_override(record, overrides)
            if override is not None:
                mapped_records.append(self._apply_override(record, override))
                continue

            candidates = self.ontology.map_candidates(
                record.source_account_name,
                record.source.source_system,
            )
            if len(candidates) > 1 and record.statement:
                statement_candidates = [
                    account for account in candidates if account.statement == record.statement
                ]
                if statement_candidates:
                    candidates = statement_candidates
            if len(candidates) == 1:
                account = candidates[0]
                mapped_records.append(
                    MappedFinancialRecord(
                        source_record=record,
                        account_id=account.id,
                        account_name=account.name,
                        status=MappingStatus.MAPPED,
                        confidence=0.95,
                    )
                )
            elif len(candidates) > 1:
                mapped_records.append(
                    MappedFinancialRecord(
                        source_record=record,
                        status=MappingStatus.AMBIGUOUS,
                        confidence=0.4,
                        diagnostics=[
                            MappingDiagnostic(
                                code="ambiguous_mapping",
                                message=(
                                    "Source account matched multiple WACCY accounts: "
                                    + ", ".join(account.id for account in candidates)
                                ),
                            )
                        ],
                    )
                )
            else:
                mapped_records.append(
                    MappedFinancialRecord(
                        source_record=record,
                        status=MappingStatus.UNMAPPED,
                        confidence=0.0,
                        diagnostics=[
                            MappingDiagnostic(
                                code="unmapped_account",
                                message=f"No WACCY account mapping for {record.source_account_name!r}.",
                            )
                        ],
                    )
                )

        return MappedFinancialDataset(
            entity_name=dataset.entity_name,
            periods=dataset.periods,
            records=mapped_records,
            metadata=dataset.metadata,
        )

    def validate(self, mapped_dataset: MappedFinancialDataset) -> ValidatedFinancialDataset:
        """Validate a mapped dataset."""
        return validate_mapped_dataset(mapped_dataset)

    def map_to_standard(
        self,
        extracted_data: ExtractedData,
        overrides: dict[str, str | MappingOverride] | None = None,
    ) -> ValidatedFinancialDataset:
        """Normalize, map, and validate extracted data."""
        normalized = self.normalize(extracted_data)
        mapped = self.map_dataset(normalized, overrides=overrides)
        return self.validate(mapped)

    def _find_override(
        self,
        record: SourceRecord,
        overrides: dict[str, str | MappingOverride],
    ) -> str | MappingOverride | None:
        keys = [
            record.source_account_id,
            record.source_account_name,
            f"{record.source.source_system}:{record.source_account_id}",
            f"{record.source.source_system}:{record.source_account_name}",
        ]
        for key in keys:
            if key in overrides:
                return overrides[key]
        return None

    def _apply_override(
        self,
        record: SourceRecord,
        override: str | MappingOverride,
    ) -> MappedFinancialRecord:
        override_model = (
            override if isinstance(override, MappingOverride) else MappingOverride(account_id=override)
        )
        account = self.ontology.get_account(override_model.account_id)
        diagnostics = []
        if account is None:
            diagnostics.append(
                MappingDiagnostic(
                    code="invalid_override",
                    message=f"Override account {override_model.account_id!r} is not in the ontology.",
                )
            )
        return MappedFinancialRecord(
            source_record=record,
            account_id=account.id if account else override_model.account_id,
            account_name=account.name if account else None,
            status=MappingStatus.OVERRIDDEN,
            confidence=1.0 if account else 0.0,
            diagnostics=diagnostics,
            override_note=override_model.note,
        )


def source_record_from_dict(data: dict[str, Any], source_system: str) -> SourceRecord:
    """Create a source record from a fixture dictionary."""
    return SourceRecord(
        source_account_id=str(data.get("source_account_id") or data.get("account_id") or data["name"]),
        source_account_name=str(data.get("source_account_name") or data.get("name") or data["account_id"]),
        amount=Decimal(str(data["amount"])),
        period_label=str(data["period"]),
        statement=data.get("statement"),
        source_account_type=data.get("source_account_type") or data.get("account_type"),
        unit=str(data.get("unit", "USD")),
        source=SourceReference(
            source_system=source_system,
            source_id=str(data.get("source_id") or data.get("id") or data.get("account_id") or data["name"]),
            source_label=str(data.get("source_label") or data.get("name") or data.get("account_id")),
            metadata=dict(data.get("metadata", {})),
        ),
        metadata={key: value for key, value in data.items() if key not in {"amount"}},
    )
