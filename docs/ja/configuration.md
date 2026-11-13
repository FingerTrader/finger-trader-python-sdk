# 設定

[English](../configuration.md) | [日本語](configuration.md) | [繁體中文](../zh-TW/configuration.md)

`FingerTraderClient` は endpoint と timeout を明示的に設定できます。本番 URL は Finger Trader の公開 service endpoint が既定です。独自 deployment では service 運用者から app API、auth API、socket-auth API の URL を取得してください。

```python
import os
from finger_trader import FingerTraderClient

client = FingerTraderClient(
    token=os.getenv("FINGER_TRADER_ACCESS_TOKEN"),
    base_url=os.getenv("FINGER_TRADER_API_BASE_URL") or None,
    auth_url=os.getenv("FINGER_TRADER_AUTH_URL") or None,
    socket_auth_url=os.getenv("FINGER_TRADER_SOCKET_AUTH_URL") or None,
    timeout=float(os.getenv("FINGER_TRADER_TIMEOUT", "10")),
)
```

| 環境変数 | 用途 |
|---|---|
| `FINGER_TRADER_ACCESS_TOKEN` | 認証済み API request 用の任意 token |
| `FINGER_TRADER_OAUTH_BASIC_TOKEN` | password login 時に service 運用者が提供する OAuth Basic credential（`Basic ` prefix なし） |
| `FINGER_TRADER_USERNAME` / `FINGER_TRADER_PASSWORD` | `auth.login` 呼び出し時にのみ読む認証情報 |
| `FINGER_TRADER_LOGIN_TYPE` | backend integer：`0` は email、`1` は mobile |
| `FINGER_TRADER_API_BASE_URL` | 任意の app API base URL |
| `FINGER_TRADER_AUTH_URL` | 任意の OAuth auth service URL |
| `FINGER_TRADER_SOCKET_AUTH_URL` | 任意の socket ticket service URL |
| `FINGER_TRADER_TIMEOUT` | 0 より大きく 300 以下の秒単位 timeout |

これらは application 設定の例です。SDK は `.env` を自動読込しません。shell から環境変数を export するか、deployment の secret manager を使用してください。本番 secret を commit する `.env` に保存しないでください。現行 client では `environment="dev"` と `"local"` が loopback default を選びます。非ローカル開発環境では URL を明示してください。loopback 以外の endpoint は HTTPS、WebSocket は WSS が必要です。

`with FingerTraderClient(...) as client` を使うか、処理後に `client.close()` を呼び出してください。
