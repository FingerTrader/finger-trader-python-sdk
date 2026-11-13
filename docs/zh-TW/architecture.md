# SDK 架構與範圍

[English](../architecture.md) | [日本語](../ja/architecture.md) | [繁體中文](../zh-TW/architecture.md) | [한국어](../ko/architecture.md) | [العربية](../ar/architecture.md)

SDK 分為同步 HTTP 存取、Desktop 管理的策略及本機訊號工具。HTTP 呼叫不會執行策略或模擬交易。Hosted Strategy 使用 worker/Host 契約；目前 P1 Host 沒有券商、撮合器、帳本或即時執行。本機 `StrategyRunner` 僅處理呼叫端提供的 K 線。

完整方法細節、payload 欄位、限制與範例，請參閱[英文技術文件](../architecture.md)。
