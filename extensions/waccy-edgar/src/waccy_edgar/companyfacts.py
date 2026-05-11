"""Normalize SEC companyfacts payloads into WACCY EDGAR fixtures."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable


CONCEPT_SPECS = {
    "revenue": (
        "income_statement",
        ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"),
    ),
    "cogs": (
        "income_statement",
        (
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
        ),
    ),
    "operating_expenses": (
        "income_statement",
        ("OperatingExpenses", "SellingGeneralAndAdministrativeExpense"),
    ),
    "depreciation_amortization": (
        "income_statement",
        ("DepreciationDepletionAndAmortizationExpense", "DepreciationDepletionAndAmortization"),
    ),
    "interest_expense": ("income_statement", ("InterestExpense", "InterestExpenseNonOperating")),
    "tax_expense": ("income_statement", ("IncomeTaxExpenseBenefit",)),
    "cash": (
        "balance_sheet",
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
    ),
    "accounts_receivable": ("balance_sheet", ("AccountsReceivableNetCurrent",)),
    "inventory": ("balance_sheet", ("InventoryNet",)),
    "ppe": ("balance_sheet", ("PropertyPlantAndEquipmentNet",)),
    "accumulated_depreciation": (
        "balance_sheet",
        ("AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",),
    ),
    "accounts_payable": ("balance_sheet", ("AccountsPayableCurrent",)),
    "accrued_expenses": ("balance_sheet", ("AccruedLiabilitiesCurrent", "AccruedIncomeTaxesCurrent")),
    "debt": (
        "balance_sheet",
        (
            "LongTermDebtCurrent",
            "LongTermDebtNoncurrent",
            "LongTermDebtAndFinanceLeaseObligationsCurrent",
            "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        ),
    ),
    "equity": (
        "balance_sheet",
        ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    ),
    "retained_earnings": ("balance_sheet", ("RetainedEarningsAccumulatedDeficit",)),
    "net_income": ("cash_flow_statement", ("NetIncomeLoss",)),
    "depreciation_addback": (
        "cash_flow_statement",
        ("DepreciationDepletionAndAmortizationExpense", "DepreciationDepletionAndAmortization"),
    ),
    "working_capital_movement": ("cash_flow_statement", ("IncreaseDecreaseInOperatingAssetsAndLiabilitiesNetOfAcquisitions", "NetCashProvidedByUsedInOperatingActivities")),
    "capex": ("cash_flow_statement", ("PaymentsToAcquirePropertyPlantAndEquipment",)),
    "financing_movement": (
        "cash_flow_statement",
        ("ProceedsFromIssuanceOfDebt", "ProceedsFromIssuanceOfLongTermDebt", "RepaymentsOfDebt"),
    ),
}


class EdgarCompanyFactsNormalizer:
    """Convert SEC companyfacts JSON into EDGAR fixture records."""

    def to_fixture(
        self,
        companyfacts: dict[str, Any],
        *,
        periods: int = 4,
        taxonomy: str = "us-gaap",
    ) -> dict[str, Any]:
        """Return an ``EdgarExtractor`` fixture from a companyfacts payload."""
        if not isinstance(periods, int) or periods <= 0:
            raise ValueError("EDGAR companyfacts periods must be a positive integer.")
        facts = companyfacts.get("facts", {}).get(taxonomy)
        if not isinstance(facts, dict):
            raise ValueError(f"Companyfacts payload is missing facts.{taxonomy}.")

        target_years = self._target_fiscal_years(facts, periods=periods)
        target_period_labels = [f"FY{year}" for year in sorted(target_years)]
        selected: list[dict[str, Any]] = []
        source_issues: list[dict[str, Any]] = []
        for canonical_account, (statement, concepts) in CONCEPT_SPECS.items():
            fact = self._select_fact(facts, concepts, target_years=target_years)
            if fact is None:
                source_issues.append(
                    {
                        "code": "edgar_missing_expected_concept",
                        "message": (
                            f"No annual 10-K companyfacts concept found for {canonical_account}."
                        ),
                        "severity": "warning",
                        "source": "edgar",
                        "issue_type": "partial_extraction",
                        "account_id": canonical_account,
                        "period_labels": target_period_labels,
                    }
                )
                continue
            selected.extend(
                self._record_from_fact(
                    canonical_account=canonical_account,
                    statement=statement,
                    concept=concept,
                    fact=item,
                )
                for concept, item in fact
            )

        periods_by_label = self._periods_from_records(selected)
        return {
            "entity_name": str(companyfacts.get("entityName", "EDGAR Entity")),
            "cik": str(companyfacts.get("cik", "")),
            "periods": [periods_by_label[label] for label in sorted(periods_by_label)],
            "records": selected,
            "metadata": {
                "source": "edgar",
                "mode": "companyfacts_normalized",
                "taxonomy": taxonomy,
                "edgar_source_issues": source_issues,
            },
        }

    def _select_fact(
        self,
        facts: dict[str, Any],
        concepts: Iterable[str],
        *,
        target_years: set[int],
    ) -> list[tuple[str, dict[str, Any]]] | None:
        selected_by_year: dict[int, tuple[str, dict[str, Any]]] = {}
        for concept in concepts:
            concept_facts = facts.get(concept, {}).get("units", {}).get("USD", [])
            if not isinstance(concept_facts, list):
                continue
            annual_facts = [
                fact
                for fact in concept_facts
                if isinstance(fact, dict)
                and fact.get("form") == "10-K"
                and fact.get("fp") == "FY"
                and fact.get("fy") is not None
                and int(fact["fy"]) in target_years
                and fact.get("end") is not None
                and fact.get("val") is not None
            ]
            selected = self._latest_by_fiscal_year(annual_facts)
            for fact in selected:
                fiscal_year = int(fact["fy"])
                selected_by_year.setdefault(fiscal_year, (concept, fact))
        if not selected_by_year:
            return None
        return [selected_by_year[year] for year in sorted(selected_by_year)]

    def _target_fiscal_years(self, facts: dict[str, Any], *, periods: int) -> set[int]:
        fiscal_years: set[int] = set()
        for concept_data in facts.values():
            if not isinstance(concept_data, dict):
                continue
            for unit_facts in concept_data.get("units", {}).values():
                if not isinstance(unit_facts, list):
                    continue
                for fact in unit_facts:
                    if (
                        isinstance(fact, dict)
                        and fact.get("form") == "10-K"
                        and fact.get("fp") == "FY"
                        and fact.get("fy") is not None
                    ):
                        fiscal_years.add(int(fact["fy"]))
        years = sorted(fiscal_years)
        last_n = min(len(years), periods)
        return set(years[-last_n:])

    def _latest_by_fiscal_year(self, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_year: dict[int, dict[str, Any]] = {}
        for fact in sorted(
            facts,
            key=lambda item: (
                int(item.get("fy", 0)),
                str(item.get("filed", "")),
                str(item.get("accn", "")),
            ),
        ):
            by_year[int(fact["fy"])] = fact
        return [by_year[year] for year in sorted(by_year)]

    def _record_from_fact(
        self,
        *,
        canonical_account: str,
        statement: str,
        concept: str,
        fact: dict[str, Any],
    ) -> dict[str, Any]:
        period_label = f"FY{fact['fy']}"
        return {
            "source_account_id": f"us-gaap:{concept}",
            "source_account_name": f"us-gaap:{concept}",
            "name": f"us-gaap:{concept}",
            "period": period_label,
            "amount": str(fact["val"]),
            "statement": statement,
            "unit": "USD",
            "metadata": {
                "canonical_account_hint": canonical_account,
                "concept": concept,
                "accession": fact.get("accn"),
                "filed": fact.get("filed"),
                "form": fact.get("form"),
                "fp": fact.get("fp"),
                "fy": fact.get("fy"),
                "frame": fact.get("frame"),
                "start": fact.get("start"),
                "end": fact.get("end"),
                "is_instant": "start" not in fact,
            },
        }

    def _periods_from_records(self, records: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
        periods: dict[str, dict[str, str]] = {}
        for record in records:
            metadata = record["metadata"]
            label = str(record["period"])
            end_date = date.fromisoformat(str(metadata["end"]))
            start_raw = metadata.get("start")
            start_date = date.fromisoformat(str(start_raw)) if start_raw else end_date
            existing = periods.get(label)
            if existing is None:
                periods[label] = {
                    "label": label,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_type": "year",
                }
                continue
            if start_date < date.fromisoformat(existing["start_date"]):
                existing["start_date"] = start_date.isoformat()
            if end_date > date.fromisoformat(existing["end_date"]):
                existing["end_date"] = end_date.isoformat()
        return periods
