"""Build financial models from validated WACCY financial datasets."""

from __future__ import annotations

from collections.abc import Callable, Iterable  # noqa: TC003
from decimal import Decimal
from typing import NoReturn

from waccy.core.models import (
    ExtractedData,
    FinancialStatement,
    IssueSeverity,
    MappedFinancialDataset,
    MappedFinancialRecord,
    StatementLine,
    ThreeStatementModel,
    ValidatedFinancialDataset,
    ValidationIssue,
)
from waccy.core.ontology import StandardChartOfAccounts
from waccy.core.validation import validate_mapped_dataset
from waccy.extraction.mapper import DataMapper
from waccy.modeling.exporters import SheetExporter

ZERO = Decimal("0")


class ModelBuilder:
    """Build financial models from normalized and validated financial data."""

    def __init__(self) -> None:
        """Initialize the model builder."""
        self.ontology = StandardChartOfAccounts()

    def build_three_statement_model(
        self,
        extracted_data: ExtractedData | MappedFinancialDataset | ValidatedFinancialDataset,
        forecast_periods: int = 0,
    ) -> ThreeStatementModel:
        """Build an integrated three-statement model."""
        del forecast_periods
        validated = self._ensure_validated(extracted_data)
        dataset = validated.mapped_dataset
        periods = dataset.periods
        period_labels = [period.label for period in periods]
        issues = list(validated.issues)

        income_lines = self._build_income_statement_lines(dataset.records, period_labels)
        balance_lines = self._build_balance_sheet_lines(dataset.records, period_labels)
        cash_flow_lines = self._build_cash_flow_lines(dataset.records, income_lines, balance_lines, period_labels)
        issues.extend(self._statement_issues(balance_lines, cash_flow_lines, period_labels))

        return ThreeStatementModel(
            entity_name=dataset.entity_name,
            periods=periods,
            income_statement=FinancialStatement(
                name="Income Statement",
                periods=periods,
                lines=income_lines,
            ),
            balance_sheet=FinancialStatement(
                name="Balance Sheet",
                periods=periods,
                lines=balance_lines,
            ),
            cash_flow_statement=FinancialStatement(
                name="Cash Flow Statement",
                periods=periods,
                lines=cash_flow_lines,
            ),
            validation_issues=issues,
            metadata=dataset.metadata,
        )

    def build_dcf_model(
        self,
        three_statement_model: ThreeStatementModel,
        wacc: float,
        terminal_growth_rate: float,
        exit_multiple: float,
    ) -> NoReturn:
        """Build DCF valuation model."""
        del three_statement_model, wacc, terminal_growth_rate, exit_multiple
        raise NotImplementedError("DCF model not yet implemented")

    def export_to_sheets(
        self,
        model: ThreeStatementModel,
        output_path: str,
    ) -> None:
        """Export model to spreadsheet output."""
        exporter = SheetExporter()
        exporter.export(model, output_path)

    def _ensure_validated(
        self,
        data: ExtractedData | MappedFinancialDataset | ValidatedFinancialDataset,
    ) -> ValidatedFinancialDataset:
        if isinstance(data, ValidatedFinancialDataset):
            return data
        if isinstance(data, MappedFinancialDataset):
            return validate_mapped_dataset(data)
        mapper = DataMapper(self.ontology)
        return mapper.map_to_standard(data)

    def _build_income_statement_lines(
        self,
        records: list[MappedFinancialRecord],
        period_labels: list[str],
    ) -> list[StatementLine]:
        revenue = self._line("Revenue", "revenue", records, period_labels)
        cogs = self._line("Cost of Goods Sold", "cogs", records, period_labels)
        opex = self._line("Operating Expenses", "operating_expenses", records, period_labels)
        da = self._line("Depreciation & Amortization", "depreciation_amortization", records, period_labels)
        interest = self._line("Interest Expense", "interest_expense", records, period_labels)
        taxes = self._line("Tax Expense", "tax_expense", records, period_labels)
        gross_profit = self._computed_line(
            "Gross Profit",
            period_labels,
            lambda period: revenue.values[period] - cogs.values[period],
        )
        operating_income = self._computed_line(
            "Operating Income",
            period_labels,
            lambda period: gross_profit.values[period] - opex.values[period] - da.values[period],
        )
        pretax_income = self._computed_line(
            "Pre-Tax Income",
            period_labels,
            lambda period: operating_income.values[period] - interest.values[period],
        )
        net_income = self._computed_line(
            "Net Income",
            period_labels,
            lambda period: pretax_income.values[period] - taxes.values[period],
        )
        return [
            revenue,
            cogs,
            gross_profit,
            opex,
            da,
            operating_income,
            interest,
            pretax_income,
            taxes,
            net_income,
        ]

    def _build_balance_sheet_lines(
        self,
        records: list[MappedFinancialRecord],
        period_labels: list[str],
    ) -> list[StatementLine]:
        cash = self._line("Cash", "cash", records, period_labels)
        ar = self._line("Accounts Receivable", "accounts_receivable", records, period_labels)
        inventory = self._line("Inventory", "inventory", records, period_labels)
        ppe = self._line("Property, Plant & Equipment", "ppe", records, period_labels)
        accumulated_depreciation = self._line(
            "Accumulated Depreciation",
            "accumulated_depreciation",
            records,
            period_labels,
        )
        ap = self._line("Accounts Payable", "accounts_payable", records, period_labels)
        accrued = self._line("Accrued Expenses", "accrued_expenses", records, period_labels)
        debt = self._line("Debt", "debt", records, period_labels)
        equity = self._line("Equity", "equity", records, period_labels)
        retained_earnings = self._line("Retained Earnings", "retained_earnings", records, period_labels)
        total_assets = self._computed_line(
            "Total Assets",
            period_labels,
            lambda period: cash.values[period]
            + ar.values[period]
            + inventory.values[period]
            + ppe.values[period]
            - accumulated_depreciation.values[period],
        )
        total_liabilities = self._computed_line(
            "Total Liabilities",
            period_labels,
            lambda period: ap.values[period] + accrued.values[period] + debt.values[period],
        )
        total_equity = self._computed_line(
            "Total Equity",
            period_labels,
            lambda period: equity.values[period] + retained_earnings.values[period],
        )
        balance_check = self._computed_line(
            "Balance Check",
            period_labels,
            lambda period: total_assets.values[period]
            - total_liabilities.values[period]
            - total_equity.values[period],
            is_check=True,
        )
        return [
            cash,
            ar,
            inventory,
            ppe,
            accumulated_depreciation,
            total_assets,
            ap,
            accrued,
            debt,
            total_liabilities,
            equity,
            retained_earnings,
            total_equity,
            balance_check,
        ]

    def _build_cash_flow_lines(
        self,
        records: list[MappedFinancialRecord],
        income_lines: list[StatementLine],
        balance_lines: list[StatementLine],
        period_labels: list[str],
    ) -> list[StatementLine]:
        income_net_income = self._find_line(income_lines, "Net Income")
        bs_cash = self._find_line(balance_lines, "Cash")
        net_income = self._line("Net Income", "net_income", records, period_labels)
        if all(value == ZERO for value in net_income.values.values()):
            net_income = StatementLine(label="Net Income", values=dict(income_net_income.values))
        da = self._line("Depreciation Add-back", "depreciation_addback", records, period_labels)
        if all(value == ZERO for value in da.values.values()):
            da = self._line("Depreciation Add-back", "depreciation_amortization", records, period_labels)
        wc = self._line("Working Capital Movement", "working_capital_movement", records, period_labels)
        capex = self._line("Capital Expenditures", "capex", records, period_labels)
        financing = self._line("Financing Movement", "financing_movement", records, period_labels)
        net_change_cash = self._computed_line(
            "Net Change In Cash",
            period_labels,
            lambda period: net_income.values[period]
            + da.values[period]
            + wc.values[period]
            + capex.values[period]
            + financing.values[period],
            is_subtotal=True,
        )
        cash_flow_tie_out = self._computed_line(
            "Cash Flow Tie-Out",
            period_labels,
            lambda period: self._cash_change(period, period_labels, bs_cash)
            - net_change_cash.values[period],
            is_check=True,
        )
        return [net_income, da, wc, capex, financing, net_change_cash, cash_flow_tie_out]

    def _line(
        self,
        label: str,
        account_id: str,
        records: Iterable[MappedFinancialRecord],
        period_labels: list[str],
    ) -> StatementLine:
        values = dict.fromkeys(period_labels, ZERO)
        source_account_ids: set[str] = set()
        for record in records:
            if record.account_id != account_id:
                continue
            period = record.source_record.period_label
            if period in values:
                values[period] += record.source_record.amount
                source_account_ids.add(record.source_record.source_account_id)
        return StatementLine(
            label=label,
            account_id=account_id,
            values=values,
            source_account_ids=sorted(source_account_ids),
        )

    def _computed_line(
        self,
        label: str,
        period_labels: list[str],
        calculate: Callable[[str], Decimal],
        is_check: bool = False,
        is_subtotal: bool = True,
    ) -> StatementLine:
        return StatementLine(
            label=label,
            values={period: calculate(period) for period in period_labels},
            is_subtotal=is_subtotal,
            is_check=is_check,
        )

    def _find_line(self, lines: list[StatementLine], label: str) -> StatementLine:
        for line in lines:
            if line.label == label:
                return line
        raise ValueError(f"Missing statement line {label!r}.")

    def _cash_change(
        self,
        period: str,
        period_labels: list[str],
        cash_line: StatementLine,
    ) -> Decimal:
        index = period_labels.index(period)
        if index == 0:
            return ZERO
        current_period = period_labels[index]
        previous_period = period_labels[index - 1]
        return cash_line.values[current_period] - cash_line.values[previous_period]

    def _statement_issues(
        self,
        balance_lines: list[StatementLine],
        cash_flow_lines: list[StatementLine],
        period_labels: list[str],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        balance_check = self._find_line(balance_lines, "Balance Check")
        cash_flow_tie_out = self._find_line(cash_flow_lines, "Cash Flow Tie-Out")
        for index, period in enumerate(period_labels):
            if balance_check.values[period] != ZERO:
                issues.append(
                    ValidationIssue(
                        code="balance_sheet_imbalance",
                        message=f"Balance sheet does not balance for {period}.",
                        severity=IssueSeverity.ERROR,
                        period_label=period,
                        metadata={"difference": str(balance_check.values[period])},
                    )
                )
            if index > 0 and cash_flow_tie_out.values[period] != ZERO:
                issues.append(
                    ValidationIssue(
                        code="cash_flow_tie_out_failure",
                        message=f"Cash flow does not tie to cash movement for {period}.",
                        severity=IssueSeverity.WARNING,
                        period_label=period,
                        metadata={"difference": str(cash_flow_tie_out.values[period])},
                    )
                )
        return issues
