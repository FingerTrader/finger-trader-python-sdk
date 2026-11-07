# Market data

`client.market_data.markets()` returns the Finger_desk market menu. `symbols(market, page)` maps stock, crypto, forex, spot and indices to their market-specific endpoints. `history()` uses the observed shared K-line endpoint and accepts the backend interval string, page, limit and optional start time (epoch milliseconds or a timezone-aware datetime).

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
