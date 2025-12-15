"""Abstract base classes for data source extractors."""

from abc import ABC, abstractmethod
from typing import Any

from waccy.core.models import ExtractedData


class Extractor(ABC):
    """Abstract base class for all data source extractors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Extractor name."""
        ...

    @property
    @abstractmethod
    def data_source(self) -> str:
        """Data source identifier (e.g., 'quickbooks', 'edgar')."""
        ...

    @abstractmethod
    def authenticate(self, credentials: dict[str, str]) -> bool:
        """Authenticate with the data source."""
        ...

    @abstractmethod
    def extract(self, config: dict[str, Any]) -> ExtractedData:
        """Extract data from the source."""
        ...

    def validate(self, data: ExtractedData) -> bool:
        """Validate extracted data."""
        # Default implementation using Pandera
        from waccy.core.validation import validate_extracted_data

        return validate_extracted_data(data)


# Re-export for convenience
from waccy.core.models import ExtractedData, ExtractedTransaction  # noqa: E402

__all__ = ["Extractor", "ExtractedData", "ExtractedTransaction"]

