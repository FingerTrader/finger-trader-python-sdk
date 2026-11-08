"""Run a small authenticated read-only API walkthrough."""

import os

from finger_trader import APIError, FingerTraderClient, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    try:
        with FingerTraderClient(token=token) as client:
            for label, response in (
                ("Markets", client.market_data.markets()),
                ("Stock products", client.market_data.symbols(market="stock", page_size=10)),
                (
                    "Daily bars",
                    client.market_data.history(
                        market="stock", ticker="AAPL", interval="1d", limit=10
                    ),
                ),
                ("Profile", client.accounts.detail()),
                ("Wallet", client.accounts.balance()),
                ("Holdings", client.positions.list(page_size=10)),
                ("Order history", client.orders.history(limit=10)),
            ):
                print(f"{label}: {response.data}")
    except NetworkError as exc:
        raise SystemExit(f"Network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None


if __name__ == "__main__":
    main()
