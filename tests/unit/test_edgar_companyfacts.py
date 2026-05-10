"""Tests for EDGAR companyfacts normalization."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from waccy.core.models import IssueSeverity
from waccy.extraction.mapper import DataMapper
from waccy.modeling.builder import ModelBuilder

ROOT = Path(__file__).resolve().parents[2]
EDGAR_SRC = ROOT / "extensions" / "waccy-edgar" / "src"
sys.path.insert(0, str(EDGAR_SRC))

from waccy_edgar import EdgarCompanyFactsNormalizer, EdgarExtractor  # noqa: E402


def test_companyfacts_normalizer_selects_annual_10k_fiscal_periods() -> None:
    """Companyfacts normalization preserves FY labels and instant-fact provenance."""
    fixture = EdgarCompanyFactsNormalizer().to_fixture(_companyfacts_fixture(), periods=2)

    assert fixture["entity_name"] == "Fixture Public Co"
    assert [period["label"] for period in fixture["periods"]] == ["FY2024", "FY2025"]
    fy2025 = fixture["periods"][1]
    assert fy2025["start_date"] == "2024-07-01"
    assert fy2025["end_date"] == "2025-06-30"
    cash_record = next(
        record
        for record in fixture["records"]
        if record["source_account_name"]
        == "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
        and record["period"] == "FY2025"
    )
    assert cash_record["statement"] == "balance_sheet"
    assert cash_record["metadata"]["is_instant"]
    assert cash_record["metadata"]["end"] == "2025-06-30"


def test_companyfacts_normalizer_builds_model_with_aliases_and_diagnostics() -> None:
    """Normalized EDGAR companyfacts can map and build an inspectable model."""
    fixture = EdgarCompanyFactsNormalizer().to_fixture(_companyfacts_fixture(), periods=2)
    model = ModelBuilder().build_three_statement_model(EdgarExtractor().extract({"fixture": fixture}))
    issue_codes = {issue.code for issue in model.validation_issues}

    assert "unmapped_account" not in issue_codes
    assert "edgar_missing_expected_concept" in issue_codes
    assert any(issue.severity == IssueSeverity.WARNING for issue in model.validation_issues)
    assert all(
        issue.severity == IssueSeverity.WARNING
        for issue in model.validation_issues
        if issue.code == "balance_sheet_imbalance"
    )
    net_income = next(
        line for line in model.income_statement.lines if line.label == "Net Income"
    )
    assert net_income.values["FY2025"] == Decimal("316")


def test_edgar_live_smoke_aliases_map_with_statement_context() -> None:
    """EDGAR aliases surfaced by live companyfacts smoke resolve deterministically."""
    mapper = DataMapper()
    extracted = EdgarExtractor().extract(
        {
            "fixture": {
                "entity_name": "Alias Co",
                "periods": [
                    {"label": "FY2025", "start_date": "2024-01-01", "end_date": "2024-12-31"}
                ],
                "records": [
                    _record("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "income_statement"),
                    _record("us-gaap:CostOfGoodsAndServicesSold", "income_statement"),
                    _record("us-gaap:OperatingExpenses", "income_statement"),
                    _record("us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "balance_sheet"),
                    _record("us-gaap:AccruedIncomeTaxesCurrent", "balance_sheet"),
                    _record("us-gaap:LongTermDebtAndFinanceLeaseObligationsCurrent", "balance_sheet"),
                    _record("us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "balance_sheet"),
                    _record("us-gaap:ProceedsFromIssuanceOfDebt", "cash_flow_statement"),
                    _record("us-gaap:DepreciationDepletionAndAmortizationExpense", "cash_flow_statement"),
                ],
            }
        }
    )

    mapped = mapper.map_dataset(mapper.normalize(extracted))
    statuses = {record.source_record.source_account_name: record.account_id for record in mapped.records}

    assert statuses["us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"] == "revenue"
    assert statuses["us-gaap:CostOfGoodsAndServicesSold"] == "cogs"
    assert statuses["us-gaap:OperatingExpenses"] == "operating_expenses"
    assert statuses["us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"] == "cash"
    assert statuses["us-gaap:AccruedIncomeTaxesCurrent"] == "accrued_expenses"
    assert statuses["us-gaap:LongTermDebtAndFinanceLeaseObligationsCurrent"] == "debt"
    assert (
        statuses["us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
        == "equity"
    )
    assert statuses["us-gaap:ProceedsFromIssuanceOfDebt"] == "financing_movement"
    assert statuses["us-gaap:DepreciationDepletionAndAmortizationExpense"] == "depreciation_addback"


def _record(name: str, statement: str) -> dict[str, object]:
    return {
        "source_account_id": name,
        "source_account_name": name,
        "name": name,
        "period": "FY2025",
        "amount": "1",
        "statement": statement,
    }


def _companyfacts_fixture() -> dict[str, object]:
    concepts = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": [1000, 1200],
        "CostOfGoodsAndServicesSold": [400, 480],
        "OperatingExpenses": [200, 240],
        "DepreciationDepletionAndAmortizationExpense": [50, 60],
        "InterestExpenseNonOperating": [20, 25],
        "IncomeTaxExpenseBenefit": [66, 79],
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": [100, 380],
        "InventoryNet": [100, 120],
        "PropertyPlantAndEquipmentNet": [500, 600],
        "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment": [50, 110],
        "AccountsPayableCurrent": [120, 140],
        "AccruedIncomeTaxesCurrent": [80, 90],
        "LongTermDebtAndFinanceLeaseObligationsCurrent": [300, 354],
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": [36, 270],
        "RetainedEarningsAccumulatedDeficit": [264, 316],
        "NetIncomeLoss": [264, 316],
        "IncreaseDecreaseInOperatingAssetsAndLiabilitiesNetOfAcquisitions": [-20, -50],
        "PaymentsToAcquirePropertyPlantAndEquipment": [-100, -100],
        "ProceedsFromIssuanceOfDebt": [70, 54],
    }
    facts = {
        concept: {"label": concept, "units": {"USD": _facts(values, instant=_is_instant(concept))}}
        for concept, values in concepts.items()
    }
    return {
        "cik": 123456,
        "entityName": "Fixture Public Co",
        "facts": {"us-gaap": facts},
    }


def _facts(values: list[int], *, instant: bool) -> list[dict[str, object]]:
    periods = [
        (2024, "2023-07-01", "2024-06-30", values[0]),
        (2025, "2024-07-01", "2025-06-30", values[1]),
    ]
    facts: list[dict[str, object]] = []
    for fiscal_year, start, end, value in periods:
        fact = {
            "accn": f"000-fixture-{fiscal_year}",
            "end": end,
            "filed": f"{fiscal_year}-08-01",
            "form": "10-K",
            "fp": "FY",
            "fy": fiscal_year,
            "val": value,
        }
        if not instant:
            fact["start"] = start
        facts.append(fact)
    return facts


def _is_instant(concept: str) -> bool:
    return concept in {
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "AccountsReceivableNetCurrent",
        "InventoryNet",
        "PropertyPlantAndEquipmentNet",
        "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
        "AccountsPayableCurrent",
        "AccruedIncomeTaxesCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "RetainedEarningsAccumulatedDeficit",
    }
