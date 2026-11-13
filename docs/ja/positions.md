# ポジション

[English](../positions.md) | [日本語](positions.md) | [繁體中文](../positions.md)

`client.positions.list()` は標準 `{page, pageSize, query}` body で Finger_desk の現行 `POST /app-api/v1/order/get-holding-orders` を呼び出します。`order_status` は現行 `orderType`（market `0`、limit `1`）に対応し、通貨は `coinType`（USD `0`、USDT `100`）に対応します。口座は認証 session によって決まります。任意の `account_id` はサポートされません。

```python
positions = client.positions.list(order_status=0, is_usd=False)
```

endpoint は account ID を受け取りません。source compatibility のため `account_id=` は受理されますが、指定すると `ValueError` になります。`market_type` は backend market enum で filter できます。ポジション原価、損益、証拠金の値は backend の元レスポンスモデルで返されます。
