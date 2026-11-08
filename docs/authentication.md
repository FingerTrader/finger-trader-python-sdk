# Authentication

`FingerTraderClient` accepts an access token for integrations that already obtained one. `client.auth.login()` implements the OAuth2 password grant used by Finger_desk: form encoded `username`, `password`, `grant_type=password`, `type`, and optional CAPTCHA fields. Authentication uses the `finger-auth` root; authenticated API requests send both `Authorization: {token_type} {token}` and the legacy `token` header, matching the desktop client.

Set `account_type=0` for an email login or `account_type=1` for a mobile phone login. These are the backend `AccountTypeEnum` values sent as form field `type`. They differ from the desktop UI `LoginType` values (Email `1`, Mobile `2`); Finger_desk maps UI selection through `LoginType.enums.value` before sending the request.

The OAuth service also requires the deployment's Basic OAuth client credential. Pass the base64 credential value (without the `Basic ` prefix) through `oauth_basic_token`. The SDK intentionally does not embed the desktop application's shared value. Obtain the correct value from the Finger Trader service operator and do not commit it. Tokens are held in memory only. There is no confirmed refresh endpoint; `auth.check()` checks local token expiry and does not make a server request.

```python
import os
from finger_trader import FingerTraderClient

client = FingerTraderClient(oauth_basic_token=os.environ["FINGER_TRADER_OAUTH_BASIC_TOKEN"])
token_response = client.auth.login(
    os.environ["FINGER_TRADER_USERNAME"],
    os.environ["FINGER_TRADER_PASSWORD"],
    account_type=int(os.environ["FINGER_TRADER_LOGIN_TYPE"]),
)
print(token_response.data.token_type, token_response.data.expires_in)
```

Do not print the complete token response. Secret fields are excluded from its representation, but remain accessible to the application that needs them.
