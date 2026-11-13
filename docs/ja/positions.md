# ポジション

[English](../positions.md) | [日本語](../ja/positions.md) | [繁體中文](../zh-TW/positions.md) | [한국어](../ko/positions.md) | [العربية](../ar/positions.md)

`client.positions.list()` は現在の `POST /app-api/v1/order/get-holding-orders` を呼び、`{page, pageSize, query}` を送ります。`order_status` は `orderType`（market `0`、limit `1`）、通貨は `coinType`（USD `0`、USDT `100`）に対応します。account は認証セッションで決まります。

任意の `account_id` はサポートされず、指定すると `ValueError` になります。`market_type` は backend enum で絞り込みできます。原価、損益、証拠金は backend のレスポンスモデルのまま返されます。

例と仕様の詳細は [English source](../positions.md) を参照してください。
