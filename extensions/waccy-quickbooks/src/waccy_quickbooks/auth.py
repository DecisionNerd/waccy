"""QuickBooks OAuth helpers built on Intuit's official OAuth client."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from waccy_quickbooks.models import QuickBooksOAuthConfig, QuickBooksToken

ACCOUNTING_SCOPE = "com.intuit.quickbooks.accounting"


class QuickBooksOAuthClient:
    """Thin wrapper around ``intuit-oauth`` for WACCY's token model."""

    def __init__(self, config: QuickBooksOAuthConfig) -> None:
        self.config = config

    def authorization_url(self, state_token: str | None = None, scopes: list[Any] | None = None) -> str:
        """Build an Intuit authorization URL."""
        auth_client = self._auth_client(state_token=state_token)
        return str(auth_client.get_authorization_url(scopes or [self._accounting_scope()]))

    def exchange_code(self, auth_code: str, realm_id: str) -> QuickBooksToken:
        """Exchange an OAuth authorization code for bearer tokens."""
        auth_client = self._auth_client(realm_id=realm_id)
        auth_client.get_bearer_token(auth_code, realm_id=realm_id)
        return self._token_from_auth_client(auth_client, realm_id)

    def refresh(self, token: QuickBooksToken) -> QuickBooksToken:
        """Refresh a cached token and return the updated token state."""
        auth_client = self._auth_client(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            realm_id=token.realm_id,
        )
        auth_client.refresh(refresh_token=token.refresh_token)
        return self._token_from_auth_client(auth_client, token.realm_id)

    def _auth_client(self, **kwargs: Any) -> Any:
        from intuitlib.client import AuthClient  # noqa: PLC0415

        return AuthClient(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            redirect_uri=self.config.redirect_uri,
            environment=self.config.environment.value,
            **kwargs,
        )

    @staticmethod
    def _accounting_scope() -> Any:
        from intuitlib.enums import Scopes  # noqa: PLC0415

        return Scopes.ACCOUNTING

    @staticmethod
    def _token_from_auth_client(auth_client: Any, realm_id: str) -> QuickBooksToken:
        now = datetime.now(UTC)
        expires_in = int(getattr(auth_client, "expires_in", 3600) or 3600)
        refresh_expires_in = getattr(auth_client, "x_refresh_token_expires_in", None)
        return QuickBooksToken(
            access_token=str(auth_client.access_token),
            refresh_token=str(auth_client.refresh_token),
            realm_id=realm_id,
            token_type=str(getattr(auth_client, "token_type", "bearer") or "bearer"),
            expires_at=now + timedelta(seconds=expires_in),
            refresh_token_expires_at=(
                now + timedelta(seconds=int(refresh_expires_in)) if refresh_expires_in else None
            ),
        )
