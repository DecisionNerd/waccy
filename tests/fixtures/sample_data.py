"""Sample data fixtures for testing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from waccy.core.models import ExtractedData, ExtractedTransaction, PeriodType, ReportingPeriod


def sample_transaction() -> ExtractedTransaction:
    """Create a sample transaction for testing."""
    return ExtractedTransaction(
        date=date(2024, 1, 15),
        account_id="revenue-001",
        amount=Decimal("1000.00"),
        description="Product sale",
        source_id="txn-001",
        confidence=0.95,
    )


def sample_extracted_data() -> ExtractedData:
    """Create sample extracted data for testing."""
    return ExtractedData(
        transactions=[sample_transaction()],
        accounts=[],
        metadata={"source": "test"},
        quality_score=0.9,
    )


def sample_periods() -> list[ReportingPeriod]:
    """Create annual fixture periods."""
    return [
        ReportingPeriod(
            label="2023",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            period_type=PeriodType.YEAR,
        ),
        ReportingPeriod(
            label="2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            period_type=PeriodType.YEAR,
        ),
    ]


def sample_qbo_fixture() -> dict[str, Any]:
    """Create a balanced QBO-like fixture."""
    return {
        "entity_name": "Fixture Co",
        "periods": [
            {"label": "2023", "start_date": "2023-01-01", "end_date": "2023-12-31"},
            {"label": "2024", "start_date": "2024-01-01", "end_date": "2024-12-31"},
        ],
        "records": _records(
            names={
                "revenue": "Sales",
                "cogs": "Cost of Goods Sold",
                "opex": "Operating Expenses",
                "da": "Depreciation",
                "interest": "Interest Expense",
                "tax": "Income Tax Expense",
                "cash": "Checking",
                "ar": "Accounts Receivable",
                "inventory": "Inventory",
                "ppe": "Fixed Assets",
                "acc_dep": "Accumulated Depreciation",
                "ap": "Accounts Payable",
                "accrued": "Accrued Expenses",
                "debt": "Notes Payable",
                "equity": "Owners Equity",
                "retained": "Retained Earnings",
                "da_addback": "Depreciation Addback",
                "wc": "Change in Working Capital",
                "capex": "Capital Expenditures",
                "financing": "Debt Proceeds",
            }
        ),
    }


def sample_edgar_fixture() -> dict[str, Any]:
    """Create a balanced EDGAR/XBRL-like fixture."""
    return {
        "entity_name": "Fixture Co",
        "cik": "0000000000",
        "periods": [
            {"label": "2023", "start_date": "2023-01-01", "end_date": "2023-12-31"},
            {"label": "2024", "start_date": "2024-01-01", "end_date": "2024-12-31"},
        ],
        "records": _records(
            names={
                "revenue": "us-gaap:Revenues",
                "cogs": "us-gaap:CostOfRevenue",
                "opex": "us-gaap:SellingGeneralAndAdministrativeExpense",
                "da": "us-gaap:DepreciationDepletionAndAmortization",
                "interest": "us-gaap:InterestExpense",
                "tax": "us-gaap:IncomeTaxExpenseBenefit",
                "cash": "us-gaap:CashAndCashEquivalentsAtCarryingValue",
                "ar": "us-gaap:AccountsReceivableNetCurrent",
                "inventory": "us-gaap:InventoryNet",
                "ppe": "us-gaap:PropertyPlantAndEquipmentNet",
                "acc_dep": "us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
                "ap": "us-gaap:AccountsPayableCurrent",
                "accrued": "us-gaap:AccruedLiabilitiesCurrent",
                "debt": "us-gaap:LongTermDebtNoncurrent",
                "equity": "us-gaap:StockholdersEquity",
                "retained": "us-gaap:RetainedEarningsAccumulatedDeficit",
                "da_addback": "Depreciation And Amortization",
                "wc": "Changes In Operating Assets And Liabilities",
                "capex": "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                "financing": "us-gaap:ProceedsFromIssuanceOfLongTermDebt",
            }
        ),
    }


def _records(names: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    records.extend(
        [
            _record(names["revenue"], "2023", 1000, "income_statement"),
            _record(names["cogs"], "2023", 400, "income_statement"),
            _record(names["opex"], "2023", 200, "income_statement"),
            _record(names["da"], "2023", 50, "income_statement"),
            _record(names["interest"], "2023", 20, "income_statement"),
            _record(names["tax"], "2023", 66, "income_statement"),
            _record(names["revenue"], "2024", 1200, "income_statement"),
            _record(names["cogs"], "2024", 480, "income_statement"),
            _record(names["opex"], "2024", 240, "income_statement"),
            _record(names["da"], "2024", 60, "income_statement"),
            _record(names["interest"], "2024", 25, "income_statement"),
            _record(names["tax"], "2024", 79, "income_statement"),
        ]
    )
    records.extend(
        [
            _record(names["cash"], "2023", 100, "balance_sheet"),
            _record(names["ar"], "2023", 150, "balance_sheet"),
            _record(names["inventory"], "2023", 100, "balance_sheet"),
            _record(names["ppe"], "2023", 500, "balance_sheet"),
            _record(names["acc_dep"], "2023", 50, "balance_sheet"),
            _record(names["ap"], "2023", 120, "balance_sheet"),
            _record(names["accrued"], "2023", 80, "balance_sheet"),
            _record(names["debt"], "2023", 300, "balance_sheet"),
            _record(names["equity"], "2023", 36, "balance_sheet"),
            _record(names["retained"], "2023", 264, "balance_sheet"),
            _record(names["cash"], "2024", 380, "balance_sheet"),
            _record(names["ar"], "2024", 180, "balance_sheet"),
            _record(names["inventory"], "2024", 120, "balance_sheet"),
            _record(names["ppe"], "2024", 600, "balance_sheet"),
            _record(names["acc_dep"], "2024", 110, "balance_sheet"),
            _record(names["ap"], "2024", 140, "balance_sheet"),
            _record(names["accrued"], "2024", 90, "balance_sheet"),
            _record(names["debt"], "2024", 354, "balance_sheet"),
            _record(names["equity"], "2024", 270, "balance_sheet"),
            _record(names["retained"], "2024", 316, "balance_sheet"),
        ]
    )
    records.extend(
        [
            _record(names["da_addback"], "2024", 60, "cash_flow_statement"),
            _record(names["wc"], "2024", -50, "cash_flow_statement"),
            _record(names["capex"], "2024", -100, "cash_flow_statement"),
            _record(names["financing"], "2024", 54, "cash_flow_statement"),
        ]
    )
    return records


def _record(name: str, period: str, amount: int, statement: str) -> dict[str, Any]:
    return {
        "source_account_id": name,
        "source_account_name": name,
        "name": name,
        "period": period,
        "amount": amount,
        "statement": statement,
    }
