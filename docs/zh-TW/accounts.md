# 帳戶與餘額

[English](../accounts.md) | [日本語](../ja/accounts.md) | [繁體中文](../zh-TW/accounts.md) | [한국어](../ko/accounts.md) | [العربية](../ar/accounts.md)

目前個人資料與錢包查詢皆限定於已驗證工作階段。SDK 不會列舉任意帳戶 ID，也不會自行計算淨值、可用資金或保證金。可使用 `client.accounts.list()`、`.detail()` 與 `.balance()`；欄位及精度以後端回應為準。

完整方法細節、payload 欄位、限制與範例，請參閱[英文技術文件](../accounts.md)。
