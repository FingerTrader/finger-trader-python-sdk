# Finger Trader Python SDK

The Finger Trader Python SDK provides synchronous HTTP API access, ticket-authenticated market-data WebSocket subscriptions, and a Desktop-hosted Python strategy API. It is an **alpha, source-install SDK** (`0.1.0`). HTTP responses preserve backend envelopes; hosted strategies use immutable Decimal/UTC models and communicate with a Desktop Host through a separate worker process.

The P1 hosted implementation is now included alongside the P0 contracts. This is a development integration: the SDK does not include a standalone backtesting engine, broker, or live execution service. See [Hosted strategies](docs/hosted-strategies.md) for the implemented API and current limits.

## Current capabilities

- OAuth2 password login and use of an existing access token.
- Market menu, product lists, and historical OHLCV requests.
- Authenticated profile, wallet/balance, holdings, and order history queries.
- Ticket-based JSON market-data WebSocket subscription (optional dependency).
- Desktop-hosted strategies under `finger_trader.hosted`: synchronous lifecycle callbacks, immutable parameters, typed context services, and a JSON-RPC worker with disconnect cleanup.
- Independent local signal tools (`StrategyRunner`, indicators, and signals) for caller-supplied bars. They remain separate from the hosted API.

Current app API order creation, modification, cancellation, and executions are **not available through a supported SDK method**. Do not use legacy mutation methods still present for compatibility; see [Orders](docs/orders.md). There is no HTTP quote snapshot endpoint, refresh-token request, arbitrary account selector, or confirmed execution-history endpoint.

## Choose an entry point

| Goal | Entry point | Guide |
|---|---|---|
| Query HTTP APIs or stream quotes | `FingerTraderClient` | [Quick start](docs/quickstart.md) |
| Write a strategy managed by Desktop | `finger_trader.hosted.Strategy` | [Hosted strategies](docs/hosted-strategies.md) |
| Experiment locally with bars and intent signals | `StrategyRunner` | [Local dual moving average example](examples/dual_ma_strategy.py) |

Hosted context methods depend on the capabilities supplied by the Host. Declaring an order method does not provide a trading engine: the current P1 Desktop integration rejects trading requests with `UNSUPPORTED_CAPABILITY`.

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
    bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=100)
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

OAuth login, environment configuration, and safe secret handling are covered in [Authentication](docs/authentication.md) and [Configuration](docs/configuration.md).

## Documentation

- [Documentation index](docs/index.md) · [Hosted strategies](docs/hosted-strategies.md)
- [Hosted API contract](docs/quant/python-managed-api-v1.md) · [Implementation status](docs/quant/p1-hosted-status.md) · [Architecture](docs/architecture.md)
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

Never commit passwords, OAuth client values, access tokens, or customer data. Production TLS verification is enabled; requests do not follow redirects. HTTP trading permissions and risk controls remain server-side. Hosted code must be trusted local code; a worker process is not a security sandbox. See [Security](docs/security.md).

Licensed under [Apache-2.0](LICENSE). API and market-data access remains subject to account authorization and applicable service terms.
