# Desktop 管理式 Python 策略

[English](../hosted-strategies.md) | [日本語](../ja/hosted-strategies.md) | [繁體中文](../zh-TW/hosted-strategies.md) | [한국어](../ko/hosted-strategies.md) | [العربية](../ar/hosted-strategies.md)

Hosted 型別須從 `finger_trader.hosted` 匯入。Callback 為同步執行並由 Desktop Host 管理；Context 僅在有效 callback 的所屬執行緒中可用。金融數值使用 `Decimal`，時間使用 UTC aware `datetime`。目前 P1 Host 不會執行交易。

完整方法細節、payload 欄位、限制與範例，請參閱[英文技術文件](../hosted-strategies.md)。
