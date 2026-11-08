# Market data

`client.market_data.markets()` calls Finger_desk's current `POST /app-api/v1/public/get-maker-info`. `symbols(market, page, page_size)` calls `POST /app-api/v1/market/ticker-list` with the current paginated query DTO; stock, forex, crypto, spot and indices map to Desk `MarketTypeEnum` values 3, 0, 2, 1 and 6. `history()` calls `POST /app-api/v1/market/kline-list`; its current DTO uses the same market enum and an epoch-millisecond `startTime` string. To fetch older bars, pass an earlier `start_time`; the old `page` parameter is accepted only for page 1 because this endpoint pages by time.

```python
markets = client.market_data.markets()
symbols = client.market_data.symbols("crypto", page=1)
bars = client.market_data.get_history(
    market="stock",
    ticker="AAPL",
    interval="1d",
    limit=100,
    page=1,
)
```

Response payloads remain available as received in `.data`. `MarketBar.from_dict()` is an opt-in decimal mapper for common OHLCV field names. HTTP quote snapshots and market-specific interval enumerations have no confirmed contract. Real-time quote streaming is documented in [WebSocket](websocket.md).
