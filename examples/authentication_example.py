"""Authenticate with the configured OAuth2 password grant; never prints tokens."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    required = (
        "FINGER_TRADER_OAUTH_BASIC_TOKEN",
        "FINGER_TRADER_USERNAME",
        "FINGER_TRADER_PASSWORD",
        "FINGER_TRADER_LOGIN_TYPE",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Set required environment variables: {', '.join(missing)}")
    try:
        with FingerTraderClient(
            oauth_basic_token=os.environ["FINGER_TRADER_OAUTH_BASIC_TOKEN"]
        ) as client:
            response = client.auth.login(
                os.environ["FINGER_TRADER_USERNAME"],
                os.environ["FINGER_TRADER_PASSWORD"],
                account_type=int(os.environ["FINGER_TRADER_LOGIN_TYPE"]),
                captcha_id=os.environ.get("FINGER_TRADER_CAPTCHA_ID"),
                captcha_code=os.environ.get("FINGER_TRADER_CAPTCHA_CODE"),
            )
            print(
                "Authentication succeeded; token held in memory only. "
                f"Token type: {response.data.token_type}; expires in: {response.data.expires_in}s"
            )
    except NetworkError as exc:
        raise SystemExit(f"Authentication network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"Authentication was rejected: {exc}") from None
    except ValueError as exc:
        raise SystemExit(f"Invalid login type configuration: {exc}") from None


if __name__ == "__main__":
    main()
