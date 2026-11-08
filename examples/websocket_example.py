"""Subscribe to one quote stream. Requires the optional websocket extra."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    tickers = [item.strip() for item in os.environ.get("FINGER_TRADER_TICKERS", "AAPL").split(",")]
    try:
        with FingerTraderClient(token=token) as client:
            with client.websocket(max_reconnect_attempts=3, heartbeat_interval=20) as socket:
                socket.subscribe(tickers, market=os.environ.get("FINGER_TRADER_MARKET", "stock"))
                print("Subscribed. Press Ctrl-C to stop.")
                try:
                    while True:
                        message = socket.recv()
                        if message is not None:
                            print(message)
                except KeyboardInterrupt:
                    print("Stopping quote stream.")
    except NetworkError as exc:
        raise SystemExit(f"WebSocket or ticket request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None
    except RuntimeError as exc:
        raise SystemExit(f"WebSocket setup failed: {exc}") from None


if __name__ == "__main__":
    main()
