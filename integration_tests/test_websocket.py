"""Real JSON quote socket test, including heartbeat and recovery after disconnect."""

from __future__ import annotations

import json
import time
from urllib.parse import urlsplit

import pytest

from finger_trader.transport import HTTPTransport


class _FrameProbe:
    """Observe outgoing JSON frames while forwarding to the real socket."""

    def __init__(self, socket):
        self._socket = socket
        self.sent_frames = []

    def send(self, payload, *args, **kwargs):
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict):
                self.sent_frames.append(parsed)
        return self._socket.send(payload, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._socket, name)


def _recv_until(stream, predicate, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = stream.recv()
        if message is not None and predicate(message):
            return message
    raise AssertionError("Timed out waiting for the expected JSON WebSocket message")


def test_quote_ticket_heartbeat_and_reconnect(live_client, integration_config, monkeypatch):
    if not integration_config.ticker:
        pytest.skip("Set FINGER_TRADER_IT_TICKER to a valid quote ticker")

    import websocket

    original_create_connection = websocket.create_connection
    original_request = HTTPTransport.request
    probes = []
    socket_urls = []
    ticket_requests = []

    def create_connection(url, *args, **kwargs):
        parsed_url = urlsplit(url)
        socket_urls.append((parsed_url.scheme, parsed_url.path, bool(parsed_url.query)))
        probe = _FrameProbe(original_create_connection(url, *args, **kwargs))
        probes.append(probe)
        return probe

    def request(transport, method, path, *args, **kwargs):
        if path == "/ws-api/v1/auth/build-ticket":
            ticket_requests.append(method)
        return original_request(transport, method, path, *args, **kwargs)

    monkeypatch.setattr(websocket, "create_connection", create_connection)
    monkeypatch.setattr(HTTPTransport, "request", request)

    heartbeat_interval = min(max(integration_config.timeout, 1.0), 5.0)
    stream = live_client.websocket(
        heartbeat_interval=heartbeat_interval,
        max_reconnect_attempts=2,
    )
    try:
        stream.connect()
        stream.subscribe(integration_config.ticker, market=integration_config.market)

        assert ticket_requests == ["POST"]
        expected_path = f"{urlsplit(integration_config.socket_auth_url).path.rstrip('/')}/ws"
        first_scheme, first_path, has_ticket_query = socket_urls[0]
        assert first_scheme == "wss"
        assert first_path == expected_path
        assert has_ticket_query

        _recv_until(
            stream,
            lambda frame: (
                frame.get("action") == 3
                and frame.get("msgType") == 0
                and isinstance(frame.get("content"), dict)
                and frame["content"].get("ticker") == integration_config.ticker
            ),
            integration_config.timeout,
        )

        stream.keepalive()
        assert any(
            frame.get("action") == 1 and frame.get("msgType") == 0 and frame.get("content") == ""
            for frame in probes[0].sent_frames
        )
        _recv_until(
            stream,
            lambda frame: frame.get("action") == 1,
            integration_config.timeout,
        )

        # Close the real underlying connection to exercise the SDK's bounded
        # reconnect and resubscription code; this does not change account state.
        probes[-1]._socket.close()
        stream.recv()

        assert stream.connected
        assert len(probes) >= 2
        assert len(ticket_requests) >= 2
        assert any(
            frame.get("action") == 3
            and frame.get("msgType") == 1
            and frame.get("content", {}).get("tickerList") == [integration_config.ticker]
            for frame in probes[-1].sent_frames
        )
        _recv_until(
            stream,
            lambda frame: (
                frame.get("action") == 3
                and frame.get("msgType") == 0
                and isinstance(frame.get("content"), dict)
                and frame["content"].get("ticker") == integration_config.ticker
            ),
            integration_config.timeout,
        )
    finally:
        stream.close()
