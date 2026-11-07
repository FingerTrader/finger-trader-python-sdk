# Finger_desk API mapping (evidence checked 2026-11-08)

This mapping follows Flutter's request providers and service code in the neighboring `finger_desk` checkout. No backend OpenAPI contract was found during the local review, so the mobile BFF calls are the current evidence. Base URLs are defined in `lib/config.dart`: production app API `https://prod-api.fingertrader.com/finger-bff-app`, auth API `https://prod-api.fingertrader.com/finger-auth`, socket auth `https://prod-api.fingertrader.com/finger-bff-socket`, socket `wss://prod-api.fingertrader.com/finger-bff-socket/ws`.

HTTP requests use JSON for ordinary calls, 10 second connect and 5 second receive timeouts, `Accept-Language`, `User-Agent`, and when logged in both `Authorization: {token_type} {access_token}` and legacy `token: {access_token}`. OAuth uses the existing Basic client authentication requirement. The SDK requires operators to provide that value explicitly as `oauth_basic_token`; it is not a user API key and no value is built into the package. A previous SDK revision included the desktop app value, which is documented in the security review as a historical exposure.

| Capability | Endpoint/method | Parameters / body | SDK |
|---|---|---|---|
| OAuth token | `POST {auth}/oauth2/token` | form fields `username`, `password`, `grant_type=password`, `type`, optional `captchaId`, `captchaCode`; Basic auth | `auth.login` |
| CAPTCHA | `GET {auth}/api/v1/auth/captcha` | none | `auth.captcha` |
| WS ticket | `POST {socket-auth}/ws-api/v1/auth/build-ticket` | no body contract shown; desktop request interceptor attaches user token | `websocket()` |
| Markets | `GET /api/mob/trade/profile-entity/getMarket` | none | `market_data.markets` |
| Crypto symbols | `GET /api/mob/market/crypto/getCryptoIndexTicker/{page}` | page | `market_data.symbols(market='crypto')` |
| Forex symbols | `GET /api/mob/market/forex-base-info-entity/getForexIndexTicker/{page}` | page | `market_data.symbols(market='forex')` |
| Spot symbols | `GET /api/mob/market/spot-base-info-entity/getSpotIndexTicker/{page}` | page | `market_data.symbols(market='spot')` |
| Stock symbols | `GET /api/mob/market/stock/stock-us-base-info/getHotTicker` | none | `market_data.symbols(market='stock')` |
| Index symbols | `GET /api/mob/market/indices-info-entity/getIndicesIndexTicker/{page}` | page | `market_data.symbols(market='indices')` |
| OHLCV | `GET /api/mob/market/kline/getKline` | `market`, `ticker`, `interval`, `limit`, `page`, optional epoch-ms `startTime` | `market_data.history` |
| Account trading profile | `GET /api/mob/trade/order-entity/getTradeProfileResponse` | `market` | `accounts.detail`; `list` uses market 0 because no all-account operation was found |
| Account wallet/balance | `GET /api/mob/trade/wallet-entity/getWalletHomePage` | session scoped | `accounts.balance` |
| Current holdings | `GET /api/mob/trade/order-entity/getHoldingListByIsUsd` | `type`, boolean `isUsd`; session scoped | `positions.list` |
| Submit order | `POST /api/mob/trade/order-entity/order` | `isBuy,isUsd,limitTime,market,orderId,orderType,price,quantity,ticker,isCreate,marginRatio,stopLose,takeProfit` | `orders.submit` |
| Order history | `GET /api/mob/trade/order-entity/getOrderHistory/{page}/{limit}` | query from `HistorySearchDto` | `orders.history` |
| Update limit order | `POST /api/mob/trade/order-entity/updateLimitOrder` | `id,price,quantity,stopLose,takeProfit` | `orders.update_limit` |
| Cancel limit order | `POST /api/mob/trade/order-entity/cancelLimitOrder` | query `orderId` | `orders.cancel_limit` |
| Set TP/SL | `POST /api/mob/trade/order-entity/setTakeProfitAndLoss` | `orderId,stopLoss,takeProfit` | `orders.set_take_profit_loss` |
| WS market subscribe | WebSocket `/ws?ticket=...` | envelope `action=3`, `msgType=1` (quote subscribe), `content.tickerList`; market is implied by ticker identifiers in this DTO | optional WS client |

## Known gaps and caveats

The API provider exposes single-user-session trade context rather than a list of arbitrary account IDs. It does not establish a separate account selector, open-order listing, executions endpoint, HTTP quote snapshot endpoint, stable order status enumeration, idempotency-key support, or token refresh request. These are deliberately not invented. `orderId` and `isCreate` semantics depend on the server's `TradeEntity` and enum values; callers must supply the server values. Market-data subscription payloads carry ticker lists; subscription message type 3 is also used by desktop for depth, while this SDK exposes the confirmed quote subscription type 1. Successful envelope response shapes are retained in raw form and callers can decode additional fields without loss.

The desktop uses market-specific lists and Kline frames, whose exact payload fields vary. This SDK therefore preserves raw response data and offers decimal-safe `Bar.from_dict` as an opt-in mapper. A matching `websocket-client` optional install is required for socket use; no third-party package is required for HTTP.
