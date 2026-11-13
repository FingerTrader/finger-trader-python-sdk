# 문제 해결

[English](../troubleshooting.md) | [日本語](../ja/troubleshooting.md) | [繁體中文](../zh-TW/troubleshooting.md) | [한국어](../ko/troubleshooting.md) | [العربية](../ar/troubleshooting.md)

401/403은 auth/app URL, token type, 만료 시각, 세션 권한을 확인하세요. 비밀번호 로그인에는 서비스 운영자가 제공한 OAuth Basic 값이 필요합니다. CAPTCHA가 필요하면 해당 필드를 전달하세요. TLS 오류는 HTTPS endpoint와 신뢰 CA를 확인하고 인증서 검증을 끄지 마세요.

시장/이력 결과가 비어 있으면 ticker, market, interval, 시작 시각, 권한을 확인하세요. WebSocket 시세가 오지 않으면 ticket, 정확한 ticker, 구독 권한, 시장 시간을 확인하고 `recv()`를 주기적으로 호출하세요. `UnknownOutcomeError` 이후에는 주문 이력을 대조한 뒤 조치하고 즉시 재전송하지 마세요. Hosted Context는 callback 소유 스레드에서만 사용할 수 있습니다.

정확한 요청 인수와 코드 예제는 [영문 원문](../troubleshooting.md)을 참조하세요.
