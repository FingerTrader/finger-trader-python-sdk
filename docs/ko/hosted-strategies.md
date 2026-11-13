# Desktop 호스팅 Python 전략

[English](../hosted-strategies.md) | [日本語](../ja/hosted-strategies.md) | [繁體中文](../zh-TW/hosted-strategies.md) | [한국어](../ko/hosted-strategies.md) | [العربية](../ar/hosted-strategies.md)

Hosted 타입은 `finger_trader.hosted`에서 가져옵니다. callback은 동기식이며 Desktop Host가 실행합니다. Context는 활성 callback의 소유 스레드에서만 유효합니다. 금융 값은 `Decimal`, 시간은 UTC aware `datetime`을 사용합니다. 현재 P1 Host는 거래를 실행하지 않습니다.

전체 메서드 세부사항, payload 필드, 제한 및 예제는 [영문 기술 문서](../hosted-strategies.md)를 참조하세요.
