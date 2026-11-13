# 安全性

[English](../security.md) | [日本語](../ja/security.md) | [繁體中文](../zh-TW/security.md) | [한국어](../ko/security.md) | [العربية](../ar/security.md)

production HTTP 與 WebSocket ticket 端點必須使用 HTTPS/WSS。只有 loopback 開發 URL 可使用 HTTP。TLS 憑證驗證保持啟用；HTTP 重新導向會被拒絕；記錄只包含 method 與 path。token 僅存在記憶體。GET 網路失敗最多重試一次；狀態異動 POST 不會重試。

舊版公開原始碼曾包含來自 Desktop 設定的固定 OAuth Basic 值。現行原始碼改由營運者明確設定，但舊 Git 歷史仍保留該值。服務負責人應確認它是公開 client ID 或機密 secret，必要時輪替。Hosted worker 面向可信任本機程式碼，並非安全沙箱。請勿將憑證放入策略、參數或記錄。

精確參數及程式範例請參閱[英文原文](../security.md)。
