# Orders

The confirmed Finger_desk order endpoint accepts `isBuy`, `isUsd`, `limitTime`, `market`, `orderId`, `orderType`, `price`, `quantity`, `ticker`, `isCreate`, `marginRatio`, `stopLose`, and `takeProfit`. The SDK retains backend enum values and does not define market/order enums that were not confirmed in the contract. Quantity is an integer per the observed `TradeEntity`; price and protective levels are sent using exact decimal strings without rounding.

```python
try:
    response = client.orders.submit(
        is_buy=True,
        is_usd=False,
        limit_time=0,
        market=1,
        order_id="",
        order_type=1,
        price="0",
        quantity=1,
        ticker="AAPL",
        is_create=1,
    )
except UnknownOutcomeError:
    # The request may have reached the server. Reconcile with order history.
    response = client.orders.history(page=1, limit=20)
```

Order submissions and modifications are not retried. Timeouts, invalid/empty responses, and server 5xx responses raise `UnknownOutcomeError`, meaning callers must reconcile before resubmitting. A 4xx response is returned as `APIError` because the server rejected the request. The confirmed operations are submit, history, update limit, cancel limit, and set take-profit/stop-loss. No executions endpoint, order-id detail query, idempotency key, or current-order endpoint was confirmed.
