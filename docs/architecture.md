# SDK architecture and scope

The package has two separate public areas: synchronous Finger Trader API access and local strategy utilities. The API client does not run strategies or simulate trades.

## API client

- `FingerTraderClient` owns the HTTP transports and composes `auth`, `market_data`, `accounts`, `positions`, and `orders` services.
- The standard-library HTTP transport handles JSON/form requests, TLS verification, response bounds, redirect rejection, and credential-safe logging.
- Service methods preserve successful API envelopes as `ApiResponse`; data fields remain backend-shaped for compatibility.
- `MarketWebSocket` is a separate synchronous ticket-based JSON quote stream with bounded reconnect and resubscription. Its dependency is optional.
- Public exceptions distinguish API failures, network failures, and ambiguous write outcomes.

See [Public API reference](api-reference.md), [API mapping](api-mapping.md), and [Models](models.md).

## Local strategy utilities

`Bar`, indicators, strategy hooks, intent signals, and `StrategyRunner` are local Python utilities. The runner dispatches caller-provided bars chronologically and collects strategy signals; it does not fetch market data, backtest, simulate fills, manage a portfolio, or submit orders. A signal represents intent only.

## Explicit scope gaps

The current SDK has no historical backtesting engine, optimizer, paper-trading simulator, arbitrary account selector, HTTP quote snapshot, execution-history endpoint, or supported current-app order mutation methods. These features are not implied by the strategy utilities or by raw payload model wrappers.
