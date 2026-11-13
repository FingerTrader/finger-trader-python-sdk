# モデルとレスポンスデータ

[English](../models.md) | [日本語](../ja/models.md) | [繁體中文](../zh-TW/models.md) | [한국어](../ko/models.md) | [العربية](../ar/models.md)

HTTP service method は `ApiResponse` を返します。`.data` は成功 payload、`.code` と `.message` は backend envelope の値、`.raw` は完全な payload です。SDK は口座や取引 schema を推測せず、受信データを保持します。各 dataclass は寛容な raw-payload wrapper であり、service が自動的に変換するとは限りません。

`MarketBar` は `finger_trader.models.Bar` の API 用 alias です。`MarketBar.from_dict()` は一般的な OHLCV キーを `Decimal` に変換し、binary float 経由の誤差を避けます。epoch が秒かミリ秒かは endpoint ごとに確認してください。WebSocket の `recv()` は dict または破棄された frame に対して `None` を返します。JSON frame は最大 1 MiB です。Hosted dataclass は root-level model と別型で、金融値 `Decimal`、UTC aware datetime、immutable snapshot を使用します。
