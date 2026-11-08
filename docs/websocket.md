# WebSocket market data

From the cloned repository, install the optional extra:

```sh
python -m pip install '.[websocket]'
```

Connect, subscribe, receive, and close:

```python
with client.websocket(heartbeat_interval=20) as socket:
    socket.subscribe(["AAPL"])
    while True:
        message = socket.recv()
        if message is not None:
            print(message)
```

The wire format uses the Finger_desk base envelope encoded as UTF-8 JSON in a **binary WebSocket frame**: market action `3`, quote subscribe message type `1`, and `content.tickerList`. Heartbeats use the same binary framing. The ticket is requested from `/ws-api/v1/auth/build-ticket` and passed in `/ws?ticket=...`. The handshake omits `Origin`, matching Finger Desk's Dart WebSocket client. The market identifier is not present in this confirmed DTO, so ticker strings must follow the server's own naming conventions.

Finger_desk sends keepalive action `1`, message type `0`, and empty string content. `recv()` handles socket timeouts, sends that keepalive, and detects missing acknowledgements. On a disconnect it attempts a bounded exponential reconnect, obtains a fresh ticket, and resends the current ticker union. Message IDs are deduplicated in a bounded recent-message window. `unsubscribe()` resends the remaining ticker set; an empty list clears quote rooms because the desktop sender documents that a subscription frame replaces the current room set.

This API is synchronous: call `recv()` regularly or use the callback form `socket.subscribe(tickers, on_message=callback)`, which drives the receive loop. The SDK does not claim binary protobuf support or account/order event subscriptions.
