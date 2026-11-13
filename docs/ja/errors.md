# 例外とエラー

[English](../errors.md) | [日本語](../ja/errors.md) | [繁體中文](../zh-TW/errors.md) | [한국어](../ko/errors.md) | [العربية](../ar/errors.md)

`APIError` reports backend failures; `NetworkError` reports transport failures. `UnknownOutcomeError` means a state-changing request may have reached the server; reconcile before retrying. Invalid arguments raise `ValueError`; unsupported endpoints raise `NotImplementedError`. Hosted errors use stable business `code` values.

For complete method details, payload fields, limitations, and examples, see the [English technical reference](../errors.md).
