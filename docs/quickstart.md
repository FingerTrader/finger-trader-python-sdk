# Installation and quick start

Python 3.10+; the HTTP client uses only the standard library.

```sh
python -m pip install finger-trader-sdk
```

```python
from finger_trader import FingerTraderClient

client = FingerTraderClient()  # production API roots from Finger_desk
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
result = client.orders.submit(
    is_buy=True, is_usd=False, limit_time=0, market=1,
    order_id="", order_type=1, price="0", quantity="1",
    ticker="AAPL", is_create=1,
)
print(result.data)
```

`order_type`, `market`, `limit_time`, `is_create`, and account/currency semantics are backend-defined enums and vary by instrument. Validate these against your account and product before enabling. Network errors on POST are not retried.

## WebSocket

The optional transport imports `websocket-client`; install it separately with `python -m pip install websocket-client`, then:

```python
def show(message):
    print(message)

client.market_data.subscribe_quotes(["AAPL"], market="stock", on_message=show)
```

WebSocket callbacks run in the receive loop. Close the returned socket when finished. The current adapter obtains the Finger_desk ticket and sends quote subscribe frames. The backend protocol uses binary protobuf in some deployments; the adapter currently supports JSON text frames only. It does not yet implement reconnect, heartbeat, unsubscribe, or binary protobuf decoding.
