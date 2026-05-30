"""Confidence scoring for account mappings."""

from typing import Any

from waccy.core.ontology import StandardChartOfAccounts


def _key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


class ConfidenceScorer:
    """Calculate confidence scores for account mappings."""

    def __init__(self, ontology: StandardChartOfAccounts | None = None) -> None:
        """Initialize the scorer."""
        self.ontology = ontology or StandardChartOfAccounts()

    def calculate_confidence(
        self,
        source_account: str,
        mapped_account: str,
        transaction_patterns: list[dict],
        validation_results: dict[str, Any],
    ) -> float:
        """Calculate confidence score for an account mapping."""
        account = self.ontology.get_account(mapped_account)
        if account is None:
            return 0.0

        score = 0.35
        source_key = _key(source_account)
        alias_keys = {_key(account.id), _key(account.name), *{_key(alias) for alias in account.aliases}}
        if source_key in alias_keys:
            score += 0.45
        elif any(source_key in alias or alias in source_key for alias in alias_keys):
            score += 0.25

        if any(_pattern_supports_account(pattern, mapped_account) for pattern in transaction_patterns):
            score += 0.1
        if validation_results.get("pattern_account_id") == mapped_account:
            score += 0.1
        if validation_results.get("statement") == account.statement:
            score += 0.05
        if validation_results.get("ambiguous"):
            score -= 0.25
        if validation_results.get("unmapped"):
            score -= 0.35
        return max(0.0, min(round(score, 2), 1.0))


def _pattern_supports_account(pattern: dict, account_id: str) -> bool:
    return (
        pattern.get("account_id") == account_id
        or pattern.get("mapped_account") == account_id
        or pattern.get("canonical_account_id") == account_id
    )
