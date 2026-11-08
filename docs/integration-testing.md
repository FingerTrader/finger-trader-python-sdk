# Live API integration tests

The opt-in suite in `integration_tests/` is separate from the Mock-only unit
tests in `tests/`. It supports `sandbox`, `dev`, and `production-read-only`
targets. Every configured endpoint must use HTTPS; the SDK upgrades the socket
connection to WSS, and the system TLS trust store remains enabled.

## Install and configure

```sh
python -m pip install -e '.[dev,websocket]'
cp integration_tests/.env.integration.example .env.integration
```

Edit the ignored `.env.integration` file with the exact API, auth, and socket
auth base URLs supplied by the service operator. For production, set:

```sh
FINGER_TRADER_IT_ENABLED=1
FINGER_TRADER_IT_TARGET=production-read-only
FINGER_TRADER_IT_CONFIRM_PRODUCTION_READ_ONLY=YES
```

For Sandbox or Dev, set `FINGER_TRADER_IT_TARGET=sandbox` or `dev`, and
`FINGER_TRADER_IT_CONFIRM_NON_PROD=YES`. Production confirmation is deliberately
separate from the non-production confirmation. Both modes require explicit
URLs and explicit opt-in; production is never selected implicitly.

Choose one authentication mode:

- `FINGER_TRADER_IT_AUTH_MODE=token`: provide a short-lived
  `FINGER_TRADER_IT_ACCESS_TOKEN`.
- `FINGER_TRADER_IT_AUTH_MODE=password`: provide
  `FINGER_TRADER_IT_OAUTH_BASIC_TOKEN`, `FINGER_TRADER_IT_USERNAME`,
  `FINGER_TRADER_IT_PASSWORD`, and the server-issued integer
  `FINGER_TRADER_IT_LOGIN_TYPE`. CAPTCHA fields can be set if required.

The OAuth Basic value is the Base64 payload without the `Basic ` prefix. Obtain
it from the service owner. Do not use a historical desktop value unless its
client classification and production permission have been confirmed. Never
commit credentials or paste them into CI logs/issues. `.env.integration` is
ignored by Git.

Additional selectors are optional and should use values confirmed for the
account/deployment:

- `FINGER_TRADER_IT_MARKET` selects the history market (default `stock`).
- `FINGER_TRADER_IT_TICKER` and `FINGER_TRADER_IT_INTERVAL` enable one bounded
  history request. The product-list checks cover stock, forex, crypto, spot,
  and indices.
- `FINGER_TRADER_IT_ACCOUNT_MARKET` enables account profile lookup.
- `FINGER_TRADER_IT_POSITION_TYPE` and `FINGER_TRADER_IT_POSITION_IS_USD`
  select the confirmed positions query values.
- `FINGER_TRADER_IT_TIMEOUT` sets the per-request timeout (default 10 seconds,
  maximum 300 seconds).

Run the suite in the configured shell:

```sh
set -a
. ./.env.integration
set +a
python -m pytest integration_tests -v -rs
```

Without `FINGER_TRADER_IT_ENABLED=1`, tests skip without network requests. When
enabled, missing settings fail before any request. The suite does not follow
HTTP redirects, includes no credentials in URLs, retains normal TLS validation,
and uses bounded page sizes, timeouts, and WebSocket reconnect attempts.

## Production safety boundary

Production mode is read-only. It may request OAuth tokens, read market/product
lists and bars, query the authenticated profile, wallet/balance, holdings, and
the first five rows of order history, and obtain a WebSocket ticket and quote
stream. A deliberately invalid token check only confirms rejection (401/403);
it does not bypass authorization. All account operations use the identity
associated with the supplied token.

The live client fixture blocks the SDK's state-changing API transport before
network I/O. Integration tests assert that submit, update, cancel, and
take-profit/loss calls hit this blocker. No order, funds transfer, deposit,
withdrawal, or other account mutation is issued. The OAuth token request and
WebSocket ticket request are the only expected POST operations, and they do
not create or modify trading state.

The WebSocket integration test is designed to assert Ticket acquisition, WSS
connection, a quote JSON frame, keepalive acknowledgement, bounded recovery,
fresh Ticket, and quote resubscription; it closes a socket to simulate a
disconnect. These are expected assertions, not a claim that every live
environment emits a quote or that the suite passes against every deployment.
Previous live validation established subscription and heartbeat request
behavior, but received no quote frame in that session. Use a low-privilege
account and a single test process; do not parallelize against production.

Order lifecycle testing remains excluded. Write request construction and field
mapping are covered by Mock tests in `tests/test_api_client.py`.

## Results and CI

With no credentials, the suite skips and makes no network calls, so ordinary
CI remains independent of production access. To exercise live services, run
the suite locally with the explicit configuration above. A passed test means
the configured principal could perform that specific request at that time; it
does not assert that every account or every production deployment has the same
permissions or data.
