# 市場資料

[English](../market-data.md) | [日本語](../ja/market-data.md) | [繁體中文](../zh-TW/market-data.md) | [한국어](../ko/market-data.md) | [العربية](../ar/market-data.md)

`client.market_data.markets()` 取得可用市場選單；`symbols(market, page, page_size)` 取得分頁商品清單。可用標籤包括 stock、forex、crypto、spot、indices、ETF、fund。`history()` 可取得 crypto、stock、forex、spot 的 OHLCV 歷史資料。

`start_time` 使用含時區日期時間或 epoch 毫秒。歷史 API 以時間分頁，因此只接受 `page=1`。回應原樣保留於 `.data`。`MarketBar.from_dict()` 可選擇將常見 OHLCV 欄位轉為 Decimal。尚未確認 HTTP 即時報價端點；即時串流請看 [WebSocket](websocket.md)。
