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


def test_qbo_live_smoke_aliases_map_deterministically() -> None:
    """QBO names surfaced by the live sandbox smoke map into canonical accounts."""
    ontology = StandardChartOfAccounts()
    expected = {
        "Accounts Receivable (A/R)": "accounts_receivable",
        "Inventory Asset": "inventory",
        "Undeposited Funds": "cash",
        "Original Cost": "ppe",
        "Accounts Payable (A/P)": "accounts_payable",
        "Mastercard": "debt",
        "Arizona Dept. of Revenue Payable": "accrued_expenses",
        "Board of Equalization Payable": "accrued_expenses",
        "Loan Payable": "debt",
        "Opening Balance Equity": "equity",
        "Net Change In Cash": "financing_movement",
    }

    for source_name, account_id in expected.items():
        account = ontology.map_account(source_name, "qbo")
        assert account is not None
        assert account.id == account_id
