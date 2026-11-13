# SDK architecture and scope

[English](architecture.md) | [日本語](architecture.md) | [繁體中文](architecture.md) | [한국어](ko/architecture.md) | [العربية](architecture.md)


The package has three distinct areas: synchronous Finger Trader API access, Desktop-hosted strategies, and independent local signal utilities. Each has its own execution and data model. The HTTP client does not run strategies or simulate trades.

## API client

- `FingerTraderClient` owns the HTTP transports and composes `auth`, `market_data`, `accounts`, `positions`, and `orders` services.
- The standard-library HTTP transport handles JSON/form requests, TLS verification, response bounds, redirect rejection, and credential-safe logging.
- Service methods preserve successful API envelopes as `ApiResponse`; data fields remain backend-shaped for compatibility.
- `MarketWebSocket` is a separate synchronous ticket-based JSON quote stream with bounded reconnect and resubscription. Its dependency is optional.
- Public exceptions distinguish API failures, network failures, and ambiguous write outcomes.

See [Public API reference](api-reference.md), [API mapping](api-mapping.md), and [Models](models.md).

## Desktop-hosted strategies

`finger_trader.hosted.Strategy` and `Context` implement the frozen Python API contract. Public dataclasses are immutable, numeric financial fields use `Decimal`, and time fields use UTC-aware `datetime`. `Context` is a Protocol; an active worker callback receives the internal run-bound implementation.

The Desktop Host starts `finger_trader.hosted.worker`, freezes the run identity and capabilities, and dispatches serial lifecycle callbacks. A separate reader handles bidirectional JSON-RPC while synchronous context calls wait for responses. The Host owns callback deadlines and confirms resource cleanup; user stdout is redirected to stderr to protect the protocol. POSIX disconnect handling terminates the worker-owned process group, including ordinary child processes. This is a boundary for trusted local code, not a security sandbox.

The SDK supplies the worker and typed service requests. The Desktop Host supplies market input, account/history/output services, persistence, and capability decisions. The current P1 integration has no broker, matcher, or trading ledger; unsupported trading requests fail explicitly. See [Hosted strategies](hosted-strategies.md), [contract](quant/python-managed-api-v1.md), and [status](quant/p1-hosted-status.md).

## Local strategy utilities

`Bar`, indicators, strategy hooks, intent signals, and `StrategyRunner` are local Python utilities. The runner dispatches caller-provided bars chronologically and collects strategy signals; it does not fetch market data, backtest, simulate fills, manage a portfolio, or submit orders. A signal represents intent only.

## Explicit scope gaps

The current SDK has no historical backtesting engine, optimizer, paper-trading simulator, arbitrary account selector, HTTP quote snapshot, execution-history endpoint, or supported current-app order mutation methods. Hosted order signatures define the future service contract; they do not supply these engines. Local signal utilities and raw payload wrappers also do not provide them.
