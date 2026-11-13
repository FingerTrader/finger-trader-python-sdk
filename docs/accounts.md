# Accounts and balances

[English](accounts.md) | [日本語](ja/accounts.md) | [繁體中文](accounts.md) | [한국어](ko/accounts.md) | [العربية](accounts.md)


Finger_desk's current data SDK calls `POST /app-api/v1/public/login-info` for the authenticated user's profile and `POST /app-api/v1/fund/get-spot-wallet` for the spot wallet overview. These are session-scoped; they do not enumerate arbitrary account IDs or accept an `account_id` filter. The legacy `market` argument to `accounts.detail(market)` remains accepted for source compatibility and is ignored because the current profile endpoint is not market-scoped.

```python
profile = client.accounts.list()
profile = client.accounts.detail()
wallet = client.accounts.balance()
```

Payloads retain backend fields without inventing equity, available-funds or margin formulas. Use the server's own returned field names and precision.
