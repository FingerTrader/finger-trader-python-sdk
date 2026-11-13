# 포지션

[English](../positions.md) | [日本語](../ja/positions.md) | [繁體中文](../zh-TW/positions.md) | [한국어](../ko/positions.md) | [العربية](../ar/positions.md)

`client.positions.list()`는 현재 `POST /app-api/v1/order/get-holding-orders`를 호출하고 `{page, pageSize, query}`를 전송합니다. `order_status`는 `orderType`(시장가 `0`, 지정가 `1`), 통화는 `coinType`(USD `0`, USDT `100`)에 매핑됩니다. 계정은 인증 세션으로 결정됩니다.

임의 `account_id`는 지원되지 않으며 지정하면 `ValueError`가 발생합니다. `market_type`은 백엔드 enum으로 필터링할 수 있습니다. 원가, 손익, 증거금은 백엔드 응답 모델 그대로 반환됩니다.

전체 예제와 명세는 [영문 원문](../positions.md)을 참조하세요.
