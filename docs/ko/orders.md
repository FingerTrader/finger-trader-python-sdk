# 주문

[English](../orders.md) | [日本語](../ja/orders.md) | [繁體中文](../zh-TW/orders.md) | [한국어](../ko/orders.md) | [العربية](../ar/orders.md)

현재 SDK는 현행 App API의 주문 이력 조회만 지원합니다. `client.orders.history(*, page=1, limit=20, filters=None)`는 인증 세션의 이력을 읽고 `limit`을 `pageSize`로 매핑합니다. 필터는 wallet_type, market_type, order_type, coin_type, order_side, start_time, end_time입니다.

현재 API에 생성, TP/SL 수정, 취소, 종료 endpoint가 있지만 SDK에 아직 매핑되지 않았습니다. 구형 `submit`, `update_limit`, `cancel_limit`, `set_take_profit_loss`는 폐기된 `api/mob` 경로를 대상으로 하므로 호출하지 마세요. 주문 전송/취소 예제는 없습니다. Hosted Context 주문 인터페이스도 현재 P1 Host에서 `UNSUPPORTED_CAPABILITY`를 반환합니다.

정확한 요청 인수와 코드 예제는 [영문 원문](../orders.md)을 참조하세요.
