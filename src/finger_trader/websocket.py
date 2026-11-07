"""Ticket-authenticated JSON market-data WebSocket client.

The supported envelope follows Finger_desk's ``WsBaseModel`` protocol. The
client is synchronous: call :meth:`recv` or pass a callback to
:meth:`subscribe` to drive incoming frames and keepalive handling.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import deque
from threading import RLock
from typing import Any
from urllib.parse import quote, urlsplit

from .exceptions import APIError, NetworkError
from .transport import HTTPTransport

MAX_MESSAGE_BYTES = 1024 * 1024
HEARTBEAT_ACTION = 1
HEARTBEAT_MSG_TYPE = 0
MARKET_ACTION = 3
SUBSCRIBE_QUOTES_MSG_TYPE = 1


class MarketWebSocket:
    """Synchronous WebSocket client with bounded reconnect and resubscription."""

    def __init__(
        self,
        auth_base: str,
        *,
        token: str | None = None,
        token_type: str = "Bearer",
        timeout: float = 10,
        max_reconnect_attempts: int = 3,
        heartbeat_interval: float = 20,
        on_error=None,
    ):
        parsed = urlsplit(auth_base)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("auth_base must be an absolute HTTPS URL")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("HTTP socket auth is only allowed for loopback development URLs")
        if max_reconnect_attempts < 0 or max_reconnect_attempts > 10:
            raise ValueError("max_reconnect_attempts must be between 0 and 10")
        if heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be positive")
        self.auth_base = auth_base.rstrip("/")
        self.token, self.token_type, self.timeout = token, token_type, timeout
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_interval = heartbeat_interval
        self.on_error = on_error
        self._ws: Any | None = None
        self._transport = HTTPTransport(self.auth_base, timeout, token=token, token_type=token_type)
        self._subscriptions: set[str] = set()
        self._last_activity = time.monotonic()
        self._last_heartbeat: float | None = None
        self._last_heartbeat_sent: float | None = None
        self._seen: set[str] = set()
        self._seen_queue: deque[str] = deque(maxlen=2048)
        self._lock = RLock()
        self._closed = False
        self.log = logging.getLogger("finger_trader.websocket")

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._closed

    @staticmethod
    def parse_message(message):
        if isinstance(message, bytes):
            if len(message) > MAX_MESSAGE_BYTES:
                raise ValueError("WebSocket message exceeds the 1 MiB limit")
            message = message.decode("utf-8")
        elif len(message.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise ValueError("WebSocket message exceeds the 1 MiB limit")
        data = json.loads(message)
        if not isinstance(data, dict):
            raise ValueError("WebSocket frame must be a JSON object")
        return data

    def connect(self):
        if self._closed:
            raise RuntimeError("WebSocket client is closed")
        try:
            import websocket
        except ImportError as exc:
            raise RuntimeError(
                "WebSocket support needs the optional dependency; install "
                "finger-trader-sdk[websocket]."
            ) from exc
        response = self._transport.request(
            "POST", "/ws-api/v1/auth/build-ticket", authenticated=True
        )
        ticket_data = response.data
        if isinstance(ticket_data, dict):
            ticket = ticket_data.get("ticket") or ticket_data.get("data")
        else:
            ticket = ticket_data
        if not isinstance(ticket, str) or not ticket:
            raise APIError(
                "WebSocket ticket response did not contain a ticket", code="INVALID_TICKET"
            )
        scheme = "wss" if self.auth_base.startswith("https://") else "ws"
        netloc = urlsplit(self.auth_base).netloc
        socket_url = f"{scheme}://{netloc}/ws?ticket={quote(ticket, safe='')}"
        # The ticket must be sent in the query by the existing protocol. Never
        # follow redirects: that URL itself is a short-lived credential.
        try:
            self._ws = websocket.create_connection(
                socket_url, timeout=self.heartbeat_interval, redirect_limit=0
            )
        except Exception:
            # The dependency may include the URL (and ticket) in its exception.
            raise NetworkError("WebSocket handshake failed", code="WS_HANDSHAKE_FAILED") from None
        status = getattr(getattr(self._ws, "handshake_response", None), "status", 101)
        if status != 101:
            self._ws.close()
            self._ws = None
            raise NetworkError(
                "WebSocket server returned a non-upgrade response", code="WS_HANDSHAKE_FAILED"
            )
        self._last_activity = time.monotonic()
        self._last_heartbeat = None
        self._last_heartbeat_sent = None
        return self

    def _frame(self, action: int, msg_type: int, content):
        now = str(int(time.time() * 1000))
        return {
            "action": action,
            "msgType": msg_type,
            "timestamp": now,
            "msgId": uuid.uuid4().hex,
            "content": content,
        }

    def _send_subscription(self):
        if self._ws is None:
            self.connect()
        assert self._ws is not None
        frame = self._frame(
            MARKET_ACTION, SUBSCRIBE_QUOTES_MSG_TYPE, {"tickerList": sorted(self._subscriptions)}
        )
        self._ws.send(json.dumps(frame, separators=(",", ":")))

    def subscribe(self, tickers, *, market="stock", on_message=None):
        if market not in {"stock", "crypto", "forex", "spot", "indices"}:
            raise ValueError("unsupported market")
        # The confirmed wire DTO carries tickerList only, so no market field is sent.
        if isinstance(tickers, str):
            tickers = [tickers]
        values = {str(item).strip() for item in tickers}
        if not values or "" in values:
            raise ValueError("tickers must contain at least one non-empty ticker")
        with self._lock:
            self._subscriptions.update(values)
            try:
                self._send_subscription()
            except Exception:
                self._reconnect()
        if on_message is None:
            return self
        while not self._closed:
            message = self.recv()
            if message is not None:
                on_message(message)
        return self

    def unsubscribe(self, tickers):
        """Replace the quote subscription with the remaining ticker set.

        Finger_desk's sender documents that each subscription frame replaces
        the existing rooms. No separate unsubscribe action is known.
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        with self._lock:
            self._subscriptions.difference_update(str(item) for item in tickers)
            try:
                self._send_subscription()  # empty list clears all quote rooms
            except Exception:
                self._reconnect()
        return self

    def _reconnect(self):
        last_error = None
        if self._ws is not None:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        for attempt in range(self.max_reconnect_attempts):
            if self._closed:
                break
            if self._ws is not None:
                try:
                    self._ws.close()
                except Exception:
                    pass
                self._ws = None
            time.sleep(min(0.25 * (2**attempt), 2.0))
            try:
                self.connect()
                if self._subscriptions:
                    self._send_subscription()
                return
            except Exception as exc:
                last_error = exc
                if self.on_error:
                    self.on_error(
                        NetworkError("WebSocket reconnect failed", code="WS_RECONNECT_FAILED")
                    )
        if last_error is not None:
            raise NetworkError(
                "WebSocket reconnect attempts exhausted", code="WS_RECONNECT_FAILED"
            ) from None
        raise NetworkError("WebSocket connection closed", code="WS_CLOSED")

    def recv(self):
        if self._closed:
            raise RuntimeError("WebSocket client is closed")
        if self._ws is None:
            self.connect()
        assert self._ws is not None
        try:
            raw = self._ws.recv()
            if raw is None:
                self._reconnect()
                return None
            message = self.parse_message(raw)
            self._last_activity = time.monotonic()
            msg_id = message.get("msgId")
            if msg_id is not None and str(msg_id) in self._seen:
                return None
            if msg_id is not None:
                if len(self._seen_queue) == self._seen_queue.maxlen:
                    self._seen.discard(self._seen_queue[0])
                self._seen_queue.append(str(msg_id))
                self._seen.add(str(msg_id))
            if message.get("action") == HEARTBEAT_ACTION:
                self._last_heartbeat = self._last_activity
            return message
        except Exception as exc:
            if self._closed:
                return None
            if "timeout" in type(exc).__name__.lower():
                now = time.monotonic()
                if (
                    self._last_heartbeat_sent is not None
                    and now - self._last_heartbeat_sent >= 2 * self.heartbeat_interval
                    and (
                        self._last_heartbeat is None
                        or self._last_heartbeat < self._last_heartbeat_sent
                    )
                ):
                    self._reconnect()
                elif (
                    self._last_heartbeat_sent is None
                    or now - self._last_heartbeat_sent >= self.heartbeat_interval
                ):
                    try:
                        self.keepalive()
                        self._last_heartbeat_sent = now
                    except Exception:
                        if self.on_error:
                            self.on_error(
                                NetworkError(
                                    "WebSocket heartbeat failed", code="WS_HEARTBEAT_FAILED"
                                )
                            )
                        self._reconnect()
                elif now - self._last_heartbeat_sent >= 3 * self.heartbeat_interval:
                    self._reconnect()
                return None
            if self.on_error:
                self.on_error(NetworkError("WebSocket receive failed", code="WS_RECEIVE_FAILED"))
            self._reconnect()
            return None

    def keepalive(self):
        """Send the exact keepalive envelope used by Finger_desk."""
        if self._ws is None:
            raise RuntimeError("WebSocket is not connected")
        self._ws.send(
            json.dumps(
                self._frame(HEARTBEAT_ACTION, HEARTBEAT_MSG_TYPE, ""),
                separators=(",", ":"),
            )
        )
        self._last_heartbeat_sent = time.monotonic()

    def close(self):
        self._closed = True
        with self._lock:
            if self._ws is not None:
                self._ws.close()
                self._ws = None
            self._transport.close()

    def __enter__(self):
        return self.connect()

    def __exit__(self, *_exc):
        self.close()
