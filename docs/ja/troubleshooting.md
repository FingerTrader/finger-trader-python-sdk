# トラブルシューティング

[English](../troubleshooting.md) | [日本語](../ja/troubleshooting.md) | [繁體中文](../zh-TW/troubleshooting.md) | [한국어](../ko/troubleshooting.md) | [العربية](../ar/troubleshooting.md)

401/403 は auth/app URL、token type、有効期限、session permission を確認します。password login には service operator が提供する OAuth Basic 値が必要です。CAPTCHA 要求時は captcha fields を渡します。TLS error 時は正しい HTTPS endpoint と信頼済み CA を確認し、証明書検証を無効化しないでください。

空の market/history は ticker、market、interval、開始時刻、権限を確認します。WebSocket で quote が届かない場合は ticket、正確な ticker、購読権限、市場時間を確認し、`recv()` を定期実行します。`UnknownOutcomeError` 後は order history で照合し、直ちに再送しないでください。Hosted Context は callback の所有 thread 内でのみ使用できます。

See the [English source](../troubleshooting.md) for exact request parameters and code examples.
