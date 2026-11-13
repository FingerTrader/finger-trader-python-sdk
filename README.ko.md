# Finger Trader Python SDK

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

Finger Trader Python SDK는 동기식 HTTP API, 티켓 인증 시장 데이터 WebSocket, Desktop Host가 관리하는 Python 전략 API를 제공합니다. 현재 alpha(`0.1.0`) 단계이며 소스에서 설치해야 합니다. HTTP 응답은 백엔드 원본 구조를 보존합니다. Hosted Strategy는 불변 Decimal/UTC 모델을 사용하고 별도의 worker 프로세스를 통해 Desktop Host와 통신합니다.

P1 Hosted 구현은 소스에 포함되어 있지만 독립 백테스트 엔진, 브로커 또는 실거래 실행 서비스는 포함되지 않습니다. 구현 내용과 제한은 [Hosted Strategy 안내서](docs/ko/hosted-strategies.md)를 참조하세요.

## 현재 기능

- OAuth2 비밀번호 로그인 및 기존 액세스 토큰 사용
- 시장 메뉴, 상품 목록, 과거 OHLCV 데이터 조회
- 인증된 세션의 프로필, 지갑/잔액, 보유 포지션, 주문 내역 조회
- 티켓 인증 JSON 시장 데이터 WebSocket 구독
- `finger_trader.hosted` 기반 Desktop 관리형 전략, 동기식 생명주기 callback, 형식화된 Context, JSON-RPC worker
- 호출자가 제공한 봉 데이터에 사용하는 독립 로컬 지표와 시그널 도구

현재 앱 API의 주문 생성·수정·취소 및 체결 조회는 지원 SDK 메서드로 제공되지 않습니다. 호환성만을 위해 남아 있는 구형 변경 메서드를 실거래에 사용하지 마세요. HTTP 시세 스냅샷, 토큰 갱신, 임의 계정 선택, 확인된 체결 내역 API도 없습니다.

## 시작 경로

| 목적 | 진입점 | 안내서 |
|---|---|---|
| HTTP API 조회 또는 시세 스트리밍 | `FingerTraderClient` | [빠른 시작](docs/quickstart.md) |
| Desktop이 관리하는 전략 작성 | `finger_trader.hosted.Strategy` | [Hosted Strategy](docs/ko/hosted-strategies.md) |
| 로컬 봉 데이터와 신호 실험 | `StrategyRunner` | [로컬 예제](examples/README.ko.md) |

Hosted Context 메서드는 Host가 부여한 capability에 따라 동작합니다. 주문 메서드의 선언이 거래 엔진을 제공하는 것은 아닙니다. 현재 P1 Desktop 통합은 거래 요청에 `UNSUPPORTED_CAPABILITY`를 반환합니다.

## 설치 요구 사항

Python 3.10 이상이 필요합니다. PyPI에는 아직 게시되지 않았습니다.

```sh
git clone https://github.com/FingerTrader/fingertrader-python-sdk.git
cd fingertrader-python-sdk
python -m pip install .
```

WebSocket 기능은 저장소에서 `python -m pip install '.[websocket]'`으로 설치하세요. 설치 및 환경별 안내는 [설치 문서](docs/installation.md)를 참조하세요.

## 빠른 시작

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
    markets = client.market_data.markets()
    products = client.market_data.symbols(market="stock", page_size=10)
    bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=100)
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

OAuth 로그인, 환경 설정, 비밀정보 취급은 [인증](docs/ko/authentication.md) 및 [구성](docs/ko/configuration.md)을 확인하세요. 토큰이나 전체 인증 응답을 출력하지 마세요.

## 문서

전체 문서 목록은 [문서 색인](docs/index.md)을 참조하세요. 여기에는 Hosted API 계약, 구현 상태, 아키텍처, API 참조와 매핑, 보안, 통합 테스트, 문제 해결이 포함됩니다. 실행 가능한 예제는 [examples](examples/README.ko.md)에 있습니다.

## 지원 및 보안

버그 신고와 API 지원 요청은 [GitHub Issues](https://github.com/FingerTrader/fingertrader-python-sdk/issues)를 이용하세요. 비밀번호, OAuth 클라이언트 값, 액세스 토큰 또는 고객 데이터를 커밋하지 마세요. 프로덕션 TLS 검증은 활성화되어 있으며 리디렉션을 따르지 않습니다. Hosted 코드는 신뢰할 수 있는 로컬 코드만 실행해야 합니다. worker는 보안 샌드박스가 아닙니다. 라이선스는 [Apache-2.0](LICENSE)입니다.
