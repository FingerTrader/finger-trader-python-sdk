# Positions

`client.positions.list()` queries the authenticated session's holdings using the confirmed `type` and `isUsd` parameters.

```python
positions = client.positions.list(order_status=0, is_usd=False)
```

The endpoint does not accept an account ID or product filter in Finger_desk. `account_id=` remains accepted for source compatibility but raises `ValueError` if provided, so the SDK cannot imply a filter that the server does not implement. Position cost, P/L, and margin values are returned in the backend's original response model.
