# 即時 API 整合測試

[English](../integration-testing.md) | [日本語](../ja/integration-testing.md) | [繁體中文](../zh-TW/integration-testing.md) | [한국어](../ko/integration-testing.md) | [العربية](../ar/integration-testing.md)

`integration_tests/` 的 opt-in 測試套件與 `tests/` 中僅使用 mock 的單元測試分開。支援 `sandbox`、`dev`、`production-read-only`。所有端點皆須 HTTPS（socket 使用 WSS），並保留 TLS 驗證。

請在 `.env.integration` 設定服務營運者提供的 URL 與驗證資訊。production 必須明確設定 `FINGER_TRADER_IT_ENABLED=1`、target `production-read-only` 及確認值 `YES`。未啟用時不發送網路請求並 skip；設定不足會在請求前失敗。production 套件唯讀，不會送單或異動資金。

精確參數及程式範例請參閱[英文原文](../integration-testing.md)。
