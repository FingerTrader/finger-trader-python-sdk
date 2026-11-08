"""Market data endpoints confirmed in Finger_desk."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import ApiResponse


class MarketData:
    # Values are Finger_desk's dataSdk MarketTypeEnum values.
    _MARKET_TYPES = {
        "forex": 0,
        "spot": 1,
        "crypto": 2,
        "stock": 3,
        "etf": 4,
        "fund": 5,
        "indices": 6,
    }
    _KLINE_MARKETS = {"crypto", "stock", "forex", "spot"}

    def __init__(self, client):
        self._client = client

    def markets(self) -> ApiResponse:
        return self._client._post("/app-api/v1/public/get-maker-info")

    def symbols(self, market: str = "stock", page: int = 1, page_size: int = 50) -> ApiResponse:
        if market not in self._MARKET_TYPES:
            raise ValueError(f"Unsupported market: {market}")
        for value, name in ((page, "page"), (page_size, "page_size")):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        return self._client._post(
            "/app-api/v1/market/ticker-list",
            {
                "page": page,
                "pageSize": page_size,
                "query": {"marketType": self._MARKET_TYPES[market]},
            },
        )

    def history(
        self,
        *,
        market: str,
        ticker: str,
        interval: str,
        limit: int = 200,
        page: int = 1,
        start_time=None,
    ) -> ApiResponse:
        if market not in self._KLINE_MARKETS:
            raise ValueError("market must be crypto, stock, forex, or spot")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("ticker must not be empty")
        if not isinstance(interval, str) or not interval.strip():
            raise ValueError("interval must not be empty")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise ValueError("page must be a positive integer")
        if page != 1:
            raise ValueError("the current API paginates K-lines with start_time, not page")
        start_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
        if start_time is not None:
            if isinstance(start_time, datetime):
                if start_time.tzinfo is None or start_time.utcoffset() is None:
                    raise ValueError("start_time datetime must be timezone-aware")
                start_millis = int(start_time.timestamp() * 1000)
            else:
                if isinstance(start_time, bool):
                    raise ValueError("start_time must be epoch milliseconds or an aware datetime")
                start_millis = int(start_time)
        payload = {
            "market": self._MARKET_TYPES[market],
            "ticker": ticker,
            "interval": interval,
            "limit": limit,
            "startTime": str(start_millis),
        }
        return self._client._post("/app-api/v1/market/kline-list", payload)

    get_history = history

    def quote(self, ticker: str):
        raise NotImplementedError(
            "No HTTP snapshot endpoint is confirmed in Finger_desk. Use subscribe_quotes()."
        )

    def subscribe_quotes(self, tickers, *, market="stock", on_message=None):
        return self._client.websocket().subscribe(tickers, market=market, on_message=on_message)
