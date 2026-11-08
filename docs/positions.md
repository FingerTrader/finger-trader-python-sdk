# Positions

`client.positions.list()` calls Finger_desk's current `POST /app-api/v1/order/get-holding-orders` with the standard `{page, pageSize, query}` body. `order_status` maps to current `orderType` (market order `0`, limit order `1`); currency maps to `coinType` (USD `0`, USDT `100`). The authenticated session selects the account; arbitrary `account_id` is not supported.

```python
positions = client.positions.list(order_status=0, is_usd=False)
```

The endpoint does not accept an account ID. `account_id=` remains accepted for source compatibility but raises `ValueError` if provided. `market_type` can filter by the backend market enum; position cost, P/L, and margin values are returned in the backend's original response model.
