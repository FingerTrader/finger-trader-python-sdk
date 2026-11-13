# Examples / 範例

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

安裝 SDK 後，請在儲存庫根目錄執行指令碼（`python -m pip install .`）。唯讀驗證範例需在 shell 或密鑰管理工具設定 `FINGER_TRADER_ACCESS_TOKEN`。請勿將實際值存入原始碼管理或 shell 歷史。

| 指令碼 | 說明 | 是否變更交易狀態 |
|---|---|---|
| `api_read_only.py` | 唯讀查詢市場／帳戶／持倉／訂單歷史 | 否 |
| `authentication_example.py` | 使用環境變數進行 OAuth 登入 | 否 |
| `market_data_example.py` | 市場及商品分類 | 否 |
| `historical_bars_example.py` | OHLCV 查詢與選用 Decimal 轉換 | 否 |
| `accounts_example.py` | 工作階段個人資料與錢包 | 否 |
| `positions_example.py` | 目前持倉 | 否 |
| `order_history_example.py` | 訂單歷史查詢 | 否 |
| `websocket_example.py` | Ticket 報價訂閱；需安裝 `.[websocket]` | 否 |
| `dual_ma_strategy.py` | 使用合成 K 線的本機範例，不呼叫 API | 否 |

範例使用 context manager 釋放網路資源並處理預期的 API／網路錯誤，不會輸出驗證權杖。目前 SDK 尚未實作現行 App API 寫入操作，因此不提供送單範例。請參閱[訂單說明](../docs/orders.md)。

```sh
python examples/market_data_example.py
```

`dual_ma_strategy.py` 使用獨立的本機訊號 API。Desktop 管理式 API 請參閱[Hosted Strategy 指南](../docs/hosted-strategies.md)。目前 P1 Host 不提供訂單執行。
