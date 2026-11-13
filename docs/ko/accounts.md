# 계정 및 잔액

[English](../accounts.md) | [日本語](../ja/accounts.md) | [繁體中文](../zh-TW/accounts.md) | [한국어](../ko/accounts.md) | [العربية](../ar/accounts.md)

현재 프로필 및 지갑 조회는 인증된 세션에 한정됩니다. SDK는 임의 계정 ID를 열거하거나 자산·가용자금·증거금을 계산하지 않습니다. `client.accounts.list()`, `.detail()`, `.balance()`를 사용하며 응답 필드와 정밀도는 백엔드가 결정합니다.

전체 메서드 세부사항, payload 필드, 제한 및 예제는 [영문 기술 문서](../accounts.md)를 참조하세요.
