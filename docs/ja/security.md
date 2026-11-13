# セキュリティ

[English](../security.md) | [日本語](../ja/security.md) | [繁體中文](../zh-TW/security.md) | [한국어](../ko/security.md) | [العربية](../ar/security.md)

本番 HTTP と WebSocket ticket endpoint は HTTPS/WSS を必須とします。loopback 開発 URL のみ HTTP を許可します。TLS 証明書検証は有効で、HTTP redirect は拒否し、ログには method と path のみ記録します。token はメモリ内だけに保持し、GET のネットワーク失敗は一度だけ再試行します。状態変更 POST は再試行しません。

公開ソースの以前の版に Desktop 設定由来の静的 OAuth Basic 値が含まれていた履歴があります。現在のソースでは operator が明示的に設定しますが、Git 履歴からは消えていません。service owner は公開 client identifier か confidential secret かを確認し、必要なら rotation してください。Hosted worker は信頼済みローカルコード向けで、security sandbox ではありません。credential を strategy、parameter、log に埋め込まないでください。

See the [English source](../security.md) for exact request parameters and code examples.
