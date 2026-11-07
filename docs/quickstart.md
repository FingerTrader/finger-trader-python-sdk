# Installation and quick start

Python 3.10+; the HTTP client uses only the standard library.

```sh
git clone https://github.com/FingerTrader/finger-trader-python-sdk.git
cd finger-trader-python-sdk
python -m pip install .
```

The package is not currently published on PyPI; install from GitHub until an official package release is announced.

```python
import os

from finger_trader import FingerTraderClient

client = FingerTraderClient(
    oauth_basic_token=os.environ["FINGER_TRADER_OAUTH_BASIC_TOKEN"]
)  # production API roots from Finger_desk
# Authenticate only when the account is eligible for the OAuth password flow.
client.auth.login("user@example.com", "password", account_type=1)
bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d")
print(bars.data)
print(client.accounts.balance().data)
```

Or provide an existing access token without storing it in source:

```python
import os

client = FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"])
```

`account_type` is the server's login type enum. OAuth CAPTCHA fields are optional in the DTO. Token refresh is not documented by the inspected desktop code; re-authenticate when the access token expires. HTTP response `.data` preserves the backend shape. `MarketBar.from_dict` converts numeric OHLCV values to `Decimal` where the payload keys match.

## Read-only market and account calls

```python
markets = client.market_data.markets()
stocks = client.market_data.symbols(market="stock")
bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=200, page=1)
profile = client.accounts.detail(market=0)
balance = client.accounts.balance()
positions = client.positions.list(is_usd=False)
orders = client.orders.history(page=1, limit=20)
```

These API routes are session-scoped in Finger_desk; the server does not expose an account ID parameter in the observed calls. See [API mapping](api-mapping.md) for market-specific routes and limitations.

## Explicit live order example

The SDK never submits orders automatically. This example is gated by an explicit environment flag and requires callers to supply the server's actual enum values and required fields.

```python
import os

if os.environ.get("FINGER_TRADER_ENABLE_LIVE_ORDER") != "YES":
    raise SystemExit("Set FINGER_TRADER_ENABLE_LIVE_ORDER=YES to enable this live request")
# Fill these variables only after confirming the server enum values, environment,
# instrument rules, and account permissions with Finger Trader.
result = client.orders.submit(
    is_buy=True,
    is_usd=os.environ["FINGER_TRADER_ORDER_IS_USD"] == "true",
    limit_time=int(os.environ["FINGER_TRADER_ORDER_LIMIT_TIME"]),
    market=int(os.environ["FINGER_TRADER_ORDER_MARKET"]),
    order_id="",
    order_type=int(os.environ["FINGER_TRADER_ORDER_TYPE"]),
    price=os.environ["FINGER_TRADER_ORDER_PRICE"],
    quantity=int(os.environ["FINGER_TRADER_ORDER_QUANTITY"]),
    ticker=os.environ["FINGER_TRADER_ORDER_TICKER"],
    is_create=int(os.environ["FINGER_TRADER_ORDER_IS_CREATE"]),
)
print(result.data)
```

`order_id=""` matches Finger_desk's new-order DTO. `order_type`, `market`, `limit_time`, `is_create`, and account/currency semantics are backend-defined enums and vary by instrument. This gated code submits a real order when enabled; validate every value, account, environment, and product before running it. Network errors on POST are not retried.

## WebSocket

Install the WebSocket extra from the repository with `python -m pip install '.[websocket]'`, then:

```python
import os

from finger_trader import FingerTraderClient

client = FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"])


def show(message):
    print(message)


socket = client.market_data.subscribe_quotes(["AAPL"], market="stock")
try:
    while True:
        message = socket.recv()
        if message is not None:
            show(message)
except KeyboardInterrupt:
    pass
finally:
    socket.close()
```

The current adapter obtains the Finger_desk ticket and sends quote subscribe frames. It supports the confirmed JSON text protocol with bounded reconnect, heartbeat, and replacement-list unsubscribe. Binary protobuf deployments and order/account event subscriptions are not implemented.
