# WebSocket 市場資料

[English](../websocket.md) | [日本語](../ja/websocket.md) | [繁體中文](../zh-TW/websocket.md) | [한국어](../ko/websocket.md) | [العربية](../ar/websocket.md)

WebSocket 功能需安裝 `python -m pip install ".[websocket]"`。取得 ticket 後建立 WSS 連線並訂閱 ticker。wire format 使用 Finger_desk base envelope，以 binary frame 傳送 UTF-8 JSON。報價訂閱欄位為 `action=3`、`msgType=1`、`content.tickerList`。ticket 由 `/ws-api/v1/auth/build-ticket` 取得，並傳入 `/ws?ticket=...`；handshake 不帶 `Origin`。

此同步 API 需定期呼叫 `recv()`。用戶端會處理 keepalive，斷線時以有限次數 exponential reconnect、取得新 ticket 並重新訂閱現有 ticker。`unsubscribe()` 會重新送出剩餘 ticker；空清單可清除訂閱。`max_reconnect_attempts` 預設為 3。已確認 DTO 不含市場識別欄位，也不支援 protobuf 或帳戶／訂單事件。
