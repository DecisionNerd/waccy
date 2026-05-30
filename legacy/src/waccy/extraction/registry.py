"""Extension registry and discovery for data source extractors."""

from importlib.metadata import entry_points
from typing import Protocol

from waccy.core.models import ExtractedData


class ExtractorProtocol(Protocol):
    """Protocol that all extractors must implement."""

    name: str
    data_source: str

    def extract(self, config: dict) -> ExtractedData:
        """Extract data from the source."""
        ...


class ExtractorRegistry:
    """Registry for discovering and managing data source extractors."""

    def __init__(self) -> None:
        """Initialize the registry and load extensions."""
        self._extractors: dict[str, type[ExtractorProtocol]] = {}
        self._load_extensions()

    def _load_extensions(self) -> None:
        """Discover extensions via entry points."""
        discovered = entry_points(group="waccy.extractors")
        for ep in discovered:
            try:
                extractor_class = ep.load()
            except (ImportError, ModuleNotFoundError):
                continue
            instance = extractor_class()
            self._extractors[instance.data_source] = extractor_class

    def get_extractor(self, data_source: str) -> type[ExtractorProtocol] | None:
        """Get extractor class for a data source."""
        return self._extractors.get(data_source)

    def list_extractors(self) -> list[str]:
        """List all available data sources."""
        return list(self._extractors.keys())

    def register_extractor(
        self, data_source: str, extractor_class: type[ExtractorProtocol]
    ) -> None:
        """Manually register an extractor (useful for testing)."""
        self._extractors[data_source] = extractor_class
