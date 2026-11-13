# 疑難排解

[English](../troubleshooting.md) | [日本語](../ja/troubleshooting.md) | [繁體中文](../zh-TW/troubleshooting.md) | [한국어](../ko/troubleshooting.md) | [العربية](../ar/troubleshooting.md)

401/403 請檢查 auth/app URL、token type、有效期限及工作階段權限。密碼登入需要服務營運者提供的 OAuth Basic 值。若要求 CAPTCHA，需傳入相應欄位。TLS 錯誤請確認 HTTPS 端點及信任的 CA，切勿關閉憑證驗證。

市場或歷史資料為空時，請確認 ticker、market、interval、起始時間及權限。WebSocket 收不到報價時，檢查 ticket、ticker 完整名稱、訂閱權限及市場交易時段，並定期呼叫 `recv()`。遇到 `UnknownOutcomeError` 後先查訂單歷史核對，不要立即重送。Hosted Context 只能在 callback 所屬執行緒使用。

精確參數及程式範例請參閱[英文原文](../troubleshooting.md)。
