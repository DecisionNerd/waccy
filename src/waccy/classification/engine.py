"""Deterministic classification for ambiguous accounts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from waccy.classification.confidence import ConfidenceScorer
from waccy.classification.patterns import PatternMatcher
from waccy.core.models import MappingStatus
from waccy.core.ontology import AccountCategory, StandardChartOfAccounts


class ClassificationResult(BaseModel):
    """Diagnostic result for account classification."""

    account: AccountCategory | None = None
    account_id: str | None = None
    status: MappingStatus
    confidence: float = Field(ge=0.0, le=1.0)
    diagnostics: list[str] = Field(default_factory=list)
    pattern: dict[str, Any] | None = None


class ClassificationEngine:
    """Deterministic-first classification for ambiguous accounts."""

    def __init__(self, llm_provider: str | None = None) -> None:
        """Initialize the classification engine."""
        self.ontology = StandardChartOfAccounts()
        self.llm_provider = llm_provider
        self.pattern_matcher = PatternMatcher(self.ontology)
        self.confidence_scorer = ConfidenceScorer(self.ontology)

    def classify_account(
        self,
        source_account_name: str,
        transaction_patterns: list[dict],
        context: dict,
    ) -> tuple[AccountCategory, float]:
        """Classify an ambiguous account with confidence score."""
        result = self.classify_with_diagnostics(source_account_name, transaction_patterns, context)
        if result.account is None:
            raise ValueError("; ".join(result.diagnostics) or "Account could not be classified.")
        return result.account, result.confidence

    def classify_with_diagnostics(
        self,
        source_account_name: str,
        transaction_patterns: list[dict],
        context: dict,
    ) -> ClassificationResult:
        """Classify an account and return mapping diagnostics."""
        source_system = str(context.get("source_system", ""))
        candidates = self.ontology.map_candidates(source_account_name, source_system)
        pattern = self.pattern_matcher.match_pattern(source_account_name, transaction_patterns)

        if pattern and isinstance(pattern.get("account_id"), str):
            pattern_account = self.ontology.get_account(str(pattern["account_id"]))
            if pattern_account:
                confidence = self.confidence_scorer.calculate_confidence(
                    source_account_name,
                    pattern_account.id,
                    transaction_patterns,
                    {
                        "pattern_account_id": pattern_account.id,
                        "statement": pattern.get("statement") or context.get("statement"),
                    },
                )
                return ClassificationResult(
                    account=pattern_account,
                    account_id=pattern_account.id,
                    status=MappingStatus.MAPPED,
                    confidence=max(confidence, float(pattern.get("confidence", 0.0))),
                    diagnostics=["classified_by_edgar_pattern"],
                    pattern=pattern,
                )

        if len(candidates) == 1:
            account = candidates[0]
            confidence = self.confidence_scorer.calculate_confidence(
                source_account_name,
                account.id,
                transaction_patterns,
                {"statement": context.get("statement")},
            )
            return ClassificationResult(
                account=account,
                account_id=account.id,
                status=MappingStatus.MAPPED,
                confidence=max(confidence, 0.8),
                diagnostics=["classified_by_ontology_alias"],
                pattern=pattern,
            )

        if len(candidates) > 1:
            return ClassificationResult(
                status=MappingStatus.AMBIGUOUS,
                confidence=0.35,
                diagnostics=[
                    "ambiguous_candidates: " + ", ".join(account.id for account in candidates)
                ],
                pattern=pattern,
            )

        return ClassificationResult(
            status=MappingStatus.UNMAPPED,
            confidence=0.0,
            diagnostics=[f"No deterministic classification for {source_account_name!r}."],
            pattern=pattern,
        )

    def learn_from_edgar(self, filing_data: dict) -> None:
        """Extract classification patterns from EDGAR filings."""
        self.pattern_matcher.extract_patterns(filing_data)
