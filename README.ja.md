# Finger Trader Python SDK

### 開発者のための金融市場 API・クオンツ戦略ツール

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

Finger Trader Python SDK は、同期 HTTP API クライアント、チケット認証によるマーケットデータ WebSocket、Desktop Host 管理型の Python 戦略 API を提供します。現在は alpha（`0.1.0`）で、ソースからインストールするパッケージです。HTTP レスポンスはバックエンドのデータ構造を保持し、Hosted Strategy は Decimal／UTC モデルと独立した worker プロセスを使用します。

P1 の Hosted Strategy 実装はソースに含まれていますが、SDK 単体にバックテストエンジン、ブローカー、ライブ注文執行サービスは含まれません。機能と制約は[Hosted Strategy ガイド](docs/hosted-strategies.md)をご覧ください。

## 主な機能

- OAuth2 パスワード認証と既存アクセストークンの利用
- マーケット一覧、銘柄一覧、過去 OHLCV データの取得
- 認証セッションのプロフィール、ウォレット、ポジション、注文履歴の照会
- チケット認証による JSON マーケットデータ WebSocket
- `finger_trader.hosted` による Desktop 管理型戦略、同期ライフサイクル、型付き Context、JSON-RPC worker
- 呼び出し側が用意したバーに対する、独立したローカル指標・シグナルツール

現在のアプリ API に対する注文の発注・変更・取消・約定照会は、サポート対象 SDK メソッドとして実装されていません。旧互換メソッドをライブ取引に使用しないでください。

## インストール

PyPI には未公開です。GitHub からソースを取得してインストールします。

```sh
git clone https://github.com/FingerTrader/fingertrader-python-sdk.git
cd fingertrader-python-sdk
python -m pip install .
```

WebSocket を使用する場合は、クローンしたリポジトリ内で `python -m pip install '.[websocket]'` を実行します。Python 3.10 以上が必要です。

## クイックスタート

`FINGER_TRADER_ACCESS_TOKEN` にアクセストークンを設定し、認証済みの読み取り API を呼び出します。

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
    markets = client.market_data.markets()
    products = client.market_data.symbols(market="stock", page_size=10)
    bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=100)
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

トークンや認証レスポンス全体を出力しないでください。注文を送信する例はありません。

## ドキュメント

- [ドキュメント一覧](docs/ja/index.md) · [インストール](docs/ja/installation.md) · [クイックスタート](docs/ja/quickstart.md)
- [認証](docs/ja/authentication.md) · [設定](docs/ja/configuration.md) · [セキュリティ](docs/security.md)
- [マーケットデータ](docs/market-data.md) · [口座](docs/ja/accounts.md) · [ポジション](docs/ja/positions.md) · [注文履歴](docs/ja/orders.md) · [WebSocket](docs/websocket.md)
- [Hosted Strategy](docs/hosted-strategies.md) · [モデル](docs/models.md) · [API リファレンス](docs/api-reference.md) · [API マッピング](docs/api-mapping.md)
- [エラー処理](docs/errors.md) · [トラブルシューティング](docs/troubleshooting.md) · [例](examples/README.ja.md)

英語版の完全な契約、型シグネチャ、内部開発・受け入れ記録は各原文をご確認ください。SDK の公開 API と Desktop Host の機能境界はリリースごとに確認してください。

## サポートと貢献

不具合報告や対応 API の提案は[GitHub Issues](https://github.com/FingerTrader/fingertrader-python-sdk/issues)へお寄せください。コード変更にはテストを添え、公開動作が変わる場合はドキュメントも更新してください。

## セキュリティとライセンス

パスワード、OAuth クライアント情報、アクセストークン、顧客データをコミットしないでください。TLS 検証は本番で有効です。Hosted Strategy は信頼できるローカルコードのみ実行してください。worker はセキュリティサンドボックスではありません。[セキュリティガイド](docs/security.md)をご覧ください。

[Apache-2.0](LICENSE) ライセンス。API とマーケットデータの利用には、アカウント権限および適用されるサービス条件が引き続き適用されます。
