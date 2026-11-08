# Models and response data

## API responses

HTTP service methods return `ApiResponse`. Its `.data` is the successful endpoint payload, `.code` and `.message` reflect the backend envelope when present, and `.raw` retains the full payload. The SDK intentionally preserves endpoint data instead of guessing a normalized account or trading schema.

```python
response = client.accounts.balance()
print(response.code, response.message)
wallet_payload = response.data
```

Account, balance, position, order, market, instrument, execution, and trading-rule dataclasses are exported as tolerant raw-payload wrappers. Current service methods generally return `ApiResponse` payloads rather than automatically converting them to these wrappers. Inspect actual response keys and use `response.data` accordingly; payload shape can vary by market and service version.

## Decimal-safe bar mapping

`MarketBar` is the API-facing alias for `finger_trader.models.Bar`; the older `finger_trader.Bar` is a separate strategy/runtime value type. `MarketBar.from_dict()` accepts common long and abbreviated OHLCV keys and converts numeric fields to `Decimal` without a binary floating point round trip.

```python
from finger_trader import MarketBar

bar = MarketBar.from_dict(
    {"time": 1_700_000_000_000, "o": "10.1", "h": "11", "l": "9.8", "c": "10.5", "v": "1200"}
)
assert str(bar.close) == "10.5"
```

The source timestamp value is retained as provided by the service; verify whether a particular endpoint's timestamps are seconds or milliseconds before converting. Input `datetime` values accepted by SDK query methods must be timezone-aware; epoch timestamps use milliseconds where documented.

## WebSocket messages

`MarketWebSocket.recv()` returns a decoded JSON object (a `dict`) or `None` when a frame is discarded as a duplicate/reconnect event. The confirmed envelope includes fields such as `action`, `msgType`, `timestamp`, `msgId`, and `content`; exact quote payload fields are service-defined and preserved unchanged. The client accepts UTF-8 JSON encoded in a text or binary WebSocket frame and rejects messages above 1 MiB.

## Serialization

The models are Python dataclasses, not a separate wire serialization layer. Use `dataclasses.asdict()` for wrapper dataclasses; convert `Decimal` values explicitly to strings for JSON or financial storage to preserve precision.
