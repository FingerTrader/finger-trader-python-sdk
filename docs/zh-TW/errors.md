# 例外與錯誤

[English](../errors.md) | [日本語](../ja/errors.md) | [繁體中文](../zh-TW/errors.md) | [한국어](../ko/errors.md) | [العربية](../ar/errors.md)

`APIError` 表示後端錯誤；`NetworkError` 表示傳輸錯誤。`UnknownOutcomeError` 表示狀態異動請求可能已送達伺服器，重試前須先核對。無效參數會引發 `ValueError`；未支援端點會引發 `NotImplementedError`。Hosted 錯誤使用穩定的業務 `code`。

完整方法細節、payload 欄位、限制與範例，請參閱[英文技術文件](../errors.md)。
