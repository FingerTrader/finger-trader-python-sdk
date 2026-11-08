# Finger Trader Python SDK

The Finger Trader Python SDK is a synchronous Python client for the confirmed Finger Trader HTTP APIs and ticket-authenticated market-data WebSocket. It is an **alpha, source-install SDK** (`0.1.0`, not currently published on PyPI). The public API preserves backend response envelopes so applications can use fields as returned by the service.

## Current capabilities

- OAuth2 password login and use of an existing access token.
- Market menu, product lists, and historical OHLCV requests.
- Authenticated profile, wallet/balance, holdings, and order history queries.
- Ticket-based JSON market-data WebSocket subscription (optional dependency).
- Local strategy primitives are also present, but this package does not provide a backtester or execution runtime.

Current app API order creation, modification, cancellation, and executions are **not available through a supported SDK method**. Do not use legacy mutation methods still present for compatibility; see [Orders](docs/orders.md). There is no HTTP quote snapshot endpoint, refresh-token request, arbitrary account selector, or confirmed execution-history endpoint.

## Requirements and install

Python 3.10 or newer. PyPI installation is not available yet. See [Installation](docs/installation.md) for virtual environment and platform instructions.

```sh
git clone https://github.com/FingerTrader/finger-trader-python-sdk.git
cd finger-trader-python-sdk
python -m pip install .
```

Add WebSocket support with `python -m pip install '.[websocket]'` from the cloned repository.

## Quick start

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
    markets = client.market_data.markets()
    products = client.market_data.symbols(market="stock", page_size=10)
    bars = client.market_data.history(
        market="stock", ticker="AAPL", interval="1d", limit=100
    )
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

OAuth login, environment configuration, and safe secret handling are covered in [Authentication](docs/authentication.md) and [Configuration](docs/configuration.md).

## Documentation

- [Documentation index](docs/index.md)
- [Installation](docs/installation.md) · [Quick start](docs/quickstart.md) · [Configuration](docs/configuration.md)
- [Authentication](docs/authentication.md) · [Security](docs/security.md)
- [Market data](docs/market-data.md) · [Accounts](docs/accounts.md) · [Positions](docs/positions.md) · [Orders](docs/orders.md)
- [WebSocket](docs/websocket.md) · [Models](docs/models.md) · [Errors](docs/errors.md)
- [Public API reference](docs/api-reference.md) · [Finger_desk API mapping](docs/api-mapping.md) · [Troubleshooting](docs/troubleshooting.md)
- [Opt-in integration tests](docs/integration-testing.md)

Runnable read-only examples are in [`examples/`](examples/). Examples require developer-provided credentials only for authenticated calls and never include credentials in source.

## Support and contribution

Report bugs and request supported API coverage through [GitHub Issues](https://github.com/FingerTrader/finger-trader-python-sdk/issues). Contributions are welcome; include tests for code changes and update documentation when public behavior changes.

## Security and license

Never commit passwords, OAuth client values, access tokens, or customer data. Production TLS verification is enabled; requests do not follow redirects. Trading permissions and risk controls remain server-side. See [Security](docs/security.md).

Licensed under [Apache-2.0](LICENSE). API and market-data access remains subject to account authorization and applicable service terms.
