# Orders

## Supported: query order history

`client.orders.history(*, page=1, limit=20, filters=None) -> ApiResponse` reads the authenticated session's order history from the current app API. It sends `page`, `pageSize`, and a `query` object. `limit` maps to `pageSize`.

Supported filter names are `wallet_type`, `market_type`, `order_type`, `coin_type`, `order_side`, `start_time`, and `end_time`; backend camelCase forms are also accepted. A `datetime` time filter must be timezone-aware and is converted to epoch milliseconds. Other values are passed through using the backend contract; use only enum values confirmed for the deployment.

```python
import os

from finger_trader import APIError, FingerTraderClient

try:
    with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
        response = client.orders.history(page=1, limit=20)
        print(response.data)
except APIError as exc:
    print(f"Could not read order history: {exc}")
```

Load the token from an environment variable or secret manager. `ApiResponse.data` retains backend order fields and is not converted to an `Order` dataclass automatically.

## Not supported by the current SDK

The active Finger_desk service contract has create, modify stop/profit/loss, cancel, and close endpoints, but these operations are **not mapped to the current SDK methods**. Existing compatibility methods `submit`, `update_limit`, `cancel_limit`, and `set_take_profit_loss` still target retired `api/mob` routes. Do not call them. The SDK cannot currently document reliable method parameters, enum values, server precision rules, or return types for those current app API operations. `orders.executions()` is also not implemented because no confirmed execution endpoint is exposed.

Consequently, this repository intentionally has no runnable order submission or cancellation example. Once these methods are mapped and verified against the active contract, their docs must specify market/limit rules, backend enum sources, quantity/price constraints, and result reconciliation before release.

## Outcome and risk guidance

No state-changing order call is included in the public supported API. The transport does not retry POST requests. `UnknownOutcomeError` is used by legacy write wrappers when a request may have reached the server; if encountered, reconcile with authorized server-side order history before any manual retry. Client validation never replaces server-side permissions or risk checks. See [API mapping](api-mapping.md) for the current endpoint coverage and gaps.
