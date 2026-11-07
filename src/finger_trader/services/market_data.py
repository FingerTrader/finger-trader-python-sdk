"""Market data endpoints confirmed in Finger_desk."""

from __future__ import annotations

from datetime import datetime

from ..models import ApiResponse


class MarketData:
    _SYMBOL_ROUTES = {
        "crypto": "/api/mob/market/crypto/getCryptoIndexTicker/{page}",
        "forex": "/api/mob/market/forex-base-info-entity/getForexIndexTicker/{page}",
        "spot": "/api/mob/market/spot-base-info-entity/getSpotIndexTicker/{page}",
        "stock": "/api/mob/market/stock/stock-us-base-info/getHotTicker",
        "indices": "/api/mob/market/indices-info-entity/getIndicesIndexTicker/{page}",
    }
    _KLINE_MARKETS = {"crypto", "stock", "forex", "spot"}

    def __init__(self, client):
        self._client = client

    def markets(self) -> ApiResponse:
        return self._client._get("/api/mob/trade/profile-entity/getMarket")

    def symbols(self, market: str = "stock", page: int = 1) -> ApiResponse:
        if market not in self._SYMBOL_ROUTES:
            raise ValueError(f"Unsupported market: {market}")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise ValueError("page must be a positive integer")
        return self._client._get(self._SYMBOL_ROUTES[market].format(page=page))

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
        for value, name in ((limit, "limit"), (page, "page")):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        params = {
            "market": market,
            "ticker": ticker,
            "interval": interval,
            "limit": limit,
            "page": page,
        }
        if start_time is not None:
            if isinstance(start_time, datetime):
                if start_time.tzinfo is None or start_time.utcoffset() is None:
                    raise ValueError("start_time datetime must be timezone-aware")
                start_millis = int(start_time.timestamp() * 1000)
            else:
                if isinstance(start_time, bool):
                    raise ValueError("start_time must be epoch milliseconds or an aware datetime")
                start_millis = int(start_time)
            params["startTime"] = start_millis
        return self._client._get("/api/mob/market/kline/getKline", params=params)

    get_history = history

    def quote(self, ticker: str):
        raise NotImplementedError(
            "No HTTP snapshot endpoint is confirmed in Finger_desk. Use subscribe_quotes()."
        )

    def subscribe_quotes(self, tickers, *, market="stock", on_message=None):
        return self._client.websocket().subscribe(tickers, market=market, on_message=on_message)
