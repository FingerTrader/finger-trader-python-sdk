# Finger_desk API mapping (evidence checked 2026-11-08)

[English](api-mapping.md) | [日本語](api-mapping.md) | [繁體中文](api-mapping.md) | [한국어](ko/api-mapping.md) | [العربية](api-mapping.md)


This mapping follows the active generated `dataSdk` provider and current desktop UI call sites in the neighboring `finger_desk` checkout. The older `api/mob` calls formerly mapped here return business error `100000` (`No static resource ...`) on the current app API and have been removed from these read services. Base URLs are defined in `lib/config.dart`: production app API `https://prod-api.fingertrader.com/finger-bff-app`, auth API `https://prod-api.fingertrader.com/finger-auth`, socket auth `https://prod-api.fingertrader.com/finger-bff-socket`, socket `wss://prod-api.fingertrader.com/finger-bff-socket/ws`.

HTTP requests use JSON for ordinary calls, bounded timeouts, `Accept`, the Finger Desk desktop `User-Agent`, and when logged in both `Authorization: {token_type} {access_token}` and legacy `token: {access_token}`. OAuth uses the existing Basic client authentication requirement. The SDK requires operators to provide that value explicitly as `oauth_basic_token`; it is not a user API key and no value is built into the package. A previous SDK revision included the desktop app value, which is documented in the security review as a historical exposure.

| Capability | Endpoint/method | Parameters / body | SDK |
|---|---|---|---|
| OAuth token | `POST {auth}/oauth2/token` | form fields `username`, `password`, `grant_type=password`, `type` (`0` email, `1` mobile per `AccountTypeEnum`), optional `captchaId`, `captchaCode`; Basic auth | `auth.login` |
| CAPTCHA | `GET {auth}/api/v1/auth/captcha` | none | `auth.captcha` |
| WS ticket | `POST {socket-auth}/ws-api/v1/auth/build-ticket` | no body contract shown; desktop request interceptor attaches user token | `websocket()` |
| Markets and enabled market types | `POST /app-api/v1/public/get-maker-info` | no body | `market_data.markets` |
| Stock, Forex, Crypto, Spot, Indices products | `POST /app-api/v1/market/ticker-list` | `{page, pageSize, query: {marketType}}`; enum: Forex 0, Spot 1, Crypto 2, Stock 3, Indices 6 | `market_data.symbols(market, page, page_size)` |
| Historical OHLCV | `POST /app-api/v1/market/kline-list` | `{market, ticker, interval, startTime, limit}`; market enum as above; `startTime` is epoch milliseconds encoded as a string; pagination advances with startTime | `market_data.history` |
| Account profile | `POST /app-api/v1/public/login-info` | no body; authenticated user session | `accounts.detail` / `accounts.list` |
| Account wallet/balance | `POST /app-api/v1/fund/get-spot-wallet` | no body; authenticated user session | `accounts.balance` |
| Current holdings / open orders | `POST /app-api/v1/order/get-holding-orders` | `{page,pageSize,query:{marketType,orderType,coinType,...}}`; USD coin type 0, USDT 100 | `positions.list` |
| Submit order (current Desk contract) | `POST /app-api/v1/order/create-order` | `ticker,orderType,orderSide,qty,coinType,walletType,price,marginRate,stopLoss,takeProfit,marketType` | Not yet mapped by this SDK's legacy `orders.submit` signature |
| Order history | `POST /app-api/v1/order/trade-history` | `{page,pageSize,query:{walletType,marketType,orderType,coinType,orderSide,startTime,endTime}}` | `orders.history` |
| Modify order / TP-SL (current Desk contract) | `POST /app-api/v1/order/modify-stop-profit-loss` | `orderId` plus supported update fields from `OrderUpdateDTO` | Not yet mapped; legacy SDK method targets are stale |
| Cancel order (current Desk contract) | `POST /app-api/v1/order/cancel-order` | `OrderLimitCancelDTO` body containing `orderId` | Not yet mapped; legacy SDK method target is stale |
| Close position (current Desk contract) | `POST /app-api/v1/order/close-order` | `orderId`, optional `qty` | Not exposed in this SDK |
| WS market subscribe | WebSocket `/ws?ticket=...` | UTF-8 JSON envelope in binary frames; `action=3`, `msgType=1` (quote subscribe), `content.tickerList`; market is implied by ticker identifiers in this DTO; handshake omits `Origin` | optional WS client |

## Known gaps and caveats

The API provider exposes single-user-session trade context rather than a list of arbitrary account IDs. It does not establish a separate account selector, executions endpoint, HTTP quote snapshot endpoint, stable idempotency-key support, or token refresh request. The current dataSdk exposes current order mutation DTOs; this SDK's corresponding mutation wrappers still target the removed legacy `api/mob` routes and must not be used with the current API until migrated. Market-data subscription payloads carry ticker lists; subscription message type 3 is also used by desktop for depth, while this SDK exposes the confirmed quote subscription type 1. Successful envelope response shapes are retained in raw form and callers can decode additional fields without loss.

The desktop uses market-specific lists and Kline frames, whose exact payload fields vary. This SDK therefore preserves raw response data and offers decimal-safe `Bar.from_dict` as an opt-in mapper. A matching `websocket-client` optional install is required for socket use; no third-party package is required for HTTP.
