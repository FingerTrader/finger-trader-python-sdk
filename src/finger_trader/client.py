"""Public entry point for the Finger Trader API SDK."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

from .services.accounts import Accounts, Positions
from .services.auth import Auth
from .services.market_data import MarketData
from .services.orders import Orders
from .transport import HTTPTransport

PROD_API = "https://prod-api.fingertrader.com/finger-bff-app"
PROD_AUTH = "https://prod-api.fingertrader.com/finger-auth"
PROD_SOCKET_AUTH = "https://prod-api.fingertrader.com/finger-bff-socket"


class FingerTraderClient:
    """Synchronous API client. Tokens are kept in memory and never persisted.

    Custom endpoints are explicit developer configuration. Production defaults
    are HTTPS and the WebSocket adapter upgrades them to WSS.
    """

    def __init__(
        self,
        *,
        token: str | None = None,
        token_type: str = "Bearer",
        oauth_basic_token: str | None = None,
        base_url: str | None = None,
        auth_url: str | None = None,
        socket_auth_url: str | None = None,
        timeout: float = 10,
        environment: str = "prod",
    ):
        if environment not in {"prod", "dev", "local"}:
            raise ValueError("environment must be prod, dev, or local")
        if environment == "prod":
            api_default, auth_default, socket_default = PROD_API, PROD_AUTH, PROD_SOCKET_AUTH
        else:
            local = "http://127.0.0.1:9999"
            api_default = local + "/finger-bff-app"
            auth_default = local + "/finger-auth"
            socket_default = local + "/finger-bff-socket"
        self._api = HTTPTransport(
            base_url or api_default, timeout, token=token, token_type=token_type
        )
        self._auth = HTTPTransport(auth_url or auth_default, timeout, basic_auth=oauth_basic_token)
        self._socket_auth_url = socket_auth_url or socket_default
        socket_parts = urlsplit(self._socket_auth_url)
        if socket_parts.scheme not in {"https", "http"} or not socket_parts.hostname:
            raise ValueError("socket_auth_url must be an absolute HTTPS URL")
        if socket_parts.scheme != "https" and socket_parts.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("HTTP socket auth is only allowed for loopback development URLs")
        self.expires_at: float | None = None
        self.auth = Auth(self)
        self.market_data = MarketData(self)
        self.accounts = Accounts(self)
        self.positions = Positions(self)
        self.orders = Orders(self)
        self._closed = False
        self._websockets: set[Any] = set()

    def set_token(
        self, access_token: str, token_type: str = "Bearer", expires_in: int | None = None
    ) -> None:
        """Set an access token in memory; no refresh-token persistence is used."""
        self._api.token = access_token
        self._api.token_type = token_type
        self.expires_at = time.time() + expires_in if expires_in else None

    def _get(self, path: str, params=None):
        return self._api.request("GET", path, params=params, authenticated=True, retry_safe=True)

    def _post(self, path: str, data=None, params=None):
        return self._api.request("POST", path, body=data, params=params, authenticated=True)

    def websocket(self, **kwargs):
        from .websocket import MarketWebSocket

        socket = MarketWebSocket(
            self._socket_auth_url,
            token=self._api.token,
            token_type=self._api.token_type,
            timeout=self._api.timeout,
            **kwargs,
        )
        self._websockets.add(socket)
        return socket

    def close(self) -> None:
        """Release client resources; safe to call more than once."""
        if self._closed:
            return
        for socket in tuple(self._websockets):
            socket.close()
        self._websockets.clear()
        self._api.close()
        self._auth.close()
        self._api.token = None
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
