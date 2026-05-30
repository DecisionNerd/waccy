"""Unit tests for extraction module."""

from waccy.extraction.registry import ExtractorRegistry


def test_extractor_registry_initialization() -> None:
    """Test ExtractorRegistry initialization."""
    registry = ExtractorRegistry()
    assert isinstance(registry.list_extractors(), list)


def test_extractor_registry_list() -> None:
    """Test listing available extractors."""
    registry = ExtractorRegistry()
    extractors = registry.list_extractors()
    assert isinstance(extractors, list)

