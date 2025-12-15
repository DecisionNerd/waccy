"""WACCY - Intelligent Financial Modeling Platform for Small Businesses."""

__version__ = "0.1.0"

# Core exports
from waccy.core import (
    AccountCategory,
    AccountType,
    ExtractedData,
    ExtractedTransaction,
    StandardChartOfAccounts,
)

# Extraction exports
from waccy.extraction import Extractor, ExtractorRegistry

# Classification exports
from waccy.classification import ClassificationEngine

# Modeling exports
from waccy.modeling import ModelBuilder

__all__ = [
    "AccountCategory",
    "AccountType",
    "ClassificationEngine",
    "ExtractedData",
    "ExtractedTransaction",
    "Extractor",
    "ExtractorRegistry",
    "ModelBuilder",
    "StandardChartOfAccounts",
]

