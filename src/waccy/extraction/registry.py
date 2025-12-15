"""Extension registry and discovery for data source extractors."""

from typing import Optional, Protocol, Type

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore


class ExtractorProtocol(Protocol):
    """Protocol that all extractors must implement."""

    name: str
    data_source: str

    def extract(self, config: dict) -> "ExtractedData":  # noqa: F821
        """Extract data from the source."""
        ...


class ExtractorRegistry:
    """Registry for discovering and managing data source extractors."""

    def __init__(self) -> None:
        """Initialize the registry and load extensions."""
        self._extractors: dict[str, Type[ExtractorProtocol]] = {}
        self._load_extensions()

    def _load_extensions(self) -> None:
        """Discover extensions via entry points."""
        try:
            discovered = entry_points(group="waccy.extractors")
        except TypeError:
            # Python < 3.10 compatibility
            discovered = entry_points().get("waccy.extractors", [])
        for ep in discovered:
            extractor_class = ep.load()
            instance = extractor_class()
            self._extractors[instance.data_source] = extractor_class

    def get_extractor(self, data_source: str) -> Optional[Type[ExtractorProtocol]]:
        """Get extractor class for a data source."""
        return self._extractors.get(data_source)

    def list_extractors(self) -> list[str]:
        """List all available data sources."""
        return list(self._extractors.keys())

    def register_extractor(
        self, data_source: str, extractor_class: Type[ExtractorProtocol]
    ) -> None:
        """Manually register an extractor (useful for testing)."""
        self._extractors[data_source] = extractor_class

