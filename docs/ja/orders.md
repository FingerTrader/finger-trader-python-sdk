# 注文

[English](../orders.md) | [日本語](../ja/orders.md) | [繁體中文](../zh-TW/orders.md) | [한국어](../ko/orders.md) | [العربية](../ar/orders.md)

現行 app API では注文履歴の取得のみ SDK が対応します。`client.orders.history(*, page=1, limit=20, filters=None)` は認証 session の履歴を読み、`limit` を `pageSize` に対応させます。filter は wallet_type、market_type、order_type、coin_type、order_side、start_time、end_time を指定できます。

現在の API には作成、TP/SL変更、取消、決済 endpoint がありますが、SDK はまだ mapping していません。旧 `submit`、`update_limit`、`cancel_limit`、`set_take_profit_loss` は廃止された `api/mob` route に向くため使用しないでください。注文送信／取消例はありません。Hosted Context の注文 interface も現行 P1 Host では `UNSUPPORTED_CAPABILITY` です。

See the [English source](../orders.md) for exact request parameters and code examples.
