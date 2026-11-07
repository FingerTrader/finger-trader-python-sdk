"""Read-only API walkthrough; needs credentials only for protected endpoints."""
import os
from finger_trader import FingerTraderClient

client = FingerTraderClient(token=os.getenv("FINGER_TRADER_ACCESS_TOKEN"))
if not client.auth.is_authenticated:
    raise SystemExit("Set FINGER_TRADER_ACCESS_TOKEN to a valid access token before querying the API")
for response in (client.market_data.markets(), client.market_data.symbols("stock")):
    print(response.data)
print(client.market_data.history(market="stock", ticker="AAPL", interval="1d").data)
print(client.accounts.balance().data)
print(client.positions.list().data)
print(client.orders.history().data)
