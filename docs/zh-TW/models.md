# 模型與回應資料

[English](../models.md) | [日本語](../ja/models.md) | [繁體中文](../zh-TW/models.md) | [한국어](../ko/models.md) | [العربية](../ar/models.md)

HTTP 服務方法回傳 `ApiResponse`。`.data` 是成功 payload，`.code` 與 `.message` 反映後端封套，`.raw` 保留完整 payload。SDK 不猜測帳戶或交易 schema，並保留原始資料。dataclass 是寬容的 raw-payload wrapper，服務方法不一定會自動轉換。

`MarketBar` 是 `finger_trader.models.Bar` 的 API alias。`MarketBar.from_dict()` 將常見 OHLCV 欄位轉成 `Decimal`，避免經過二進位浮點數。請依端點確認 epoch 單位是秒或毫秒。WebSocket `recv()` 回傳 dict；丟棄的 frame 則回傳 `None`。JSON frame 上限為 1 MiB。Hosted dataclass 與根層模型不同，金融數值使用 `Decimal`，時間採 UTC aware datetime，回傳集合為不可變快照。
