"""Read current holdings for the authenticated session."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    try:
        with FingerTraderClient(token=token) as client:
            response = client.positions.list(page=1, page_size=50)
            print("Current holdings:", response.data)
    except NetworkError as exc:
        raise SystemExit(f"Network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None
    except ValueError as exc:
        raise SystemExit(f"Invalid holdings query: {exc}") from None


if __name__ == "__main__":
    main()
