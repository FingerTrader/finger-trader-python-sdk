# WebSocket market data

[English](websocket.md) | [日本語](websocket.md) | [繁體中文](websocket.md) | [한국어](websocket.md) | [العربية](websocket.md)


From the cloned repository, install the optional extra:

```sh
python -m pip install '.[websocket]'
```

Connect, subscribe, receive, and close:

```python
import os

from finger_trader import APIError, FingerTraderClient, NetworkError

try:
    with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
        with client.websocket(heartbeat_interval=20) as socket:
            socket.subscribe(["AAPL", "MSFT"], market="stock")
            try:
                while True:
                    message = socket.recv()
                    if message is not None:
                        print(message)
            except KeyboardInterrupt:
                pass
except NetworkError as exc:
    print(f"WebSocket request failed: {exc}")
except APIError as exc:
    print(f"API request failed: {exc}")
```

The wire format uses the Finger_desk base envelope encoded as UTF-8 JSON in a **binary WebSocket frame**: market action `3`, quote subscribe message type `1`, and `content.tickerList`. Heartbeats use the same binary framing. The ticket is requested from `/ws-api/v1/auth/build-ticket` and passed in `/ws?ticket=...`. The handshake omits `Origin`, matching Finger Desk's Dart WebSocket client. The market identifier is not present in this confirmed DTO, so ticker strings must follow the server's own naming conventions.

Finger_desk sends keepalive action `1`, message type `0`, and empty string content. `recv()` handles socket timeouts, sends that keepalive, and detects missing acknowledgements. On a disconnect it attempts a bounded exponential reconnect, obtains a fresh ticket, and resends the current ticker union. Message IDs are deduplicated in a bounded recent-message window. `unsubscribe()` resends the remaining ticker set; an empty list clears quote rooms because the desktop sender documents that a subscription frame replaces the current room set.

This API is synchronous: call `recv()` regularly or use `socket.subscribe(tickers, on_message=callback)`, which drives the receive loop until the socket is closed (for example from another thread). `unsubscribe(tickers)` removes those symbols from the local subscription set and resends the full remaining list; an empty list clears all quote rooms. `close()` releases the socket. Reconnect attempts are bounded by `max_reconnect_attempts` (default 3), and the active symbol set is resent after reconnect. Pass `on_error=` when creating the socket to receive sanitized reconnect/heartbeat notices. The SDK does not claim protobuf support or account/order event subscriptions.
