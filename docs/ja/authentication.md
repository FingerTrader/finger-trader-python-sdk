# 認証

[English](../authentication.md) | [日本語](authentication.md) | [繁體中文](../zh-TW/authentication.md)

`FingerTraderClient` は、既に取得済みのアクセストークンを受け取れます。`client.auth.login()` は Finger_desk が使用する OAuth2 password grant を実装します。form field は `username`、`password`、`grant_type=password`、`type`、必要に応じて CAPTCHA field です。認証は `finger-auth` root を使います。認証済み API request は Desktop client と同様に `Authorization: {token_type} {token}` と旧形式の `token` header を送信します。

メールログインでは `account_type=0`、携帯電話ログインでは `account_type=1` を指定してください。これは form field `type` に送られる backend `AccountTypeEnum` の値です。Desktop UI の `LoginType`（Email `1`、Mobile `2`）とは値が異なります。Finger_desk は request 前に `LoginType.enums.value` で変換します。

OAuth service は deployment ごとの Basic OAuth client credential も必要とします。`Basic ` prefix を除いた base64 credential を `oauth_basic_token` に渡してください。SDK は Desktop application の共有値を埋め込みません。サービス運用者から正しい値を取得し、commit しないでください。token はメモリ上だけに保持されます。refresh endpoint は確認されていません。`auth.check()` はローカルで token expiry を確認し、サーバーには request しません。

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

token response 全体を出力しないでください。secret field は repr から除外されますが、必要な application からはアクセス可能です。
