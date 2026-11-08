# Configuration

`FingerTraderClient` accepts explicit endpoint and timeout configuration. Production URLs default to Finger Trader's public service endpoints; custom deployments should provide the matching app API, auth API, and socket-auth API URLs from the service operator.

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

| Variable | Use |
|---|---|
| `FINGER_TRADER_ACCESS_TOKEN` | Optional pre-obtained token for authenticated API requests. |
| `FINGER_TRADER_OAUTH_BASIC_TOKEN` | OAuth Basic credential payload, without the `Basic ` prefix, supplied by the service operator when using password login. |
| `FINGER_TRADER_USERNAME` / `FINGER_TRADER_PASSWORD` | Login credentials; read only when the application calls `auth.login`. |
| `FINGER_TRADER_LOGIN_TYPE` | Backend integer: `0` email or `1` mobile. |
| `FINGER_TRADER_API_BASE_URL` | Optional app API base URL. |
| `FINGER_TRADER_AUTH_URL` | Optional OAuth auth service base URL. |
| `FINGER_TRADER_SOCKET_AUTH_URL` | Optional socket ticket service base URL. |
| `FINGER_TRADER_TIMEOUT` | Request timeout in seconds, greater than 0 and at most 300. |

These names are examples for application configuration; the SDK does not automatically load a `.env` file. Export variables in your shell or use your deployment's secret manager. Do not store production secrets in a committed `.env` file. `environment="dev"` and `"local"` select loopback defaults in the current client implementation; use explicit URLs for a non-local development deployment. Non-loopback endpoints require HTTPS; WebSocket transport uses WSS.

Close clients with a context manager (`with FingerTraderClient(...) as client`) or call `client.close()` when finished.
