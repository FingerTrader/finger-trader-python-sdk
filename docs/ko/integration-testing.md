# 실 API 통합 테스트

[English](../integration-testing.md) | [日本語](../ja/integration-testing.md) | [繁體中文](../zh-TW/integration-testing.md) | [한국어](../ko/integration-testing.md) | [العربية](../ar/integration-testing.md)

`integration_tests/`의 opt-in 테스트는 `tests/`의 mock 전용 단위 테스트와 별개입니다. `sandbox`, `dev`, `production-read-only` 대상을 지원합니다. 모든 endpoint는 HTTPS(socket은 WSS)를 사용하고 TLS 검증을 유지합니다.

`.env.integration`에 서비스 운영자가 제공한 URL과 인증정보를 설정하세요. production은 `FINGER_TRADER_IT_ENABLED=1`, target `production-read-only`, 확인 문자열 `YES`를 명시해야 합니다. 활성화하지 않으면 네트워크 요청 없이 skip하며, 설정 누락은 요청 전에 실패합니다. production 테스트는 읽기 전용이며 주문이나 자금 변경을 하지 않습니다.

정확한 요청 인수와 코드 예제는 [영문 원문](../integration-testing.md)을 참조하세요.
