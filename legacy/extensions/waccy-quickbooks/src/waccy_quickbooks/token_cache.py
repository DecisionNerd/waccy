"""Small file-backed token cache for QuickBooks OAuth state."""

from __future__ import annotations

from pathlib import Path

from waccy_quickbooks.models import QuickBooksToken


class FileTokenCache:
    """Persist QuickBooks OAuth tokens in a caller-owned JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()

    def load(self) -> QuickBooksToken | None:
        """Load a token if the cache exists."""
        if not self.path.exists():
            return None
        return QuickBooksToken.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, token: QuickBooksToken) -> None:
        """Write the token cache with owner-only permissions where supported."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(token.model_dump_json(indent=2), encoding="utf-8")
        self.path.chmod(0o600)

    def clear(self) -> None:
        """Remove cached token state if present."""
        if self.path.exists():
            self.path.unlink()
