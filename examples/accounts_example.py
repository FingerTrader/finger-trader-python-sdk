"""Read the authenticated profile and wallet payload."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    try:
        with FingerTraderClient(token=token) as client:
            print("Session profile:", client.accounts.detail().data)
            print("Wallet and balance:", client.accounts.balance().data)
    except NetworkError as exc:
        raise SystemExit(f"Network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None


if __name__ == "__main__":
    main()
