# Orders

Order history uses Finger_desk's current `POST /app-api/v1/order/trade-history` endpoint. The request body is `{page, pageSize, query}`; supported filters use the backend `OrderQueryDTO` fields `walletType`, `marketType`, `orderType`, `coinType`, `orderSide`, `startTime`, and `endTime`.

```python
history = client.orders.history(page=1, limit=20)
print(history.data)
```

The current Finger_desk `dataSdk` exposes order creation at `POST /app-api/v1/order/create-order`, modification at `/app-api/v1/order/modify-stop-profit-loss`, cancellation at `/app-api/v1/order/cancel-order`, and position close at `/app-api/v1/order/close-order`. The SDK's existing order mutation wrappers still target retired `api/mob` routes and are not supported against the current API. Do not use them for live orders until they are migrated and verified.

The current contract does not establish an idempotency key or separate execution endpoint. Never automatically retry a state-changing order request after an unknown network outcome.
