# Examples

Run scripts from the repository root after installing the SDK (`python -m pip install .`). Set `FINGER_TRADER_ACCESS_TOKEN` in your shell or secret manager for read-only authenticated examples. On PowerShell use `$env:FINGER_TRADER_ACCESS_TOKEN = ...`; on macOS/Linux use `export FINGER_TRADER_ACCESS_TOKEN=...`. Never put a real value in source control or shell history.

| Script | What it demonstrates | Writes trading state? |
|---|---|---|
| `api_read_only.py` | Read-only market/account/position/order-history walkthrough | No |
| `authentication_example.py` | OAuth password login using environment variables | No |
| `market_data_example.py` | Markets and five product categories | No |
| `historical_bars_example.py` | Bounded OHLCV query and optional Decimal mapping | No |
| `accounts_example.py` | Session profile and wallet | No |
| `positions_example.py` | Current holdings | No |
| `order_history_example.py` | Order history query | No |
| `websocket_example.py` | Ticket-based quote subscription; requires `python -m pip install '.[websocket]'` | No |
| `dual_ma_strategy.py` | Local demonstration on synthetic bars; no API calls | No |

Examples use context managers to release network resources and handle expected API/network failures. They do not print authentication tokens. There is deliberately no order-submission example: current app API write methods are not implemented by the SDK. See [Orders](../docs/orders.md).

Run one from the checkout root, for example:

```sh
python examples/market_data_example.py
```
