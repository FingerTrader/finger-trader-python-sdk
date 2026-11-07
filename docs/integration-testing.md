# Sandbox and Dev integration tests

The live integration suite is separate from the Mock-only unit suite in
`tests/`. It never runs against the production defaults, and it sends no
order-creation or other trading-state mutation requests. It covers OAuth or an
operator-issued access token, markets, products, historical bars, account
profile, balance, positions, and the JSON quote WebSocket protocol.

## Requirements

Ask the Finger Trader service owner for all of the following before enabling
the suite:

- A dedicated Sandbox or non-production Dev deployment.
- The three HTTPS base URLs: app API, auth API, and socket auth API. The socket
  auth base must route the WebSocket connection under its `/ws` child path.
- Either a short-lived Sandbox access token, or an approved OAuth password
  test account, login type, and operator-provided OAuth Basic value.
- A valid market name, ticker, K-line interval, account market enum, and
  test-account position currency setting. These values depend on the service
  deployment and are not guessed by the test suite.
- Confirmation from the service owner that the endpoints and account are
  non-production and safe for read-only integration checks.

The SDK does not define a sandbox URL. Every endpoint must be supplied
explicitly. The test suite rejects the known production API host, requires
HTTPS, and requires two explicit opt-in settings. Operators must still confirm
that custom hostnames route to non-production services.

## Configure

Install from a local clone:

```sh
python -m pip install -e '.[dev,websocket]'
cp integration_tests/.env.integration.example .env.integration
```

Edit `.env.integration` with the service-owner-provided values. The example is
disabled by default and contains no usable credentials. Select one mode:

- `FINGER_TRADER_IT_AUTH_MODE=token`: set a short-lived
  `FINGER_TRADER_IT_ACCESS_TOKEN`.
- `FINGER_TRADER_IT_AUTH_MODE=password`: set the Basic OAuth value, username,
  password, and server login type. CAPTCHA values are optional when required
  by the service.

The `*_OAUTH_BASIC_TOKEN` value is the Base64 credential payload without the
`Basic ` prefix. Obtain it from the service owner; do not copy the historical
desktop value into your environment unless the owner confirms it is approved
for this Sandbox client.

Quote shell values that contain whitespace or shell-special characters. The
`.env.integration` file is ignored by Git; keep it local and do not attach it to
issues or CI logs.

For a POSIX shell, source the ignored file and run the separate suite:

```sh
set -a
. ./.env.integration
set +a
python -m pytest integration_tests -v -rs
```

Without `FINGER_TRADER_IT_ENABLED=1`, pytest reports skipped tests and sends no
requests. With opt-in enabled but incomplete endpoint configuration, tests
fail early with the missing setting name. Missing optional ticker or account
market settings skip only the corresponding checks.

## Coverage and safety

The suite performs read-only API calls. Password mode exercises the actual
`POST /oauth2/token` flow; token mode verifies the supplied token by making the
authenticated read calls. The WebSocket test checks Ticket acquisition, the
configured `/ws` route, a quote frame, the confirmed keepalive frame and server
keepalive traffic, then closes the live socket to verify reconnect and quote
resubscription. WebSocket credentials are kept out of assertion output.

Order request construction and backend field mapping are tested in
`tests/test_api_client.py` with a Mock HTTP transport. No live order lifecycle
test is provided. Add one only after the service owner supplies an isolated
Sandbox trading account, confirms the order enum values and reset procedure,
and separately approves that controlled write test.

Ordinary CI runs `integration_tests` without credentials; the suite skips and
does not make production calls. Unit tests remain in `tests/` and always run.
