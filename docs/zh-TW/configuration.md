# 設定

[English](../configuration.md) | [日本語](../ja/configuration.md) | [繁體中文](configuration.md)

`FingerTraderClient` 接受明確的 endpoint 與 timeout 設定。正式環境 URL 預設使用 Finger Trader 公開服務端點；自訂部署請向服務營運者取得相符的 app API、auth API 與 socket-auth API URL。

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

| 環境變數 | 用途 |
|---|---|
| `FINGER_TRADER_ACCESS_TOKEN` | 已取得的選用權杖，用於需要驗證的 API request |
| `FINGER_TRADER_OAUTH_BASIC_TOKEN` | 使用密碼登入時由 service operator 提供的 OAuth Basic credential payload，不含 `Basic ` 前綴 |
| `FINGER_TRADER_USERNAME` / `FINGER_TRADER_PASSWORD` | 僅在 application 呼叫 `auth.login` 時讀取的登入憑證 |
| `FINGER_TRADER_LOGIN_TYPE` | Backend 整數：`0` 為 email、`1` 為 mobile |
| `FINGER_TRADER_API_BASE_URL` | 選用 app API base URL |
| `FINGER_TRADER_AUTH_URL` | 選用 OAuth auth service URL |
| `FINGER_TRADER_SOCKET_AUTH_URL` | 選用 socket ticket service URL |
| `FINGER_TRADER_TIMEOUT` | request timeout 秒數，需大於 0 且不超過 300 |

這些名稱是 application 設定範例；SDK 不會自動載入 `.env`。請在 shell 匯出變數或使用部署環境的 secret manager。勿將正式環境 secret 儲存在已提交的 `.env` 檔案。現行 client 中 `environment="dev"` 與 `"local"` 會選擇 loopback 預設值；非本機開發部署請明確設定 URL。非 loopback endpoint 必須使用 HTTPS；WebSocket 傳輸則使用 WSS。

使用 context manager（`with FingerTraderClient(...) as client`）或完成後呼叫 `client.close()` 關閉用戶端。
