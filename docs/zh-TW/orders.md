# 訂單

[English](../orders.md) | [日本語](../ja/orders.md) | [繁體中文](../zh-TW/orders.md) | [한국어](../ko/orders.md) | [العربية](../ar/orders.md)

目前 SDK 僅支援查詢現行 App API 的訂單歷史。`client.orders.history(*, page=1, limit=20, filters=None)` 讀取已驗證工作階段的歷史，`limit` 對應 `pageSize`。篩選欄位包含 wallet_type、market_type、order_type、coin_type、order_side、start_time、end_time。

目前 API 雖有建立、TP/SL 修改、取消及平倉端點，但 SDK 尚未完成對應。舊版 `submit`、`update_limit`、`cancel_limit`、`set_take_profit_loss` 指向已退役的 `api/mob` 路由，請勿呼叫。本文件不提供送單／取消範例。Hosted Context 的訂單介面在目前 P1 Host 也會回傳 `UNSUPPORTED_CAPABILITY`。

精確參數及程式範例請參閱[英文原文](../orders.md)。
