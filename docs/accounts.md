# Accounts and balances

Finger_desk calls return the authenticated session's trading profile and wallet overview. The observed profile request requires a market value; `accounts.list()` maps to its market-0 default and `accounts.detail(market)` lets callers select a backend market. `accounts.balance()` returns the wallet overview. These calls do not enumerate arbitrary account IDs or accept an `account_id` filter.

```python
profile = client.accounts.list()
market_profile = client.accounts.detail(market=0)
wallet = client.accounts.balance()
```

Payloads retain backend fields without inventing equity, available-funds or margin formulas. Use the server's own returned field names and precision.
