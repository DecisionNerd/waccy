"""Sample data fixtures for testing."""

from datetime import date
from decimal import Decimal

from waccy.core.models import ExtractedData, ExtractedTransaction


def sample_transaction() -> ExtractedTransaction:
    """Create a sample transaction for testing."""
    return ExtractedTransaction(
        date=date(2024, 1, 15),
        account_id="revenue-001",
        amount=Decimal("1000.00"),
        description="Product sale",
        source_id="txn-001",
        confidence=0.95,
    )


def sample_extracted_data() -> ExtractedData:
    """Create sample extracted data for testing."""
    return ExtractedData(
        transactions=[sample_transaction()],
        accounts=[],
        metadata={"source": "test"},
        quality_score=0.9,
    )

