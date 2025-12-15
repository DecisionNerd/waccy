"""Standardized chart of accounts and financial ontology."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AccountType(str, Enum):
    """Top-level account categories."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountCategory(BaseModel):
    """Standard account category."""

    id: str
    name: str
    type: AccountType
    parent_id: Optional[str] = None
    level: int
    description: str


class StandardChartOfAccounts:
    """WACCY standardized chart of accounts."""

    def __init__(self) -> None:
        """Initialize the standard chart of accounts."""
        self.accounts: dict[str, AccountCategory] = {}
        self._initialize_standard_accounts()

    def _initialize_standard_accounts(self) -> None:
        """Initialize the standard chart of accounts."""
        # TODO: Implement comprehensive standard chart of accounts
        # Income statement accounts
        # Balance sheet accounts
        # Cash flow accounts
        # Supporting schedules
        pass

    def map_account(
        self, source_account: str, source_system: str
    ) -> Optional[AccountCategory]:
        """Map a source account to standard account."""
        # TODO: Implement account mapping logic
        return None

    def get_account(self, account_id: str) -> Optional[AccountCategory]:
        """Get account by ID."""
        return self.accounts.get(account_id)

    def list_accounts(self, account_type: Optional[AccountType] = None) -> list[AccountCategory]:
        """List all accounts, optionally filtered by type."""
        if account_type is None:
            return list(self.accounts.values())
        return [acc for acc in self.accounts.values() if acc.type == account_type]

