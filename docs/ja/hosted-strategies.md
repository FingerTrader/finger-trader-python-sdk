# Desktop 管理型 Python 戦略

[English](../hosted-strategies.md) | [日本語](../ja/hosted-strategies.md) | [繁體中文](../zh-TW/hosted-strategies.md) | [한국어](../ko/hosted-strategies.md) | [العربية](../ar/hosted-strategies.md)

Import hosted types from `finger_trader.hosted`. Callbacks are synchronous and run under a Desktop Host; Context is valid only during an active callback on its owning thread. Financial values use `Decimal`, times use UTC-aware `datetime`. The current P1 Host does not execute trades.

For complete method details, payload fields, limitations, and examples, see the [English technical reference](../hosted-strategies.md).
