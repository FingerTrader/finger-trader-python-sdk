# 市場データ

[English](../market-data.md) | [日本語](../ja/market-data.md) | [繁體中文](../zh-TW/market-data.md) | [한국어](../ko/market-data.md) | [العربية](../ar/market-data.md)

`client.market_data.markets()` は利用可能な市場メニュー、`symbols(market, page, page_size)` はページ分割された商品一覧を取得します。利用可能なラベルは stock、forex、crypto、spot、indices、ETF、fund です。`history()` は crypto、stock、forex、spot の OHLCV 履歴を取得します。

`start_time` はタイムゾーン付き日時または epoch ミリ秒で指定します。履歴 API は時間でページングするため `page=1` のみ受け付けます。レスポンスは `.data` にそのまま保持されます。`MarketBar.from_dict()` は一般的な OHLCV キーを Decimal に変換する任意の mapper です。HTTP quote snapshot endpoint は確認されていません。リアルタイム相場は [WebSocket](websocket.md) を参照してください。
