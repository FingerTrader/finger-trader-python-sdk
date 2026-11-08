"""Read order history only. This example never creates or changes an order."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    try:
        with FingerTraderClient(token=token) as client:
            response = client.orders.history(page=1, limit=20)
            print("Order history:", response.data)
    except NetworkError as exc:
        raise SystemExit(f"Network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None
    except ValueError as exc:
        raise SystemExit(f"Invalid history query: {exc}") from None


if __name__ == "__main__":
    main()
