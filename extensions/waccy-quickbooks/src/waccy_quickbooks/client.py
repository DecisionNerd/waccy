"""Tiny typed QuickBooks Online report puller."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from waccy_quickbooks.auth import QuickBooksOAuthClient
from waccy_quickbooks.models import (
    QuickBooksEnvironment,
    QuickBooksOAuthConfig,
    QuickBooksReportPull,
    QuickBooksReportRequest,
    QuickBooksToken,
)

if TYPE_CHECKING:
    from datetime import date

    from waccy_quickbooks.token_cache import FileTokenCache

DEFAULT_REPORTS = ("ProfitAndLoss", "BalanceSheet", "CashFlow")
Transport = Callable[[Request, float], bytes]


class QuickBooksApiError(RuntimeError):
    """Raised when QBO returns an HTTP error or malformed JSON."""


class QuickBooksApiClient:
    """Pull raw QBO JSON for the reports WACCY needs."""

    def __init__(
        self,
        token: QuickBooksToken,
        environment: QuickBooksEnvironment = QuickBooksEnvironment.SANDBOX,
        *,
        transport: Transport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.token = token
        self.environment = environment
        self.transport = transport or self._default_transport
        self.timeout = timeout

    @classmethod
    def from_token_cache(
        cls,
        cache: FileTokenCache,
        oauth_config: QuickBooksOAuthConfig,
        *,
        transport: Transport | None = None,
        timeout: float = 30.0,
    ) -> QuickBooksApiClient:
        """Create a client from cached token state, refreshing when needed."""
        token = cache.load()
        if token is None:
            raise ValueError("QuickBooks token cache is empty; complete OAuth before pulling reports.")
        if token.is_access_token_expired():
            token = QuickBooksOAuthClient(oauth_config).refresh(token)
            cache.save(token)
        return cls(
            token,
            oauth_config.environment,
            transport=transport,
            timeout=timeout,
        )

    def get_company_info(self) -> dict[str, Any]:
        """Return the QBO CompanyInfo payload."""
        path = f"/v3/company/{self.token.realm_id}/companyinfo/{self.token.realm_id}"
        return self._request_json(path)

    def get_accounts(self, *, page_size: int = 1000) -> list[dict[str, Any]]:
        """Return all chart-of-account rows visible to the token."""
        if page_size <= 0:
            raise ValueError("QBO account query page_size must be a positive integer.")
        accounts: list[dict[str, Any]] = []
        start_position = 1
        while True:
            query = (
                "select * from Account "
                f"startposition {start_position} maxresults {page_size}"
            )
            payload = self._request_json(
                f"/v3/company/{self.token.realm_id}/query",
                {"query": query},
            )
            batch = payload.get("QueryResponse", {}).get("Account", [])
            if not isinstance(batch, list):
                raise QuickBooksApiError("QBO Account query returned an unexpected payload shape.")
            accounts.extend(batch)
            if len(batch) < page_size:
                return accounts
            start_position += page_size

    def get_report(self, request: QuickBooksReportRequest) -> dict[str, Any]:
        """Return a raw QBO report payload."""
        params = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "accounting_method": request.accounting_method,
        }
        if request.summarize_column_by:
            params["summarize_column_by"] = request.summarize_column_by
        return self._request_json(
            f"/v3/company/{self.token.realm_id}/reports/{request.report_name}",
            params,
        )

    def pull_financial_reports(
        self,
        *,
        start_date: date,
        end_date: date,
        report_names: Iterable[str] = DEFAULT_REPORTS,
        accounting_method: str = "Accrual",
        summarize_column_by: str | None = None,
    ) -> QuickBooksReportPull:
        """Pull company info, chart of accounts, and the requested report set."""
        company_info = self.get_company_info()
        accounts = self.get_accounts()
        reports = {
            report_name: self.get_report(
                QuickBooksReportRequest(
                    report_name=report_name,
                    start_date=start_date,
                    end_date=end_date,
                    accounting_method=accounting_method,
                    summarize_column_by=summarize_column_by,
                )
            )
            for report_name in report_names
        }
        return QuickBooksReportPull(
            realm_id=self.token.realm_id,
            entity_name=_company_name(company_info),
            environment=self.environment,
            start_date=start_date,
            end_date=end_date,
            company_info=company_info,
            accounts=accounts,
            reports=reports,
            metadata={"accounting_method": accounting_method},
        )

    def _request_json(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{self._base_url}{path}{query}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token.access_token}",
            },
            method="GET",
        )
        try:
            raw_response = self.transport(request, self.timeout)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise QuickBooksApiError(f"QBO request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise QuickBooksApiError(f"QBO request failed: {exc.reason}") from exc
        try:
            payload = json.loads(raw_response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise QuickBooksApiError("QBO returned a non-JSON response.") from exc
        if not isinstance(payload, dict):
            raise QuickBooksApiError("QBO returned an unexpected non-object JSON response.")
        return payload

    @property
    def _base_url(self) -> str:
        if self.environment == QuickBooksEnvironment.PRODUCTION:
            return "https://quickbooks.api.intuit.com"
        return "https://sandbox-quickbooks.api.intuit.com"

    @staticmethod
    def _default_transport(request: Request, timeout: float) -> bytes:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
        if not isinstance(data, bytes):
            raise QuickBooksApiError("QBO returned a non-bytes HTTP response.")
        return data


def _company_name(company_info: dict[str, Any]) -> str:
    info = company_info.get("CompanyInfo", {})
    if isinstance(info, dict):
        name = info.get("CompanyName") or info.get("LegalName")
        if name:
            return str(name)
    return "QuickBooks Entity"
