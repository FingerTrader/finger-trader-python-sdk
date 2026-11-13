# SDK 아키텍처와 범위

[English](../architecture.md) | [日本語](../ja/architecture.md) | [繁體中文](../zh-TW/architecture.md) | [한국어](../ko/architecture.md) | [العربية](../ar/architecture.md)

SDK는 동기 HTTP, Desktop 호스팅 전략, 로컬 시그널 도구를 분리합니다. HTTP 호출은 전략을 실행하거나 거래를 시뮬레이션하지 않습니다. Hosted 전략은 worker/Host 계약을 사용하며 현재 P1 Host에는 브로커, 매칭 엔진, 원장, 실거래 기능이 없습니다. 로컬 `StrategyRunner`는 호출자가 제공한 봉만 처리합니다.

전체 메서드 세부사항, payload 필드, 제한 및 예제는 [영문 기술 문서](../architecture.md)를 참조하세요.
