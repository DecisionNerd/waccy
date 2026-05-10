"""Pattern matching from EDGAR filings."""

from typing import Any

from waccy.core.ontology import StandardChartOfAccounts


def _key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


class PatternMatcher:
    """Extract and match patterns from EDGAR filings."""

    def __init__(self, ontology: StandardChartOfAccounts | None = None) -> None:
        """Initialize the pattern matcher."""
        self.ontology = ontology or StandardChartOfAccounts()
        self.patterns: dict[str, Any] = {}

    def extract_patterns(self, filing_data: dict) -> dict[str, Any]:
        """Extract classification patterns from filing data."""
        raw_records = filing_data.get("records") or filing_data.get("facts") or filing_data.get("concepts") or []
        if not isinstance(raw_records, list):
            raise ValueError("EDGAR pattern extraction requires a list of records, facts, or concepts.")

        aliases: dict[str, dict[str, Any]] = {}
        statements: dict[str, str] = {}
        for raw_record in raw_records:
            if not isinstance(raw_record, dict):
                raise ValueError("EDGAR pattern records must be dictionaries.")
            source_name = _source_name(raw_record)
            if not source_name:
                continue
            statement = raw_record.get("statement")
            candidates = self.ontology.map_candidates(source_name, "edgar")
            if len(candidates) == 1:
                account = candidates[0]
                aliases[_key(source_name)] = {
                    "source": source_name,
                    "account_id": account.id,
                    "account_name": account.name,
                    "statement": statement or account.statement,
                    "confidence": 0.85,
                }
                if isinstance(statement, str):
                    statements[account.id] = statement

        self.patterns = {"aliases": aliases, "statements": statements}
        return self.patterns

    def match_pattern(self, account_name: str, transaction_data: list[dict]) -> dict | None:
        """Match account against learned patterns."""
        aliases = self.patterns.get("aliases", {})
        if isinstance(aliases, dict):
            match = aliases.get(_key(account_name))
            if isinstance(match, dict):
                return match

        for transaction in transaction_data:
            if not isinstance(transaction, dict):
                continue
            source_name = _source_name(transaction)
            if source_name and isinstance(aliases, dict):
                match = aliases.get(_key(source_name))
                if isinstance(match, dict):
                    return match
        return None


def _source_name(record: dict[str, Any]) -> str:
    value = (
        record.get("source_account_name")
        or record.get("concept")
        or record.get("name")
        or record.get("source_account_id")
        or record.get("account_id")
    )
    return str(value) if value else ""
