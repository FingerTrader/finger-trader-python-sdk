# 예제

[English](README.md) | [日本語](README.md) | [繁體中文](README.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

SDK를 설치한 뒤 저장소 루트에서 스크립트를 실행하세요 (`python -m pip install .`). 읽기 전용 인증 예제에는 셸 또는 비밀정보 관리자에 `FINGER_TRADER_ACCESS_TOKEN`을 설정합니다. 실제 값을 소스 관리나 셸 기록에 남기지 마세요.

| 스크립트 | 설명 | 거래 상태 변경 |
|---|---|---|
| `api_read_only.py` | 시장/계정/포지션/주문 이력 조회 | 아니요 |
| `authentication_example.py` | 환경 변수 기반 OAuth 로그인 | 아니요 |
| `market_data_example.py` | 시장과 상품 카테고리 조회 | 아니요 |
| `historical_bars_example.py` | OHLCV 조회 및 선택적 Decimal 변환 | 아니요 |
| `accounts_example.py` | 세션 프로필과 지갑 | 아니요 |
| `positions_example.py` | 현재 포지션 | 아니요 |
| `order_history_example.py` | 주문 이력 조회 | 아니요 |
| `websocket_example.py` | 티켓 기반 시세 구독 (`.[websocket]` 필요) | 아니요 |
| `dual_ma_strategy.py` | 합성 봉에 대한 로컬 예제, API 호출 없음 | 아니요 |

예제는 context manager로 네트워크 자원을 정리하고 예상되는 API/네트워크 오류를 처리합니다. 인증 토큰을 출력하지 않습니다. SDK는 현재 앱 API의 주문 쓰기를 구현하지 않으므로 주문 제출 예제가 없습니다. 자세한 내용은 [주문 문서](../docs/orders.md)를 확인하세요.

```sh
python examples/market_data_example.py
```

`dual_ma_strategy.py`는 독립적인 로컬 시그널 API를 사용합니다. Desktop 관리형 API는 [Hosted Strategy 안내서](../docs/hosted-strategies.md)를 참조하세요. 현행 P1 Host는 주문 실행을 제공하지 않습니다.
