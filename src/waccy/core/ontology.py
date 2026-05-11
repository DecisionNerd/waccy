"""Standardized chart of accounts and financial ontology."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AccountType(str, Enum):
    """Top-level account categories."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    CASH_FLOW = "cash_flow"


class AccountCategory(BaseModel):
    """Standard account category."""

    id: str
    name: str
    type: AccountType
    parent_id: str | None = None
    level: int
    description: str
    statement: str | None = None
    normal_balance: str = "debit"
    cash_flow_section: str | None = None
    sort_order: int = 0
    aliases: list[str] = Field(default_factory=list)


def _key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


class StandardChartOfAccounts:
    """WACCY standardized chart of accounts."""

    def __init__(self) -> None:
        """Initialize the standard chart of accounts."""
        self.accounts: dict[str, AccountCategory] = {}
        self._aliases: dict[str, list[str]] = {}
        self._initialize_standard_accounts()

    def _add_account(self, account: AccountCategory) -> None:
        self.accounts[account.id] = account
        self._aliases.setdefault(_key(account.id), []).append(account.id)
        self._aliases.setdefault(_key(account.name), []).append(account.id)
        for alias in account.aliases:
            self._aliases.setdefault(_key(alias), []).append(account.id)

    def _initialize_standard_accounts(self) -> None:
        """Initialize the minimum chart of accounts for v0.1.0."""
        account_specs = [
            ("revenue", "Revenue", AccountType.REVENUE, "income_statement", "credit", None, 100, ["sales", "sales revenue", "total revenue", "income", "us-gaap:revenues", "us-gaap:revenuefromcontractwithcustomerexcludingassessedtax", "us-gaap:salesrevenuenet", "revenues"]),
            ("cogs", "Cost of Goods Sold", AccountType.EXPENSE, "income_statement", "debit", None, 200, ["cost of goods sold", "cost of revenue", "cost of sales", "us-gaap:costofrevenue", "us-gaap:costofgoodsandservicessold", "us-gaap:costofgoodsandserviceexcludingdepreciationdepletionandamortization"]),
            ("operating_expenses", "Operating Expenses", AccountType.EXPENSE, "income_statement", "debit", None, 300, ["opex", "operating expense", "operating expenses", "general and administrative", "sg&a", "us-gaap:operatingexpenses", "us-gaap:sellinggeneralandadministrativeexpense"]),
            ("depreciation_amortization", "Depreciation & Amortization", AccountType.EXPENSE, "income_statement", "debit", None, 350, ["depreciation", "amortization", "d&a", "us-gaap:depreciationdepletionandamortization", "us-gaap:depreciationdepletionandamortizationexpense"]),
            ("interest_expense", "Interest Expense", AccountType.EXPENSE, "income_statement", "debit", None, 400, ["interest", "interest expense", "us-gaap:interestexpense", "us-gaap:interestexpensenonoperating"]),
            ("tax_expense", "Tax Expense", AccountType.EXPENSE, "income_statement", "debit", None, 500, ["tax", "income tax", "income tax expense", "us-gaap:incometaxexpensebenefit"]),
            ("cash", "Cash", AccountType.ASSET, "balance_sheet", "debit", None, 1000, ["bank", "cash and cash equivalents", "checking", "savings", "undeposited funds", "us-gaap:cashandcashequivalentsatcarryingvalue", "us-gaap:cashcashequivalentsrestrictedcashandrestrictedcashequivalents"]),
            ("accounts_receivable", "Accounts Receivable", AccountType.ASSET, "balance_sheet", "debit", None, 1100, ["accounts receivable", "accounts receivable a/r", "ar", "a/r", "us-gaap:accountsreceivablenetcurrent"]),
            ("inventory", "Inventory", AccountType.ASSET, "balance_sheet", "debit", None, 1200, ["inventory", "inventory asset", "stock", "us-gaap:inventorynet"]),
            ("ppe", "Property, Plant & Equipment", AccountType.ASSET, "balance_sheet", "debit", None, 1300, ["fixed assets", "original cost", "property plant and equipment", "ppe", "pp&e", "us-gaap:propertyplantandequipmentnet"]),
            ("accumulated_depreciation", "Accumulated Depreciation", AccountType.ASSET, "balance_sheet", "credit", None, 1350, ["accumulated depreciation", "us-gaap:accumulateddepreciationdepletionandamortizationpropertyplantandequipment"]),
            ("accounts_payable", "Accounts Payable", AccountType.LIABILITY, "balance_sheet", "credit", None, 2000, ["accounts payable", "accounts payable a/p", "ap", "a/p", "us-gaap:accountspayablecurrent"]),
            ("accrued_expenses", "Accrued Expenses", AccountType.LIABILITY, "balance_sheet", "credit", None, 2100, ["accrued expenses", "accruals", "accrued liabilities", "arizona dept of revenue payable", "board of equalization payable", "tax payable", "sales tax payable", "us-gaap:accruedliabilitiescurrent", "us-gaap:accruedincometaxescurrent"]),
            ("debt", "Debt", AccountType.LIABILITY, "balance_sheet", "credit", None, 2200, ["loan", "loans", "loan payable", "mastercard", "credit card", "notes payable", "debt", "long-term debt", "us-gaap:longtermdebtcurrent", "us-gaap:longtermdebtnoncurrent", "us-gaap:longtermdebtandfinanceleaseobligationscurrent", "us-gaap:longtermdebtandfinanceleaseobligationsnoncurrent"]),
            ("equity", "Equity", AccountType.EQUITY, "balance_sheet", "credit", None, 3000, ["owners equity", "owner's equity", "opening balance equity", "members equity", "stockholders equity", "us-gaap:stockholdersequity", "us-gaap:stockholdersequityincludingportionattributabletononcontrollinginterest"]),
            ("retained_earnings", "Retained Earnings", AccountType.EQUITY, "balance_sheet", "credit", None, 3100, ["retained earnings", "us-gaap:retainedearningsaccumulateddeficit"]),
            ("net_income", "Net Income", AccountType.CASH_FLOW, "cash_flow_statement", "credit", "operating", 4000, ["net income", "net earnings", "profit", "us-gaap:netincomeloss"]),
            ("depreciation_addback", "Depreciation Add-back", AccountType.CASH_FLOW, "cash_flow_statement", "credit", "operating", 4100, ["depreciation addback", "depreciation and amortization", "us-gaap:depreciationdepletionandamortization", "us-gaap:depreciationdepletionandamortizationexpense"]),
            ("working_capital_movement", "Working Capital Movement", AccountType.CASH_FLOW, "cash_flow_statement", "credit", "operating", 4200, ["change in working capital", "changes in operating assets and liabilities", "us-gaap:increasedecreaseinoperatingassetsandliabilitiesnetofacquisitions", "us-gaap:netcashprovidedbyusedinoperatingactivities"]),
            ("capex", "Capital Expenditures", AccountType.CASH_FLOW, "cash_flow_statement", "debit", "investing", 5000, ["capex", "capital expenditures", "purchase of property and equipment", "us-gaap:paymentstoacquirepropertyplantandequipment"]),
            ("financing_movement", "Financing Movement", AccountType.CASH_FLOW, "cash_flow_statement", "credit", "financing", 6000, ["financing activities", "debt proceeds", "debt repayment", "us-gaap:proceedsfromissuanceofdebt", "us-gaap:proceedsfromissuanceoflongtermdebt", "us-gaap:repaymentsofdebt"]),
        ]
        for account_id, name, account_type, statement, normal_balance, cf_section, order, aliases in account_specs:
            self._add_account(
                AccountCategory(
                    id=account_id,
                    name=name,
                    type=account_type,
                    level=1,
                    description=name,
                    statement=statement,
                    normal_balance=normal_balance,
                    cash_flow_section=cf_section,
                    sort_order=order,
                    aliases=aliases,
                )
            )

    def map_candidates(self, source_account: str, source_system: str | None = None) -> list[AccountCategory]:
        """Return possible standard accounts for a source account."""
        del source_system
        account_ids = self._aliases.get(_key(source_account), [])
        return [self.accounts[account_id] for account_id in dict.fromkeys(account_ids)]

    def map_account(
        self, source_account: str, source_system: str
    ) -> AccountCategory | None:
        """Map a source account to one standard account when deterministic."""
        candidates = self.map_candidates(source_account, source_system)
        if len(candidates) == 1:
            return candidates[0]
        return None

    def get_account(self, account_id: str) -> AccountCategory | None:
        """Get account by ID."""
        return self.accounts.get(account_id)

    def list_accounts(self, account_type: AccountType | None = None) -> list[AccountCategory]:
        """List all accounts, optionally filtered by type."""
        accounts = sorted(self.accounts.values(), key=lambda account: account.sort_order)
        if account_type is None:
            return accounts
        return [acc for acc in accounts if acc.type == account_type]
