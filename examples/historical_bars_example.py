"""Request one bounded historical OHLCV window."""

import os

from finger_trader import APIError, FingerTraderClient, MarketBar, NetworkError


def main() -> None:
    token = os.environ.get("FINGER_TRADER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN before running this example.")
    market = os.environ.get("FINGER_TRADER_MARKET", "stock")
    ticker = os.environ.get("FINGER_TRADER_TICKER", "AAPL")
    interval = os.environ.get("FINGER_TRADER_INTERVAL", "1d")
    try:
        with FingerTraderClient(token=token, timeout=10) as client:
            response = client.market_data.history(
                market=market, ticker=ticker, interval=interval, limit=100
            )
            print("Raw bars:", response.data)
            if isinstance(response.data, list):
                for value in response.data:
                    if isinstance(value, dict):
                        print("Decimal-safe bar:", MarketBar.from_dict(value))
    except NetworkError as exc:
        raise SystemExit(f"Network request failed: {exc}") from None
    except APIError as exc:
        raise SystemExit(f"API request failed: {exc}") from None
    except ValueError as exc:
        raise SystemExit(f"Invalid market-data argument: {exc}") from None


if __name__ == "__main__":
    main()
