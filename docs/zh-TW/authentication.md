# 驗證

[English](../authentication.md) | [日本語](../ja/authentication.md) | [繁體中文](authentication.md)

`FingerTraderClient` 可接收已取得的存取權杖。`client.auth.login()` 實作 Finger_desk 使用的 OAuth2 password grant，表單欄位為 `username`、`password`、`grant_type=password`、`type` 與選用 CAPTCHA 欄位。驗證使用 `finger-auth` root。已驗證 API request 會傳送 `Authorization: {token_type} {token}` 及舊版 `token` header，與桌面用戶端一致。

電子郵件登入請設定 `account_type=0`，手機登入請設定 `account_type=1`。這是表單欄位 `type` 傳送的 backend `AccountTypeEnum` 值，與 Desktop UI 的 `LoginType`（Email `1`、Mobile `2`）不同。Finger_desk 會在送出 request 前透過 `LoginType.enums.value` 轉換。

OAuth service 也需要部署環境提供的 Basic OAuth 用戶端憑證。將不含 `Basic ` 前綴的 base64 憑證值透過 `oauth_basic_token` 傳入。SDK 不會內嵌 Desktop application 共用值。請向 Finger Trader service operator 取得正確值，且勿提交至版本控制。權杖僅保存在記憶體中。目前沒有已確認的 refresh endpoint；`auth.check()` 只檢查本機權杖是否存在及是否過期，不會呼叫伺服器。

```python
import os
from finger_trader import APIError, FingerTraderClient, NetworkError

try:
    with FingerTraderClient(
        oauth_basic_token=os.environ["FINGER_TRADER_OAUTH_BASIC_TOKEN"]
    ) as client:
        token_response = client.auth.login(
            os.environ["FINGER_TRADER_USERNAME"],
            os.environ["FINGER_TRADER_PASSWORD"],
            account_type=int(os.environ["FINGER_TRADER_LOGIN_TYPE"]),
        )
        print(token_response.data.token_type, token_response.data.expires_in)
except NetworkError as exc:
    print(f"Authentication network request failed: {exc}")
except APIError as exc:
    print(f"Authentication was rejected: {exc}")
```

請勿輸出完整 token response。secret 欄位會從 repr 中排除，但仍可供需要它的 application 存取。
