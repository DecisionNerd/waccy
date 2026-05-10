"""WACCY - Intelligent Financial Modeling Platform for Small Businesses."""

__version__ = "0.0.2"

# Core exports
# Classification exports
from waccy.classification import ClassificationEngine
from waccy.core import (
    AccountCategory,
    AccountType,
    ExtractedData,
    ExtractedTransaction,
    StandardChartOfAccounts,
    ThreeStatementModel,
)

# Extraction exports
from waccy.extraction import Extractor, ExtractorRegistry

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
    "ThreeStatementModel",
]
