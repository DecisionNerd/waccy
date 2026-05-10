"""Coverage for small support modules and edge branches."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from tests.fixtures.sample_data import sample_extracted_data, sample_periods, sample_qbo_fixture
from waccy.classification import ClassificationEngine, ConfidenceScorer, PatternMatcher
from waccy.cli import main
from waccy.core.models import (
    ExtractedData,
    IssueSeverity,
    MappedFinancialDataset,
    MappedFinancialRecord,
    MappingStatus,
    PeriodType,
    ReportingPeriod,
    SourceRecord,
    SourceReference,
    ValidatedFinancialDataset,
    ValidationIssue,
)
from waccy.core.ontology import AccountType, StandardChartOfAccounts
from waccy.core.validation import validate_extracted_data
from waccy.extraction.base import Extractor
from waccy.extraction.mapper import DataMapper, source_record_from_dict
from waccy.extraction.registry import ExtractorRegistry
from waccy.modeling import ModelBuilder, ModelTemplate
from waccy.utils import (
    format_currency,
    format_date,
    format_percentage,
    generate_reporting_periods,
    infer_reporting_period,
    parse_date_range,
)
from waccy.utils.dates import validate_date_range as validate_date_range_util
from waccy.utils.validation import validate_amount

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_placeholder_returns_success(capsys: pytest.CaptureFixture[str]) -> None:
    """The placeholder CLI exits successfully and prints API guidance."""
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "WACCY CLI" in output
    assert "ModelBuilder" in output


def test_utils_parse_format_and_validate_values() -> None:
    """Utility helpers format and validate the simple supported cases."""
    assert parse_date_range(("2024-01-01", "2024-12-31")) == (
        date(2024, 1, 1),
        date(2024, 12, 31),
    )
    assert parse_date_range((date(2024, 1, 1), date(2024, 12, 31))) == (
        date(2024, 1, 1),
        date(2024, 12, 31),
    )
    assert parse_date_range("2024-01-01 to 2024-12-31") == (
        date(2024, 1, 1),
        date(2024, 12, 31),
    )
    assert parse_date_range("2024-01-01, 2024-03-31") == (
        date(2024, 1, 1),
        date(2024, 3, 31),
    )
    assert parse_date_range("2024-01-01|2024-03-31") == (
        date(2024, 1, 1),
        date(2024, 3, 31),
    )
    assert format_date(date(2024, 1, 2)) == "2024-01-02"
    assert validate_date_range_util(date(2024, 1, 1), date(2024, 1, 2))
    assert format_currency(Decimal("1234.5")) == "USD 1,234.50"
    assert format_percentage(0.1234, decimals=1) == "12.3%"
    assert validate_amount(1.0)
    assert validate_amount(1)
    assert not validate_amount(float("nan"))
    with pytest.raises(ValueError, match="between ISO dates"):
        parse_date_range("2024-01-01 2024-12-31")
    with pytest.raises(ValueError, match="exactly two ISO dates"):
        parse_date_range(("2024-01-01", "2024-12-31", "2025-12-31"))
    with pytest.raises(ValueError, match="ISO format"):
        parse_date_range((date(2024, 1, 1), "2024-12-31"))
    with pytest.raises(ValueError, match="on or before"):
        parse_date_range("2024-12-31 to 2024-01-01")


def test_reporting_period_generation_and_label_inference() -> None:
    """Date utilities generate deterministic model periods."""
    quarters = generate_reporting_periods("2024-02-01 to 2024-08-15", PeriodType.QUARTER)
    months = generate_reporting_periods(("2024-01-15", "2024-03-10"), PeriodType.MONTH)
    years = generate_reporting_periods("2023-04-01 to 2024-03-31", PeriodType.YEAR)

    assert [period.label for period in quarters] == ["2024Q1", "2024Q2", "2024Q3"]
    assert quarters[0].start_date == date(2024, 2, 1)
    assert quarters[-1].end_date == date(2024, 8, 15)
    assert [period.label for period in months] == ["2024-01", "2024-02", "2024-03"]
    assert [period.label for period in years] == ["2023", "2024"]
    assert infer_reporting_period("2024").period_type == PeriodType.YEAR
    assert infer_reporting_period("2024Q2").start_date == date(2024, 4, 1)
    assert infer_reporting_period("2024-Q3").end_date == date(2024, 9, 30)
    assert infer_reporting_period("2024-2").end_date == date(2024, 2, 29)
    assert infer_reporting_period("202402").end_date == date(2024, 2, 29)
    assert infer_reporting_period("2024-02").period_type == PeriodType.MONTH
    with pytest.raises(ValueError, match="Unsupported reporting period"):
        infer_reporting_period("FY24")


def test_classification_and_pattern_matching_are_deterministic() -> None:
    """Classification uses ontology aliases, confidence scoring, and EDGAR patterns."""
    engine = ClassificationEngine(llm_provider="fixture")
    assert engine.llm_provider == "fixture"

    account, confidence = engine.classify_account("Sales", [], {"source_system": "qbo"})
    assert account.id == "revenue"
    assert confidence >= 0.8

    result = engine.classify_with_diagnostics("Mystery Account", [], {"source_system": "qbo"})
    assert result.status == MappingStatus.UNMAPPED
    assert result.confidence == 0.0

    scorer = ConfidenceScorer()
    assert scorer.calculate_confidence("Sales", "revenue", [], {}) > 0.0
    assert scorer.calculate_confidence("Unknown", "not-real", [], {}) == 0.0

    matcher = PatternMatcher()
    patterns = matcher.extract_patterns(
        {
            "records": [
                {
                    "concept": "us-gaap:Revenues",
                    "statement": "income_statement",
                }
            ]
        }
    )
    assert patterns["aliases"]
    assert matcher.match_pattern("us-gaap:Revenues", [])["account_id"] == "revenue"

    engine.learn_from_edgar(
        {
            "records": [
                {
                    "concept": "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                    "statement": "cash_flow_statement",
                }
            ]
        }
    )
    pattern_result = engine.classify_with_diagnostics(
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        [],
        {"source_system": "edgar"},
    )
    assert pattern_result.account_id == "capex"
    assert "classified_by_edgar_pattern" in pattern_result.diagnostics


def test_model_template_placeholder_contract() -> None:
    """ModelTemplate keeps placeholder structure behavior explicit."""
    template = ModelTemplate("three_statement")
    assert template.model_type == "three_statement"
    assert template.get_structure() == {}
    assert template.apply_template({"value": 1}) == {}


def test_extractors_registry_and_base_validation() -> None:
    """Registry registration and base validation work without installed extensions."""

    class FixtureExtractor(Extractor):
        @property
        def name(self) -> str:
            return "Fixture"

        @property
        def data_source(self) -> str:
            return "fixture"

        def authenticate(self, credentials: dict[str, str]) -> bool:
            return bool(credentials)

        def extract(self, config: dict[str, object]) -> ExtractedData:
            return ExtractedData(metadata={"config": config})

    registry = ExtractorRegistry()
    registry.register_extractor("fixture", FixtureExtractor)

    assert registry.get_extractor("fixture") is FixtureExtractor
    assert "fixture" in registry.list_extractors()
    assert registry.get_extractor("missing") is None
    assert FixtureExtractor().validate(sample_extracted_data())
    assert not validate_extracted_data(ExtractedData())


def test_quality_report_covers_empty_and_partial_legacy_transactions() -> None:
    """Quality reports surface empty datasets and partially mapped transactions."""
    empty_report = ExtractedData().generate_quality_report()
    assert empty_report["completeness"] == 0.0
    assert empty_report["avg_confidence"] == 1.0
    assert empty_report["issues"] == ["No source records or transactions were extracted."]

    extracted = sample_extracted_data().model_copy(deep=True)
    extracted.transactions[0].account_id = ""
    report = extracted.generate_quality_report()

    assert report["completeness"] == 1.0
    assert report["avg_confidence"] == 0.95
    assert "Some transactions are missing account mappings." in report["issues"]


def test_ontology_filters_accounts_and_handles_missing_mappings() -> None:
    """Ontology filtering and missing lookup branches are covered."""
    ontology = StandardChartOfAccounts()

    assert ontology.map_account("not a real account", "qbo") is None
    assert ontology.get_account("not-real") is None
    assert all(account.type == AccountType.ASSET for account in ontology.list_accounts(AccountType.ASSET))


def test_mapper_creates_periods_for_legacy_transactions_and_handles_missing_names() -> None:
    """The mapper supports transaction-only compatibility and sparse fixture dicts."""
    normalized = DataMapper().normalize(sample_extracted_data())
    assert [period.label for period in normalized.periods] == ["2024"]
    assert normalized.records[0].source_account_id == "revenue-001"

    record = source_record_from_dict({"account_id": "Sales", "period": "2024", "amount": 10}, "qbo")
    assert record.source_account_id == "Sales"
    assert record.source_account_name == "Sales"


def test_validation_branches_for_period_ranges_and_empty_dataset() -> None:
    """Validation reports invalid periods and empty mapped datasets."""
    bad_period = ReportingPeriod(
        label="bad",
        start_date=date(2024, 12, 31),
        end_date=date(2024, 1, 1),
    )
    mapped = MappedFinancialDataset(entity_name="Fixture", periods=[bad_period], records=[])
    validated = DataMapper().validate(mapped)
    issue_codes = {issue.code for issue in validated.issues}

    assert {"invalid_period_range", "empty_dataset"}.issubset(issue_codes)
    assert not validated.is_valid


def test_validation_reports_mapped_records_without_account_ids() -> None:
    """Validation rejects mapped statuses that lack canonical account IDs."""
    source = SourceRecord(
        source_account_id="sales",
        source_account_name="Sales",
        amount=Decimal("1"),
        period_label="2024",
        source=SourceReference(source_system="qbo", source_id="sales", source_label="Sales"),
    )
    mapped = MappedFinancialDataset(
        entity_name="Fixture",
        periods=[sample_periods()[1]],
        records=[
            MappedFinancialRecord(
                source_record=source,
                status=MappingStatus.MAPPED,
                confidence=0.95,
            )
        ],
    )
    validated = DataMapper().validate(mapped)
    issue_codes = {issue.code for issue in validated.issues}

    assert "missing_mapped_account_id" in issue_codes
    assert "mapping_overridden" not in issue_codes
    assert not validated.is_valid


def test_model_builder_accepts_validated_and_mapped_inputs(tmp_path: Path) -> None:
    """ModelBuilder handles all public input layers and export helper."""
    fixture = sample_qbo_fixture()
    extracted = ExtractedData(
        entity_name="Fixture Co",
        periods=sample_periods(),
        source_records=[source_record_from_dict(record, "qbo") for record in fixture["records"]],
        metadata={"source": "qbo"},
    )
    validated = DataMapper().map_to_standard(extracted)
    builder = ModelBuilder()

    mapped_model = builder.build_three_statement_model(validated.mapped_dataset)
    validated_model = builder.build_three_statement_model(validated)
    output_path = tmp_path / "model.xlsx"
    builder.export_to_sheets(mapped_model, str(output_path))

    assert mapped_model.entity_name == "Fixture Co"
    assert validated_model.entity_name == "Fixture Co"
    assert output_path.exists()
    with pytest.raises(NotImplementedError):
        builder.build_dcf_model(mapped_model, 0.1, 0.03, 10.0)


def test_model_builder_reports_missing_required_statement_line() -> None:
    """Missing computed statement lines fail loudly through public model building."""
    fixture = sample_qbo_fixture()
    extracted = ExtractedData(
        entity_name="Fixture Co",
        periods=sample_periods(),
        source_records=[source_record_from_dict(record, "qbo") for record in fixture["records"]],
        metadata={"source": "qbo"},
    )

    class BrokenModelBuilder(ModelBuilder):
        def _build_income_statement_lines(
            self,
            records: list[MappedFinancialRecord],
            period_labels: list[str],
        ) -> list:
            del records, period_labels
            return []

    with pytest.raises(ValueError, match="Missing statement line"):
        BrokenModelBuilder().build_three_statement_model(extracted)


def test_validated_dataset_is_invalid_when_error_issue_exists() -> None:
    """Validated datasets distinguish warning/info issues from errors."""
    source = SourceRecord(
        source_account_id="sales",
        source_account_name="Sales",
        amount=Decimal("1"),
        period_label="2024",
        source=SourceReference(source_system="qbo", source_id="sales", source_label="Sales"),
    )
    mapped = DataMapper().map_dataset(
        DataMapper().normalize(
            ExtractedData(
                entity_name="Fixture",
                periods=sample_periods(),
                source_records=[source],
            )
        )
    )
    warning_only = ValidatedFinancialDataset(
        mapped_dataset=mapped,
        issues=[ValidationIssue(code="warning", message="warning", severity=IssueSeverity.WARNING)],
    )
    error = ValidatedFinancialDataset(
        mapped_dataset=mapped,
        issues=[ValidationIssue(code="error", message="error", severity=IssueSeverity.ERROR)],
    )

    assert warning_only.is_valid
    assert not error.is_valid
