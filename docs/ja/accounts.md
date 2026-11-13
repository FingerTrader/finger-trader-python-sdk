# アカウントと残高

[English](../accounts.md) | [日本語](../ja/accounts.md) | [繁體中文](../zh-TW/accounts.md) | [한국어](../ko/accounts.md) | [العربية](../ar/accounts.md)

Current profile and wallet calls are session-scoped. The SDK does not enumerate arbitrary account IDs or calculate equity, available funds, or margin. Use `client.accounts.list()`, `.detail()`, and `.balance()`; payload fields and precision are returned by the backend.

For complete method details, payload fields, limitations, and examples, see the [English technical reference](../accounts.md).
