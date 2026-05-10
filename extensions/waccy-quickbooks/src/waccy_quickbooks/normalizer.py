"""Normalize raw QuickBooks Online reports into WACCY fixture data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from waccy_quickbooks.models import QuickBooksReportPull

REPORT_STATEMENTS = {
    "ProfitAndLoss": "income_statement",
    "BalanceSheet": "balance_sheet",
    "CashFlow": "cash_flow_statement",
}
REQUIRED_REPORTS = tuple(REPORT_STATEMENTS)


class QuickBooksReportNormalizer:
    """Convert raw QBO report payloads into ``QuickBooksExtractor`` fixtures."""

    def to_fixture(self, payload: QuickBooksReportPull | dict[str, Any]) -> dict[str, Any]:
        """Return a WACCY-compatible fixture from raw QBO report data."""
        data = payload.model_dump(mode="json") if isinstance(payload, QuickBooksReportPull) else payload
        if not isinstance(data, dict):
            raise ValueError("QBO normalization requires a dictionary or QuickBooksReportPull payload.")

        reports_by_period = self._reports_by_period(data)
        accounts_by_id = self._accounts_by_id(data.get("accounts", []))
        records: list[dict[str, Any]] = []
        periods: dict[str, dict[str, str]] = {}
        source_issues: list[dict[str, Any]] = []
        report_record_counts: dict[str, int] = {}

        for period_label, reports in reports_by_period.items():
            if not isinstance(reports, dict):
                raise ValueError(f"QBO reports for period {period_label!r} must be a dictionary.")
            present_reports = {self._report_name(report_name, report) for report_name, report in reports.items()}
            source_issues.extend(
                self._issue(
                    "missing_required_source_statement",
                    f"Missing required QBO report {required_report!r} for {period_label}.",
                    required_report,
                    period_label,
                )
                for required_report in REQUIRED_REPORTS
                if required_report not in present_reports
            )

            for report_key, report in reports.items():
                if not isinstance(report, dict):
                    raise ValueError(f"QBO report {report_key!r} must be a dictionary.")
                report_name = self._report_name(str(report_key), report)
                statement = REPORT_STATEMENTS.get(report_name)
                if statement is None:
                    continue

                period = self._period_from_report(period_label, report)
                periods.setdefault(period["label"], period)
                if self._has_no_report_data(report):
                    source_issues.append(
                        self._issue(
                            "qbo_report_no_data",
                            f"QBO report {report_name!r} has NoReportData=true for {period['label']}.",
                            report_name,
                            period["label"],
                        )
                    )

                before_count = len(records)
                self._collect_records(
                    report=report,
                    report_name=report_name,
                    statement=statement,
                    period_label=period["label"],
                    accounts_by_id=accounts_by_id,
                    records=records,
                )
                report_record_counts[f"{period['label']}:{report_name}"] = len(records) - before_count

        for period_label in sorted(periods):
            for required_report in REQUIRED_REPORTS:
                count = report_record_counts.get(f"{period_label}:{required_report}", 0)
                if count == 0:
                    source_issues.append(
                        self._issue(
                            "missing_required_source_statement",
                            (
                                f"Required QBO report {required_report!r} produced no source records "
                                f"for {period_label}."
                            ),
                            required_report,
                            period_label,
                        )
                    )

        return {
            "entity_name": self._entity_name(data),
            "periods": [periods[label] for label in sorted(periods)],
            "accounts": list(accounts_by_id.values()),
            "records": records,
            "metadata": {
                "source": "qbo",
                "mode": "raw_report_normalized",
                "qbo_source_issues": source_issues,
            },
        }

    def _reports_by_period(self, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        reports = data.get("reports")
        if not isinstance(reports, dict):
            raise ValueError("QBO normalization requires a 'reports' dictionary.")
        if not reports:
            raise ValueError("QBO normalization requires at least one report payload.")

        if all(isinstance(report, dict) and "Header" in report for report in reports.values()):
            label = self._period_from_report(
                str(data.get("end_date", "report_period")),
                next(iter(reports.values())),
            )["label"]
            return {label: reports}
        return reports

    def _accounts_by_id(self, raw_accounts: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(raw_accounts, list):
            raise ValueError("QBO normalization requires 'accounts' to be a list.")
        accounts: dict[str, dict[str, Any]] = {}
        for account in raw_accounts:
            if not isinstance(account, dict):
                raise ValueError("QBO accounts must be dictionaries.")
            account_id = account.get("Id") or account.get("id")
            if account_id is not None:
                accounts[str(account_id)] = account
        return accounts

    def _collect_records(
        self,
        *,
        report: dict[str, Any],
        report_name: str,
        statement: str,
        period_label: str,
        accounts_by_id: dict[str, dict[str, Any]],
        records: list[dict[str, Any]],
    ) -> None:
        rows = report.get("Rows", {}).get("Row", [])
        if not isinstance(rows, list):
            raise ValueError(f"QBO report {report_name!r} Rows.Row must be a list.")
        self._walk_rows(
            rows,
            path=[],
            report_name=report_name,
            statement=statement,
            period_label=period_label,
            unit=str(report.get("Header", {}).get("Currency", "USD")),
            accounts_by_id=accounts_by_id,
            records=records,
        )

    def _walk_rows(
        self,
        rows: list[Any],
        *,
        path: list[str],
        report_name: str,
        statement: str,
        period_label: str,
        unit: str,
        accounts_by_id: dict[str, dict[str, Any]],
        records: list[dict[str, Any]],
    ) -> None:
        for row in rows:
            if not isinstance(row, dict):
                continue
            label = self._row_label(row)
            next_path = [*path, label] if label else path
            child_rows = row.get("Rows", {}).get("Row", [])
            if isinstance(child_rows, list):
                self._walk_rows(
                    child_rows,
                    path=next_path,
                    report_name=report_name,
                    statement=statement,
                    period_label=period_label,
                    unit=unit,
                    accounts_by_id=accounts_by_id,
                    records=records,
                )
            if row.get("type") == "Data":
                record = self._record_from_row(
                    row,
                    path=next_path,
                    report_name=report_name,
                    statement=statement,
                    period_label=period_label,
                    unit=unit,
                    accounts_by_id=accounts_by_id,
                )
                if record is not None:
                    records.append(record)
            elif report_name == "CashFlow":
                summary_record = self._cash_flow_summary_record(
                    row,
                    path=next_path,
                    report_name=report_name,
                    statement=statement,
                    period_label=period_label,
                    unit=unit,
                )
                if summary_record is not None:
                    records.append(summary_record)

    def _record_from_row(
        self,
        row: dict[str, Any],
        *,
        path: list[str],
        report_name: str,
        statement: str,
        period_label: str,
        unit: str,
        accounts_by_id: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        columns = row.get("ColData", [])
        if not isinstance(columns, list) or len(columns) < 2:
            return None
        account_column = columns[0]
        amount_column = columns[-1]
        if not isinstance(account_column, dict) or not isinstance(amount_column, dict):
            return None
        account_name = str(account_column.get("value", "")).strip()
        if not account_name:
            return None
        amount = self._decimal(amount_column.get("value"))
        if amount is None:
            return None
        account_id = str(account_column.get("id") or account_name)
        account = accounts_by_id.get(account_id, {})
        account_type = account.get("AccountType") or account.get("Classification")
        return {
            "source_account_id": account_id,
            "source_account_name": account_name,
            "name": account_name,
            "period": period_label,
            "amount": str(amount),
            "statement": statement,
            "source_account_type": str(account_type) if account_type else None,
            "unit": unit,
            "metadata": {
                "report_name": report_name,
                "row_path": path,
                "qbo_account": account,
                "qbo_row_type": row.get("type"),
            },
        }

    def _cash_flow_summary_record(
        self,
        row: dict[str, Any],
        *,
        path: list[str],
        report_name: str,
        statement: str,
        period_label: str,
        unit: str,
    ) -> dict[str, Any] | None:
        summary = row.get("Summary", {}).get("ColData", [])
        if not isinstance(summary, list) or len(summary) < 2:
            return None
        label_column = summary[0]
        amount_column = summary[-1]
        if not isinstance(label_column, dict) or not isinstance(amount_column, dict):
            return None
        label = str(label_column.get("value", "")).strip()
        if label != "Net Change In Cash":
            return None
        amount = self._decimal(amount_column.get("value"))
        if amount is None:
            return None
        return {
            "source_account_id": label,
            "source_account_name": label,
            "name": label,
            "period": period_label,
            "amount": str(amount),
            "statement": statement,
            "unit": unit,
            "metadata": {
                "report_name": report_name,
                "row_path": path,
                "qbo_row_type": row.get("type"),
                "is_summary_check": True,
            },
        }

    def _period_from_report(self, fallback_label: str, report: dict[str, Any]) -> dict[str, str]:
        header = report.get("Header", {})
        start = str(header.get("StartPeriod") or "")
        end = str(header.get("EndPeriod") or "")
        if not end:
            raise ValueError("QBO report Header.EndPeriod is required.")
        start_date = date.fromisoformat(start or f"{end[:4]}-01-01")
        end_date = date.fromisoformat(end)
        label = end_date.strftime("%Y") if fallback_label == "report_period" else str(fallback_label)
        if label.endswith("-12-31") or label.endswith("-06-30"):
            label = end_date.strftime("%Y")
        return {
            "label": label,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period_type": "year",
        }

    @staticmethod
    def _report_name(report_key: str, report: Any) -> str:
        if isinstance(report, dict):
            header_name = report.get("Header", {}).get("ReportName")
            if header_name:
                return str(header_name)
        return report_key

    @staticmethod
    def _has_no_report_data(report: dict[str, Any]) -> bool:
        options = report.get("Header", {}).get("Option", [])
        if not isinstance(options, list):
            return False
        for option in options:
            if (
                isinstance(option, dict)
                and option.get("Name") == "NoReportData"
                and str(option.get("Value", "")).lower() == "true"
            ):
                return True
        return False

    @staticmethod
    def _row_label(row: dict[str, Any]) -> str:
        header = row.get("Header", {}).get("ColData", [])
        if isinstance(header, list) and header and isinstance(header[0], dict):
            return str(header[0].get("value", "")).strip()
        summary = row.get("Summary", {}).get("ColData", [])
        if isinstance(summary, list) and summary and isinstance(summary[0], dict):
            return str(summary[0].get("value", "")).strip()
        columns = row.get("ColData", [])
        if isinstance(columns, list) and columns and isinstance(columns[0], dict):
            return str(columns[0].get("value", "")).strip()
        return ""

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value in {None, ""}:
            return None
        try:
            return Decimal(str(value).replace(",", ""))
        except InvalidOperation:
            return None

    @staticmethod
    def _entity_name(data: dict[str, Any]) -> str:
        if data.get("entity_name"):
            return str(data["entity_name"])
        company_info = data.get("company_info", {}).get("CompanyInfo", {})
        if isinstance(company_info, dict):
            name = company_info.get("CompanyName") or company_info.get("LegalName")
            if name:
                return str(name)
        return "QuickBooks Entity"

    @staticmethod
    def _issue(code: str, message: str, report_name: str, period_label: str) -> dict[str, str]:
        return {
            "code": code,
            "message": message,
            "severity": "error",
            "source": "qbo",
            "report_name": report_name,
            "period_label": period_label,
        }
