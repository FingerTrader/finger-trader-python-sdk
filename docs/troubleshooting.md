# Troubleshooting

## Authentication returns 401 or 403

Check the configured auth/app URLs, token type, expiry, and the expected session permissions. Password login requires the service-issued OAuth Basic value and `account_type=0` for email or `1` for mobile. The SDK does not refresh tokens; authenticate again when expired. A 403 is an authorization result, not a signal to try another account identifier.

## Login fails or CAPTCHA is required

Use the OAuth Basic payload supplied by the service owner, without the `Basic ` prefix. Pass `captcha_id` and `captcha_code` only when the authentication flow requires them. `auth.check()` is local-only and does not validate a token with the server.

## API URL or TLS error

Use the service operator's complete base URL for the app API, auth API, and socket-auth API. Non-loopback HTTP is rejected; production TLS verification is always enabled and redirects are not followed. Do not disable certificate verification. For private CAs, configure the host's trusted certificate store.

## Product or interval request is rejected

Use a market label supported by `market_data.symbols`; historical bars accept only `crypto`, `stock`, `forex`, or `spot`. The API's interval values are backend-defined; use a value confirmed for the selected market. Product identifiers are not normalized by the SDK.

## Empty account or history results

Accounts and positions are scoped to the authenticated session. An empty result may mean the account has no matching data or permission. Historical API coverage and interval availability vary by instrument; confirm ticker, market, requested start time, and interval. `history()` currently accepts `page=1` and uses `start_time` (epoch milliseconds or aware datetime) for its time window.

## WebSocket connects but no quote arrives

Install `.[websocket]`, verify that the ticket request and TLS handshake succeed, and use the service's exact ticker identifier. Call `recv()` regularly so the synchronous client can process heartbeat frames. Quote availability depends on entitlement and market session. The SDK exposes the confirmed quote subscription protocol only; it does not implement account/order events or protobuf messages.

## WebSocket disconnects

Reconnect is bounded (default three attempts) and resends active ticker subscriptions with a newly fetched ticket. Inspect the sanitized `on_error` callback. Close the socket cleanly and create a new client after exhausted retries.

## Order result is unknown

`UnknownOutcomeError` means a state-changing request may have reached the server. Check order history or the service's authorized order interface before considering any further action. Current SDK legacy mutation methods are not supported with the app API; do not use them for live trading.

## Optional WebSocket dependency is missing

Install from the cloned project with `python -m pip install '.[websocket]'`. HTTP functionality does not require this extra.

## Hosted import is missing or uses the wrong models

Verify which checkout the selected Python imports. Use a source revision containing `src/finger_trader/hosted/`, and match the exact SDK revision required by Desktop. An old editable install can silently import another checkout. `finger_trader.hosted.Bar` and `.Strategy` are separate from the root-level signal utilities.

## Hosted Context is stale, denied, or unsupported

Do not instantiate `Context` or use it outside the active callback. Service calls must run on the callback's owning thread. Check the stage and granted capabilities. `UNSUPPORTED_CAPABILITY` is expected for current P1 trading requests; retrying or switching to legacy HTTP writes does not add a trading engine.

## A strategy file does not run by itself

The Desktop Host owns initialization, run identity, callback dispatch, services, and resource cleanup. The private worker expects a Host handshake and bidirectional JSON-RPC. Use the compatible Desktop workflow described in [Hosted strategies](hosted-strategies.md); `StrategyRunner` runs the separate local signal API.
