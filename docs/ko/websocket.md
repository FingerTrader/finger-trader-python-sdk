# WebSocket 시장 데이터

[English](../websocket.md) | [日本語](../ja/websocket.md) | [繁體中文](../zh-TW/websocket.md) | [한국어](../ko/websocket.md) | [العربية](../ar/websocket.md)

WebSocket 기능은 `python -m pip install ".[websocket]"` 설치가 필요합니다. ticket을 발급받아 WSS에 연결한 뒤 ticker를 구독합니다. wire format은 Finger_desk base envelope의 UTF-8 JSON을 binary frame으로 전송합니다. 시세 구독은 `action=3`, `msgType=1`, `content.tickerList`를 사용합니다. ticket은 `/ws-api/v1/auth/build-ticket`에서 받고 `/ws?ticket=...`로 전달합니다. handshake에는 `Origin`을 넣지 않습니다.

동기 API이므로 `recv()`를 주기적으로 호출해야 합니다. keepalive를 처리하며 연결이 끊기면 제한된 exponential reconnect 후 새 ticket을 받고 활성 ticker를 재구독합니다. `unsubscribe()`는 남은 ticker 전체를 다시 보내며 빈 목록은 구독을 지웁니다. `max_reconnect_attempts` 기본값은 3입니다. 확인된 DTO에는 시장 식별자가 없으며 protobuf와 계정/주문 이벤트 구독도 지원하지 않습니다.
