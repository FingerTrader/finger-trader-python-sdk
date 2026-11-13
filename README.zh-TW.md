# Finger Trader Python SDK

### 為開發者打造的金融市場 API 與量化策略工具

[English](README.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [العربية](README.ar.md)

Finger Trader Python SDK 提供同步 HTTP API 用戶端、以票證驗證的市場資料 WebSocket，以及由 Desktop Host 管理的 Python 策略 API。目前版本為 alpha（`0.1.0`），需由原始碼安裝。HTTP 回應保留後端資料結構；Hosted Strategy 使用 Decimal／UTC 資料模型與獨立 worker 程序。

P1 Hosted Strategy 實作已包含於原始碼，但 SDK 本身不包含回測引擎、券商或即時下單服務。功能範圍與限制請參閱[Hosted Strategy 指南](docs/hosted-strategies.md)。

## 目前功能

- OAuth2 密碼登入及使用既有存取權杖
- 查詢市場清單、商品清單與歷史 OHLCV 資料
- 查詢已驗證工作階段的個人資料、錢包、持倉與訂單紀錄
- 以票證驗證的 JSON 市場資料 WebSocket
- 透過 `finger_trader.hosted` 執行由 Desktop 管理的策略、同步生命週期、具型別的 Context 與 JSON-RPC worker
- 對呼叫端提供的 K 線資料使用獨立的本機指標與訊號工具

目前 SDK 尚未透過受支援的方法提供現行 App API 的下單、修改、取消或成交查詢。請勿使用舊版相容方法進行實盤交易。

## 安裝

SDK 尚未發布至 PyPI。請從 GitHub 取得原始碼後安裝：

```sh
git clone https://github.com/FingerTrader/fingertrader-python-sdk.git
cd fingertrader-python-sdk
python -m pip install .
```

若需使用 WebSocket，請在複製下來的儲存庫中執行 `python -m pip install '.[websocket]'`。需要 Python 3.10 以上版本。

## 快速開始

將存取權杖設為環境變數 `FINGER_TRADER_ACCESS_TOKEN`，再呼叫唯讀的已驗證 API：

```python
import os
from finger_trader import FingerTraderClient

with FingerTraderClient(token=os.environ["FINGER_TRADER_ACCESS_TOKEN"]) as client:
    markets = client.market_data.markets()
    products = client.market_data.symbols(market="stock", page_size=10)
    bars = client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=100)
    wallet = client.accounts.balance()
    print(markets.data, products.data, bars.data, wallet.data)
```

請勿輸出權杖或完整的驗證回應。SDK 不包含送出訂單的範例。

## 文件

- [文件索引](docs/zh-TW/index.md) · [安裝](docs/zh-TW/installation.md) · [快速開始](docs/zh-TW/quickstart.md)
- [驗證](docs/zh-TW/authentication.md) · [設定](docs/zh-TW/configuration.md) · [安全性](docs/security.md)
- [市場資料](docs/market-data.md) · [帳戶](docs/accounts.md) · [持倉](docs/positions.md) · [訂單紀錄](docs/orders.md) · [WebSocket](docs/websocket.md)
- [Hosted Strategy](docs/hosted-strategies.md) · [資料模型](docs/models.md) · [API 參考](docs/api-reference.md) · [API 對照](docs/api-mapping.md)
- [錯誤處理](docs/errors.md) · [疑難排解](docs/troubleshooting.md) · [範例](examples/README.zh-TW.md)

完整契約、精確型別簽章，以及內部開發／驗收紀錄請參閱英文原文。使用前請確認 SDK 公開 API 與 Desktop Host 支援範圍符合目前發布版本。

## 支援與貢獻

請透過 [GitHub Issues](https://github.com/FingerTrader/fingertrader-python-sdk/issues) 回報錯誤或提出 API 支援需求。歡迎貢獻；程式碼變更請附上測試，若公開行為有所變動，請一併更新文件。

## 安全性與授權

請勿提交密碼、OAuth 用戶端資訊、存取權杖或客戶資料。正式環境會啟用 TLS 憑證驗證。Hosted Strategy 僅應執行可信任的本機程式碼；worker 並非安全沙箱。請參閱[安全性指南](docs/security.md)。

本專案採用 [Apache-2.0](LICENSE) 授權。API 與市場資料的使用仍須符合帳戶權限及適用的服務條款。
