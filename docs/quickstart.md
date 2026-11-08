# Quick start

Install from the GitHub checkout as described in [Installation](installation.md). The SDK is not yet on PyPI.

## Use an existing access token

Set `FINGER_TRADER_ACCESS_TOKEN` in your shell or secret manager, then run:

```python
import os
from finger_trader import APIError, FingerTraderClient, NetworkError

try:
    with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
        markets = client.market_data.markets()
        symbols = client.market_data.symbols(market="stock", page_size=10)
        bars = client.market_data.history(
            market="stock", ticker="AAPL", interval="1d", limit=100
        )
        profile = client.accounts.detail()
        wallet = client.accounts.balance()
        holdings = client.positions.list()
        order_history = client.orders.history(limit=10)
        for response in (markets, symbols, bars, profile, wallet, holdings, order_history):
            print(response.data)
except NetworkError as exc:
    print(f"Network request failed: {exc}")
except APIError as exc:
    print(f"Finger Trader API request failed: {exc}")
```

Do not print tokens or full authentication responses. Service payloads are returned in `ApiResponse.data` with backend field names intact. For login instead, see [Authentication](authentication.md). For methods and return types, see the [API reference](api-reference.md).

## Real-time quotes

Install the optional WebSocket extra and follow [WebSocket](websocket.md). There is no confirmed HTTP snapshot API.

## Trading actions

The current SDK does not provide supported order create, modify, cancel, or close operations for the active app API. Legacy mutation wrappers are not safe to call against the current endpoint contract. No order is submitted by any quick start or included API example.
