# 보안

[English](../security.md) | [日本語](../ja/security.md) | [繁體中文](../zh-TW/security.md) | [한국어](../ko/security.md) | [العربية](../ar/security.md)

프로덕션 HTTP 및 WebSocket ticket endpoint는 HTTPS/WSS를 요구합니다. loopback 개발 URL만 HTTP를 허용합니다. TLS 검증을 유지하고 HTTP redirect를 거부하며 로그에는 method와 path만 기록합니다. token은 메모리에만 보관합니다. GET 네트워크 실패는 한 번 재시도할 수 있으나 상태 변경 POST는 재시도하지 않습니다.

이전 공개 소스 버전에는 Desktop 설정의 정적 OAuth Basic 값이 포함됐던 이력이 있습니다. 현재 소스는 운영자가 명시적으로 설정하지만 과거 Git 기록에서는 제거되지 않았습니다. 서비스 소유자는 공개 client ID인지 기밀 secret인지 확인하고 필요하면 교체해야 합니다. Hosted worker는 신뢰된 로컬 코드용이지 보안 샌드박스가 아닙니다. 자격증명을 전략, 매개변수, 로그에 넣지 마세요.

정확한 요청 인수와 코드 예제는 [영문 원문](../security.md)을 참조하세요.
