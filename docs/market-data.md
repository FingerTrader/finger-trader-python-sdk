# Market data

`client.market_data.markets()` retrieves the available market menu. `symbols(market, page, page_size)` retrieves a paginated product list. Supported labels include stock, forex, crypto, spot, indices, ETF, and fund. `history()` retrieves historical OHLCV for crypto, stock, forex, and spot. It accepts an epoch-millisecond `startTime` string internally. To request older bars, pass an earlier timezone-aware `start_time`; the compatibility `page` parameter must be 1 because this endpoint pages by time. Consult [API mapping](api-mapping.md) for current enum mapping and backend routes.

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

Response payloads remain available as received in `.data`; the API does not automatically convert them to model instances. `MarketBar.from_dict()` is an opt-in decimal mapper for common OHLCV field names. The SDK does not impose product-specific interval values; use those confirmed for the chosen market and deployment. There is no confirmed HTTP quote snapshot endpoint. Real-time quote streaming is documented in [WebSocket](websocket.md).
