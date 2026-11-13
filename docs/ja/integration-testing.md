# ライブ API 統合テスト

[English](../integration-testing.md) | [日本語](../ja/integration-testing.md) | [繁體中文](../zh-TW/integration-testing.md) | [한국어](../ko/integration-testing.md) | [العربية](../ar/integration-testing.md)

`integration_tests/` の opt-in suite は `tests/` の mock unit test と別です。対象は `sandbox`、`dev`、`production-read-only`。すべて HTTPS（socket は WSS）を使用し、TLS 検証を維持します。

`.env.integration` に service operator が提供した URL と認証情報を設定し、production では `FINGER_TRADER_IT_ENABLED=1`、target `production-read-only`、確認値 `YES` を明示します。未有効ならネットワーク要求なしで skip し、設定不足なら要求前に失敗します。production suite は read-only で、注文・資金移動などの変更を行いません。

See the [English source](../integration-testing.md) for exact request parameters and code examples.
