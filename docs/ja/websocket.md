# WebSocket 市場データ

[English](../websocket.md) | [日本語](../ja/websocket.md) | [繁體中文](../zh-TW/websocket.md) | [한국어](../ko/websocket.md) | [العربية](../ar/websocket.md)

WebSocket 機能には `python -m pip install ".[websocket]"` が必要です。ticket を取得して WSS 接続し、ticker を購読します。wire format は Finger_desk base envelope の UTF-8 JSON を binary frame で送ります。quote subscription は `action=3`、`msgType=1`、`content.tickerList` を使います。ticket は `/ws-api/v1/auth/build-ticket` で取得し、`/ws?ticket=...` に渡します。handshake では `Origin` を送信しません。

この同期 API では `recv()` を定期的に呼ぶ必要があります。keepalive を処理し、切断時は上限付き exponential reconnect、新 ticket の取得、現行 ticker set の再購読を行います。`unsubscribe()` は残りの ticker 全体を再送し、空配列なら購読を解除します。`max_reconnect_attempts` の既定値は 3 です。市場識別子は確認済み DTO に含まれず、protobuf や口座／注文 event もサポートしません。
