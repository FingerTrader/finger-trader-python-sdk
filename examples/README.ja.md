# Examples / サンプル

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

SDK のインストール後、リポジトリのルートからスクリプトを実行します（`python -m pip install .`）。読み取り専用の認証例では、シェルまたはシークレットマネージャーに `FINGER_TRADER_ACCESS_TOKEN` を設定してください。実際の値をソース管理やシェル履歴に保存しないでください。

| スクリプト | 内容 | 取引状態の変更 |
|---|---|---|
| `api_read_only.py` | 市場／口座／ポジション／注文履歴の読み取り | いいえ |
| `authentication_example.py` | 環境変数を使った OAuth ログイン | いいえ |
| `market_data_example.py` | 市場と商品カテゴリ | いいえ |
| `historical_bars_example.py` | OHLCV 取得と任意の Decimal 変換 | いいえ |
| `accounts_example.py` | セッションプロフィールとウォレット | いいえ |
| `positions_example.py` | 現在のポジション | いいえ |
| `order_history_example.py` | 注文履歴 | いいえ |
| `websocket_example.py` | ticket 認証の相場購読。`.[websocket]` が必要 | いいえ |
| `dual_ma_strategy.py` | 合成バーを使うローカル例。API 呼び出しなし | いいえ |

例は context manager で通信資源を解放し、想定される API／通信エラーを処理します。認証トークンは出力しません。現行 app API の書き込み操作は SDK 未実装のため、注文送信例はありません。[注文ガイド](../docs/orders.md)を参照してください。

```sh
python examples/market_data_example.py
```

`dual_ma_strategy.py` は独立したローカル signal API を使います。Desktop 管理型 API は[Hosted Strategy ガイド](../docs/hosted-strategies.md)を参照してください。現行 P1 Host は注文を執行しません。
