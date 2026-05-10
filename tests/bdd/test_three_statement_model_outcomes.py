"""Outcome-oriented BDD specs for the v0.1.0 financial model slice."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from tests.fixtures.sample_data import sample_edgar_fixture, sample_periods, sample_qbo_fixture
from waccy.core.models import ExtractedData, IssueSeverity, StatementLine, ThreeStatementModel
from waccy.extraction.mapper import source_record_from_dict
from waccy.modeling.builder import ModelBuilder

scenarios("three_statement_model.feature")


@given(parsers.parse("a balanced {source_name} financial fixture"), target_fixture="source_fixture")
def balanced_financial_fixture(source_name: str) -> dict[str, Any]:
    """Provide a source-specific fixture by source name."""
    source_key = source_name.lower()
    if source_key == "qbo":
        return {"source": "qbo", "fixture": sample_qbo_fixture()}
    if source_key == "edgar":
        return {"source": "edgar", "fixture": sample_edgar_fixture()}
    raise AssertionError(f"Unsupported source fixture {source_name!r}")


@when("I build the v0.1.0 workbook model", target_fixture="workbook_model")
def build_v010_workbook_model(source_fixture: dict[str, Any]) -> ThreeStatementModel:
    """Build the workbook-ready model from a source fixture."""
    fixture = source_fixture["fixture"]
    source = source_fixture["source"]
    extracted = ExtractedData(
        entity_name=str(fixture["entity_name"]),
        periods=sample_periods(),
        source_records=[source_record_from_dict(record, source) for record in fixture["records"]],
        metadata={"source": source},
    )
    return ModelBuilder().build_three_statement_model(extracted)


@then("the workbook has exactly the three expected statements")
def workbook_has_three_expected_statements(workbook_model: ThreeStatementModel) -> None:
    """Assert the model exposes only the expected v0.1.0 statements."""
    assert [
        workbook_model.income_statement.name,
        workbook_model.balance_sheet.name,
        workbook_model.cash_flow_statement.name,
    ] == ["Income Statement", "Balance Sheet", "Cash Flow Statement"]


@then(parsers.parse("the {period} income statement reports net income of {amount:d}"))
def income_statement_reports_net_income(
    workbook_model: ThreeStatementModel,
    period: str,
    amount: int,
) -> None:
    """Assert the income statement net income outcome."""
    assert _line_value(workbook_model.income_statement.lines, "Net Income", period) == Decimal(amount)


@then(parsers.parse("the {period} income statement reports revenue of {amount:d}"))
def income_statement_reports_revenue(
    workbook_model: ThreeStatementModel,
    period: str,
    amount: int,
) -> None:
    """Assert the income statement revenue outcome."""
    assert _line_value(workbook_model.income_statement.lines, "Revenue", period) == Decimal(amount)


@then(parsers.parse("the {period} balance sheet balance check is zero"))
def balance_sheet_balance_check_is_zero(workbook_model: ThreeStatementModel, period: str) -> None:
    """Assert the balance sheet check outcome."""
    assert _line_value(workbook_model.balance_sheet.lines, "Balance Check", period) == Decimal("0")


@then(parsers.parse("the {period} cash flow tie-out is zero"))
def cash_flow_tie_out_is_zero(workbook_model: ThreeStatementModel, period: str) -> None:
    """Assert the cash flow statement tie-out outcome."""
    assert _line_value(workbook_model.cash_flow_statement.lines, "Cash Flow Tie-Out", period) == Decimal(
        "0"
    )


@then("the model has no error-level validation issues")
def model_has_no_error_level_validation_issues(workbook_model: ThreeStatementModel) -> None:
    """Assert that validation did not produce blocking issues."""
    assert all(issue.severity != IssueSeverity.ERROR for issue in workbook_model.validation_issues)


def _line_value(lines: list[StatementLine], label: str, period: str) -> Decimal:
    for line in lines:
        if line.label == label:
            return line.values[period]
    raise AssertionError(f"Missing statement line {label!r}")
