"""Tests for the QuickBooks live-pull support layer."""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError

import pytest

if TYPE_CHECKING:
    from urllib.request import Request

ROOT = Path(__file__).resolve().parents[2]
QUICKBOOKS_SRC = ROOT / "extensions" / "waccy-quickbooks" / "src"
if not QUICKBOOKS_SRC.exists():
    pytest.skip("waccy-quickbooks extension source tree is not available.", allow_module_level=True)
sys.path.insert(0, str(QUICKBOOKS_SRC))

from waccy_quickbooks import (  # noqa: E402
    FileTokenCache,
    QuickBooksApiClient,
    QuickBooksApiError,
    QuickBooksEnvironment,
    QuickBooksOAuthConfig,
    QuickBooksReportNormalizer,
    QuickBooksToken,
)


def test_file_token_cache_round_trips_token(tmp_path: Path) -> None:
    token = QuickBooksToken(
        access_token="access",
        refresh_token="refresh",
        realm_id="123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    cache = FileTokenCache(tmp_path / "qbo-token.json")

    cache.save(token)
    loaded = cache.load()

    assert loaded == token
    assert cache.path.stat().st_mode & 0o777 == 0o600


def test_api_client_pulls_company_accounts_and_financial_reports() -> None:
    seen_urls: list[str] = []

    def fake_transport(request: Request, timeout: float) -> bytes:
        assert timeout == 30.0
        assert request.headers["Authorization"] == "Bearer access"
        seen_urls.append(request.full_url)
        if "/companyinfo/" in request.full_url:
            return _json({"CompanyInfo": {"CompanyName": "Fixture QBO Co"}})
        if "/query?" in request.full_url:
            return _json({"QueryResponse": {"Account": [{"Id": "1", "Name": "Checking"}]}})
        if "/reports/ProfitAndLoss" in request.full_url:
            return _json({"Header": {"ReportName": "ProfitAndLoss"}})
        if "/reports/BalanceSheet" in request.full_url:
            return _json({"Header": {"ReportName": "BalanceSheet"}})
        if "/reports/CashFlow" in request.full_url:
            return _json({"Header": {"ReportName": "CashFlow"}})
        raise AssertionError(f"Unexpected URL: {request.full_url}")

    client = QuickBooksApiClient(
        QuickBooksToken(access_token="access", refresh_token="refresh", realm_id="123"),
        transport=fake_transport,
    )

    pull = client.pull_financial_reports(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert pull.entity_name == "Fixture QBO Co"
    assert pull.accounts == [{"Id": "1", "Name": "Checking"}]
    assert set(pull.reports) == {"ProfitAndLoss", "BalanceSheet", "CashFlow"}
    assert all("sandbox-quickbooks.api.intuit.com" in url for url in seen_urls)
    assert any("start_date=2024-01-01" in url for url in seen_urls)
    assert any("end_date=2024-12-31" in url for url in seen_urls)


def test_api_client_from_token_cache_refreshes_expired_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expired = QuickBooksToken(
        access_token="old",
        refresh_token="refresh",
        realm_id="123",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    refreshed = QuickBooksToken(
        access_token="new",
        refresh_token="new-refresh",
        realm_id="123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    cache = FileTokenCache(tmp_path / "qbo-token.json")
    cache.save(expired)

    class FakeOAuthClient:
        def __init__(self, config: QuickBooksOAuthConfig) -> None:
            self.config = config

        def refresh(self, token: QuickBooksToken) -> QuickBooksToken:
            assert token == expired
            return refreshed

    monkeypatch.setattr("waccy_quickbooks.client.QuickBooksOAuthClient", FakeOAuthClient)

    client = QuickBooksApiClient.from_token_cache(
        cache,
        QuickBooksOAuthConfig(client_id="id", client_secret="secret", redirect_uri="http://localhost"),
    )

    assert client.token == refreshed
    assert cache.load() == refreshed


def test_api_client_reports_http_errors() -> None:
    def fake_transport(request: Request, timeout: float) -> bytes:
        del request, timeout
        raise HTTPError("https://example.test", 400, "Bad Request", {}, None)

    client = QuickBooksApiClient(
        QuickBooksToken(access_token="access", refresh_token="refresh", realm_id="123"),
        QuickBooksEnvironment.PRODUCTION,
        transport=fake_transport,
    )

    with pytest.raises(QuickBooksApiError, match="HTTP 400"):
        client.get_company_info()


def test_api_client_rejects_invalid_account_page_size() -> None:
    client = QuickBooksApiClient(
        QuickBooksToken(access_token="access", refresh_token="refresh", realm_id="123")
    )

    with pytest.raises(ValueError, match="page_size"):
        client.get_accounts(page_size=0)


def test_api_client_reports_url_errors() -> None:
    def fake_transport(request: Request, timeout: float) -> bytes:
        del request, timeout
        raise URLError("network unavailable")

    client = QuickBooksApiClient(
        QuickBooksToken(access_token="access", refresh_token="refresh", realm_id="123"),
        transport=fake_transport,
    )

    with pytest.raises(QuickBooksApiError, match="network unavailable"):
        client.get_company_info()


def test_report_normalizer_converts_nested_qbo_reports_to_fixture() -> None:
    raw_fixture = _release_raw_fixture()

    fixture = QuickBooksReportNormalizer().to_fixture(raw_fixture)

    assert fixture["entity_name"] == "Sanitized QBO Release Fixture Co"
    assert [period["label"] for period in fixture["periods"]] == ["2023", "2024"]
    assert fixture["metadata"]["qbo_source_issues"] == []
    records = fixture["records"]
    assert any(
        record["source_account_name"] == "Accounts Receivable (A/R)"
        and record["statement"] == "balance_sheet"
        and record["source_account_type"] == "Accounts Receivable"
        and record["metadata"]["row_path"] == ["ASSETS", "Current Assets", "Accounts Receivable (A/R)"]
        for record in records
    )
    assert any(
        record["source_account_name"] == "Net Change In Cash"
        and record["statement"] == "cash_flow_statement"
        and record["metadata"]["is_summary_check"]
        for record in records
    )


def test_report_normalizer_reports_no_data_and_missing_statements() -> None:
    raw_fixture = _release_raw_fixture()
    raw_fixture["reports"] = {
        "2024": {
            "ProfitAndLoss": raw_fixture["reports"]["2024"]["ProfitAndLoss"],
        }
    }
    raw_fixture["reports"]["2024"]["ProfitAndLoss"]["Header"]["Option"] = [
        {"Name": "NoReportData", "Value": "true"}
    ]
    raw_fixture["reports"]["2024"]["ProfitAndLoss"]["Rows"]["Row"] = []

    fixture = QuickBooksReportNormalizer().to_fixture(raw_fixture)
    issue_codes = {issue["code"] for issue in fixture["metadata"]["qbo_source_issues"]}

    assert {"qbo_report_no_data", "missing_required_source_statement"}.issubset(issue_codes)
    assert fixture["records"] == []


def test_report_normalizer_parses_parenthesized_negative_values() -> None:
    assert QuickBooksReportNormalizer._decimal("(1,234.56)") == Decimal("-1234.56")


def _json(payload: dict[str, object]) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _release_raw_fixture() -> dict[str, object]:
    return json.loads((ROOT / "tests" / "fixtures" / "qbo_release_smoke_raw.json").read_text())
