"""WACCY - Intelligent Financial Modeling Platform for Small Businesses."""

__version__ = "0.1.0"

# Core exports
# Classification exports
from waccy.classification import ClassificationEngine
from waccy.core import (
    CONTRACT_SCHEMA_VERSION,
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
    "CONTRACT_SCHEMA_VERSION",
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
