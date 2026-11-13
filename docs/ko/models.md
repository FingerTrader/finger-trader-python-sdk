# 모델 및 응답 데이터

[English](../models.md) | [日本語](../ja/models.md) | [繁體中文](../zh-TW/models.md) | [한국어](../ko/models.md) | [العربية](../ar/models.md)

HTTP 서비스 메서드는 `ApiResponse`를 반환합니다. `.data`는 성공 payload, `.code`와 `.message`는 백엔드 envelope 값, `.raw`는 전체 payload입니다. SDK는 계정/거래 스키마를 추측하지 않고 응답을 보존합니다. dataclass는 허용적인 raw-payload wrapper이며 서비스가 자동 변환한다고 보장하지 않습니다.

`MarketBar`는 `finger_trader.models.Bar`의 API alias입니다. `MarketBar.from_dict()`는 일반 OHLCV 키를 `Decimal`로 변환해 이진 부동소수점 오차를 방지합니다. epoch 단위(초/밀리초)는 endpoint별로 확인하세요. WebSocket `recv()`는 dict 또는 폐기된 frame의 경우 `None`을 반환합니다. JSON frame은 1 MiB를 초과할 수 없습니다. Hosted dataclass는 루트 모델과 별개이며 금융 값에 `Decimal`, 시간에 UTC aware datetime, 컬렉션에 불변 snapshot을 사용합니다.
