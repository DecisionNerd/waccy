"""Unit tests for ontology module."""

from waccy.core.ontology import AccountCategory, AccountType, StandardChartOfAccounts


def test_account_type_enum() -> None:
    """Test AccountType enum values."""
    assert AccountType.ASSET == "asset"
    assert AccountType.LIABILITY == "liability"
    assert AccountType.EQUITY == "equity"
    assert AccountType.REVENUE == "revenue"
    assert AccountType.EXPENSE == "expense"


def test_account_category_model() -> None:
    """Test AccountCategory model."""
    account = AccountCategory(
        id="revenue-001",
        name="Product Sales",
        type=AccountType.REVENUE,
        level=1,
        description="Revenue from product sales",
    )
    assert account.id == "revenue-001"
    assert account.type == AccountType.REVENUE


def test_standard_chart_of_accounts() -> None:
    """Test StandardChartOfAccounts initialization."""
    ontology = StandardChartOfAccounts()
    assert isinstance(ontology.accounts, dict)

