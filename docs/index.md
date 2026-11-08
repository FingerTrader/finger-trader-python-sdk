# Finger Trader Python SDK documentation

This guide describes the SDK's currently implemented public API. It is an alpha source distribution, not yet published to PyPI. Endpoint details are mapped from confirmed Finger_desk API calls; unsupported operations are identified explicitly.

## Start here

1. [Install from source](installation.md).
2. [Configure endpoints and credentials](configuration.md).
3. Follow the [quick start](quickstart.md).
4. Use the API guides below and review [error handling](errors.md) and [security](security.md) before production use.

## API guides

| Topic | Guide |
|---|---|
| Authentication | [OAuth2 password login and existing tokens](authentication.md) |
| Market data | [Markets, product lists, and OHLCV history](market-data.md) |
| Accounts | [Session profile and wallet](accounts.md) |
| Positions | [Current holdings](positions.md) |
| Orders | [History available; writes currently unsupported](orders.md) |
| WebSocket | [Ticket-based JSON quote subscription](websocket.md) |
| Models | [Response envelopes and exported model types](models.md) |
| Exceptions | [API, network, and unknown outcome behavior](errors.md) |
| Security | [Credential and transport protections](security.md) |
| Troubleshooting | [Common configuration and API issues](troubleshooting.md) |

Reference material: [Public API signatures](api-reference.md), [API mapping and coverage](api-mapping.md), [opt-in live integration tests](integration-testing.md).

See [Architecture and scope](architecture.md) for package boundaries and local strategy utilities.

Runnable scripts and their required environment settings are listed in [Examples](../examples/README.md).

## Support status

Implemented HTTP calls include OAuth token and CAPTCHA, market menu and product lists, historical bars, session profile, wallet, holdings, and order history. WebSocket supports ticket-authenticated JSON quote subscription. HTTP quote snapshots, refresh-token calls, execution history, and current API order mutations are not implemented in this SDK. See the mapping for exact endpoint coverage.
