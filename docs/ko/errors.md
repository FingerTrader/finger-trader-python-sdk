# 예외 및 오류

[English](../errors.md) | [日本語](../ja/errors.md) | [繁體中文](../zh-TW/errors.md) | [한국어](../ko/errors.md) | [العربية](../ar/errors.md)

`APIError`는 백엔드 실패, `NetworkError`는 전송 실패를 나타냅니다. `UnknownOutcomeError`는 상태 변경 요청이 서버에 도달했을 수 있음을 뜻하므로 재시도 전에 대조해야 합니다. 잘못된 인수는 `ValueError`, 미지원 작업은 `NotImplementedError`를 발생시킵니다. Hosted 오류는 안정적인 업무 `code`를 사용합니다.

전체 메서드 세부사항, payload 필드, 제한 및 예제는 [영문 기술 문서](../errors.md)를 참조하세요.
