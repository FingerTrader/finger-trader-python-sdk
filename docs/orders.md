# Orders

The confirmed Finger_desk order endpoint accepts `isBuy`, `isUsd`, `limitTime`, `market`, `orderId`, `orderType`, `price`, `quantity`, `ticker`, `isCreate`, `marginRatio`, `stopLose`, and `takeProfit`. The SDK retains backend enum values and does not define market/order enums that were not confirmed in the contract. Quantity is an integer per the observed `TradeEntity`; price and protective levels are sent using exact decimal strings without rounding.

```python
import os

from finger_trader import FingerTraderClient, UnknownOutcomeError

if os.environ.get("FINGER_TRADER_ENABLE_LIVE_ORDER") != "YES":
    raise SystemExit("Set FINGER_TRADER_ENABLE_LIVE_ORDER=YES to enable this live request")

client = FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"])

try:
    response = client.orders.submit(
        is_buy=True,
        is_usd=os.environ["FINGER_TRADER_ORDER_IS_USD"] == "true",
        limit_time=int(os.environ["FINGER_TRADER_ORDER_LIMIT_TIME"]),
        market=int(os.environ["FINGER_TRADER_ORDER_MARKET"]),
        order_id="",  # Finger_desk uses an empty ID when creating a new order.
        order_type=int(os.environ["FINGER_TRADER_ORDER_TYPE"]),
        price=os.environ["FINGER_TRADER_ORDER_PRICE"],
        quantity=int(os.environ["FINGER_TRADER_ORDER_QUANTITY"]),
        ticker=os.environ["FINGER_TRADER_ORDER_TICKER"],
        is_create=int(os.environ["FINGER_TRADER_ORDER_IS_CREATE"]),
    )
except UnknownOutcomeError:
    # The request may have reached the server. Reconcile with order history.
    response = client.orders.history(page=1, limit=20)
```

This gated snippet submits a real order when enabled. Confirm server enum values, trading environment, product rules, and account permissions before running it. Order submissions and modifications are not retried. Timeouts, invalid/empty responses, and server 5xx responses raise `UnknownOutcomeError`, meaning callers must reconcile before resubmitting. A 4xx response is returned as `APIError` because the server rejected the request. The confirmed operations are submit, history, update limit, cancel limit, and set take-profit/stop-loss. No executions endpoint, order-id detail query, idempotency key, or current-order endpoint was confirmed.
