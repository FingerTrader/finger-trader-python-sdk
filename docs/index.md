# Finger Trader Python SDK documentation

This guide covers the HTTP/WebSocket client, independent signal tools, and the P1 Desktop-hosted strategy implementation now included in the source tree. The package remains alpha (`0.1.0`). HTTP endpoint details are mapped from confirmed Finger_desk calls; hosted context services use a separate Host/worker contract.

## Start here

1. [Install from source](installation.md).
2. [Configure endpoints and credentials](configuration.md).
3. Follow the [quick start](quickstart.md).
4. Use the API guides below and review [error handling](errors.md) and [security](security.md) before production use.

For Desktop-managed Python strategies, start with [Hosted strategies](hosted-strategies.md), then the [full API contract](quant/python-managed-api-v1.md) and [implementation status](quant/p1-hosted-status.md). Installing the SDK alone does not create a usable Host or trading service.

## API guides

| Topic | Guide |
|---|---|
| Hosted strategies | [Lifecycle, Context, Decimal models, and worker requirements](hosted-strategies.md) |
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

Hosted public models, synchronous callbacks, bidirectional worker communication, and process-disconnect handling are implemented. Account/history/output services require explicit Host capabilities. A backtesting matcher, trading ledger, live execution, complete Runtime installation/update flow, and overall P1/P4 platform acceptance remain outside this implementation. See [Architecture](architecture.md) and [hosted status](quant/p1-hosted-status.md).
