# 持倉

[English](../positions.md) | [日本語](../ja/positions.md) | [繁體中文](../zh-TW/positions.md) | [한국어](../ko/positions.md) | [العربية](../ar/positions.md)

`client.positions.list()` 呼叫現行 `POST /app-api/v1/order/get-holding-orders`，並送出 `{page, pageSize, query}`。`order_status` 對應 `orderType`（市價 `0`、限價 `1`）；幣別對應 `coinType`（USD `0`、USDT `100`）。帳戶由已驗證工作階段決定。

不支援任意 `account_id`，若提供會引發 `ValueError`。`market_type` 可依後端 enum 篩選。成本、損益及保證金欄位依後端原始回應模型傳回。

完整範例與規格細節請參閱 [英文原文](../positions.md)。
