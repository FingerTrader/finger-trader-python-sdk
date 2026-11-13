# SDK アーキテクチャと範囲

[English](../architecture.md) | [日本語](../ja/architecture.md) | [繁體中文](../zh-TW/architecture.md) | [한국어](../ko/architecture.md) | [العربية](../ar/architecture.md)

The SDK separates synchronous HTTP access, Desktop-hosted strategies, and local signal utilities. HTTP calls do not run strategies or simulate trades. Hosted strategies use a worker/Host contract; the current P1 Host has no broker, matcher, ledger, or live execution. Local `StrategyRunner` processes caller-supplied bars only.

For complete method details, payload fields, limitations, and examples, see the [English technical reference](../architecture.md).
