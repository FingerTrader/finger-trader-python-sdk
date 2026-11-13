# Public API reference

[English](api-reference.md) | [日本語](api-reference.md) | [繁體中文](api-reference.md) | [한국어](ko/api-reference.md) | [العربية](api-reference.md)


This is a concise reference to the current exported client surface. All HTTP service calls return `ApiResponse` unless noted. Request methods and exact backend payload mappings are listed in [API mapping](api-mapping.md).

## Client lifecycle

`FingerTraderClient(*, token=None, token_type="Bearer", oauth_basic_token=None, base_url=None, auth_url=None, socket_auth_url=None, timeout=10, environment="prod")`

Use as a context manager or call `.close()`. `.set_token(access_token, token_type="Bearer", expires_in=None)` sets an in-memory token. `.websocket(**kwargs)` creates a `MarketWebSocket`; install the WebSocket extra first.

## Services

- `client.auth.login(username, password, *, account_type, captcha_id=None, captcha_code=None)` — OAuth password grant. `account_type` is required (`0` email, `1` mobile). Returns `ApiResponse` whose `.data` is `AuthToken`.
- `client.auth.check()` / `.is_authenticated` — local token presence/expiry check; no server call. `.captcha()` requests a CAPTCHA. `.refresh()` is not implemented.
- `client.market_data.markets()` — market menu.
- `client.market_data.symbols(market="stock", page=1, page_size=50)` — product page. Supported labels: forex, spot, crypto, stock, etf, fund, indices.
- `client.market_data.history(*, market, ticker, interval, limit=200, page=1, start_time=None)` / `.get_history(...)` — historical OHLCV. Only crypto, stock, forex, and spot are accepted; `page` must remain 1. Use a timezone-aware `datetime` or epoch milliseconds for `start_time` to request an earlier window.
- `client.market_data.quote(ticker)` — raises `NotImplementedError`; no HTTP snapshot endpoint is confirmed. `.subscribe_quotes(...)` is the WebSocket entry point.
- `client.accounts.list()` / `.detail(market=None)` — authenticated, session-scoped profile. `market` remains accepted for compatibility and is ignored.
- `client.accounts.balance()` — current session wallet/balance payload.
- `client.positions.list(*, account_id=None, order_status=0, is_usd=False, page=1, page_size=100, market_type=None)` — holdings endpoint. `account_id` is not supported and raises `ValueError`; identity comes from the token session.
- `client.orders.history(*, page=1, limit=20, filters=None)` — order history. Filter keys may be snake_case or backend camelCase: wallet_type, market_type, order_type, coin_type, order_side, start_time, end_time.
- `client.orders.executions()` — raises `NotImplementedError`; no confirmed execution endpoint.

## WebSocket

`socket = client.websocket(*, max_reconnect_attempts=3, heartbeat_interval=20, on_error=None)`; then `socket.connect()`, `socket.subscribe(tickers, market="stock", on_message=None)`, `socket.recv()`, `socket.keepalive()`, `socket.unsubscribe(tickers)`, and `socket.close()`. `subscribe` returns the socket unless a callback is supplied, in which case it drives a receive loop until closed. Context manager use is supported.

## Exceptions

`APIError` and `NetworkError` describe failed API/transport operations. `UnknownOutcomeError` indicates an ambiguous state-changing request and requires reconciliation before any retry. `ValueError` indicates invalid local arguments; unsupported operations raise `NotImplementedError`. See [Error handling](errors.md).

## Hosted strategy API

The hosted API is imported explicitly from `finger_trader.hosted`; root-level `Strategy`, `Bar`, and account/order wrappers retain their independent meanings.

- `Strategy(**parameters)` exposes immutable `parameters` and a Host-bound `context`.
- Lifecycle: `on_start(context)`, `on_bar(bar)`, `on_stop()`; all are synchronous and return `None`.
- Context queries: `history(...)`, `account()`, `position()`, `get_order(order_id)`.
- Context trading requests: `submit_order(...)`, `cancel_order(order_id)`, `exit_protected(group_id, quantity)`; require stage permission and Host capabilities. The current P1 Desktop integration does not implement trading.
- Context output: `log(...)`, `plot(...)`, `marker(...)`; acknowledgement exposes whether output was accepted.
- Models use `Decimal`, UTC-aware `datetime`, immutable containers, and keyword-only construction. Exceptions derive from `HostedError` and expose stable business `code` values.

For signatures, defaults, models, and errors, see [Hosted strategies](hosted-strategies.md), [the full contract](quant/python-managed-api-v1.md), and the [type declarations](../contracts/quant/python/finger_trader/hosted/__init__.pyi). HTTP `ApiResponse` and `APIError` do not describe hosted IPC results.
