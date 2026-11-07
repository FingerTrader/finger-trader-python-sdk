# Finger Trader Python SDK

Official Python package for connecting to the Finger Trader APIs used by Finger_desk. Python 3.10+. HTTP support uses only Python's standard library. The existing local strategy, indicator, and chronological runner APIs remain available.

## Install

```sh
python -m pip install finger-trader-sdk
```

## Quick start

```python
import os
from finger_trader import FingerTraderClient

client = FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"])
markets = client.market_data.markets()
symbols = client.market_data.symbols(market="stock")
bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d")
balance = client.accounts.balance()
positions = client.positions.list()
orders = client.orders.history()
```

OAuth password login is available using the exact Finger_desk request shape:

```python
client = FingerTraderClient()
client.auth.login("user@example.com", "password", account_type=1)
```

Use a valid server login type, and pass CAPTCHA fields when required by the service. Never embed credentials in source. The SDK does not invent refresh-token behavior; log in again after expiration.

## Supported API surface

- Auth: OAuth2 password token and CAPTCHA request.
- Market data: market menu, supported market-specific symbol lists, and historical OHLCV.
- Accounts: authenticated trade profile and wallet overview/balance.
- Positions: session-scoped holdings.
- Orders: submit, history, update limit order, cancel limit order, set stop loss/take profit.
- WebSocket: ticket-based quote subscription, using JSON text protocol.

See [API mapping](docs/api-mapping.md) for endpoints, actual parameters, and limitations; [Quick Start](docs/quickstart.md) for executable snippets; and [Errors](docs/errors.md) for response handling. A read-only runnable example is in `examples/api_read_only.py`.

The SDK returns `ApiResponse` envelopes and retains raw payload fields for forward compatibility. `MarketBar.from_dict` parses numeric OHLCV values as `Decimal`. Existing strategy `Bar` remains unchanged.

## Orders are opt-in

Order requests change live account state. They are never retried automatically. See the guarded live-order example in the Quick Start before using it, and confirm server enum values and account permissions for each instrument. The SDK does not simulate fills or add trading rules.

## WebSocket optional package

Install `websocket-client` separately to use the optional socket adapter:

```sh
python -m pip install websocket-client
```

The SDK's default HTTP usage has no third-party runtime dependency. WebSocket currently supports ticket acquisition and JSON quote subscription; binary protobuf deployments, heartbeat, reconnect and unsubscribe are not implemented.

## Development

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Scope

This repository currently provides API access plus the existing local strategy primitives. It does not include a backtesting engine, optimizer, Flutter UI, local runner process, paper trading, or cloud strategy hosting. Features without a confirmed Finger_desk backend contract are listed as gaps rather than represented as implemented. See [API mapping](docs/api-mapping.md).

Licensed under Apache-2.0. Access to Finger Trader services and market data remains subject to account permissions and applicable third-party terms.
