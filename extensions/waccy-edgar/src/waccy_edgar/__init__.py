"""WACCY extension for SEC EDGAR filing parsing."""

from waccy_edgar.companyfacts import EdgarCompanyFactsNormalizer
from waccy_edgar.extractor import EdgarExtractor

__version__ = "0.0.2"

__all__ = [
    "EdgarCompanyFactsNormalizer",
    "EdgarExtractor",
]
