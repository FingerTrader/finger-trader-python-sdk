"""Synchronous client for the Finger Trader HTTP API."""
from __future__ import annotations

import json
import logging
import os
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import APIError, ApiResponse

PROD_API = "https://prod-api.fingertrader.com/finger-bff-app"
PROD_AUTH = "https://prod-api.fingertrader.com/finger-auth"
PROD_SOCKET_AUTH = "https://prod-api.fingertrader.com/finger-bff-socket"
_CLIENT_ID = "ZmluZ2VyLWFwcDoxMjM0NTY="  # Finger_desk's public app client credential


class _HTTP:
    def __init__(self, base_url: str, timeout: float, token: str | None = None,
                 token_type: str = "Bearer", basic_auth: str | None = None):
        self.base_url, self.timeout = base_url.rstrip("/"), timeout
        self.token, self.token_type, self.basic_auth = token, token_type, basic_auth
        self.log = logging.getLogger("finger_trader.http")

    def request(self, method: str, path: str, *, params=None, body=None, form=False,
                authenticated=False, retry_safe=False):
        query = "?" + urlencode(params, doseq=True) if params else ""
        url = self.base_url + path + query
        headers = {"Accept": "application/json"}
        payload = None
        if body is not None:
            if form:
                payload = urlencode(body).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                payload = json.dumps(body, separators=(",", ":")).encode()
                headers["Content-Type"] = "application/json"
        if self.basic_auth:
            headers["Authorization"] = "Basic " + self.basic_auth
        if authenticated and self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
            headers["token"] = self.token  # legacy header sent by the desktop app
        request = Request(url, data=payload, headers=headers, method=method.upper())
        self.log.debug("%s %s", method.upper(), url)
        attempts = 2 if retry_safe and method.upper() in {"GET", "HEAD"} else 1
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    data = json.loads(raw) if raw else None
                return self._unwrap(data)
            except HTTPError as exc:
                raw = exc.read()
                try: data = json.loads(raw) if raw else {}
                except ValueError: data = {"message": raw.decode("utf-8", "replace")}
                raise APIError.from_payload(data, status=exc.code, path=path) from None
            except (TimeoutError, URLError) as exc:
                if attempt + 1 == attempts:
                    raise APIError(str(exc), code="NETWORK_ERROR", path=path) from exc

    @staticmethod
    def _unwrap(data):
        if isinstance(data, dict) and "code" in data and "success" in data:
            if not data.get("success"):
                raise APIError.from_payload(data)
            return ApiResponse(data.get("data"), data.get("code"), data.get("message", ""), data)
        return ApiResponse(data, raw=data)


class Auth:
    def __init__(self, client): self._client = client
    @property
    def is_authenticated(self):
        expires = self._client.expires_at
        return bool(self._client._api.token) and (expires is None or time.time() < expires)
    def login(self, username: str, password: str, *, account_type: int,
              captcha_id: str | None = None, captcha_code: str | None = None):
        """OAuth2 password grant documented by Finger_desk (captcha optional)."""
        data = {"username": username, "password": password, "grant_type": "password", "type": account_type}
        if captcha_id is not None: data["captchaId"] = captcha_id
        if captcha_code is not None: data["captchaCode"] = captcha_code
        result = self._client._auth.request("POST", "/oauth2/token", body=data, form=True)
        token = result.data
        self._client.set_token(token["access_token"], token["token_type"], token.get("refresh_token"), token.get("expires_in"))
        return result
    def captcha(self): return self._client._auth.request("GET", "/api/v1/auth/captcha")
    def check(self): return self.is_authenticated
    def refresh(self):
        raise NotImplementedError("Finger_desk contains no refresh-token request contract; authenticate again when expired.")


class MarketData:
    def __init__(self, c): self.c = c
    def markets(self): return self.c._get("/api/mob/trade/profile-entity/getMarket")
    def symbols(self, market="stock", page=1):
        routes = {"crypto":"/api/mob/market/crypto/getCryptoIndexTicker/{}", "forex":"/api/mob/market/forex-base-info-entity/getForexIndexTicker/{}", "spot":"/api/mob/market/spot-base-info-entity/getSpotIndexTicker/{}", "stock":"/api/mob/market/stock/stock-us-base-info/getHotTicker", "indices":"/api/mob/market/indices-info-entity/getIndicesIndexTicker/{}"}
        if market not in routes: raise ValueError(f"Unsupported market: {market}")
        route = routes[market]
        return self.c._get(route.format(page) if "{}" in route else route)
    def history(self, *, market, ticker, interval, limit=200, page=1, start_time=None):
        if market not in {"crypto", "stock", "forex", "spot"}: raise ValueError("market must be crypto, stock, forex, or spot")
        p = {"market":market,"ticker":ticker,"interval":interval,"limit":limit,"page":page}
        if start_time is not None: p["startTime"] = int(start_time.timestamp()*1000) if hasattr(start_time,"timestamp") else int(start_time)
        return self.c._get("/api/mob/market/kline/getKline", params=p)
    get_history = history
    def quote(self, ticker: str):
        raise NotImplementedError("No HTTP snapshot endpoint is confirmed in Finger_desk. Use subscribe_quotes().")
    def subscribe_quotes(self, tickers, *, market="stock", on_message=None):
        return self.c.websocket().subscribe(tickers, market=market, on_message=on_message)


class Accounts:
    def __init__(self,c): self.c=c
    def list(self): return self.c._get("/api/mob/trade/order-entity/getTradeProfileResponse", params={"market":0})
    def detail(self, market): return self.c._get("/api/mob/trade/order-entity/getTradeProfileResponse", params={"market":market})
    def balance(self): return self.c._get("/api/mob/trade/wallet-entity/getWalletHomePage")


class Positions:
    def __init__(self,c): self.c=c
    def list(self, *, account_id=None, order_status=0, is_usd=False):
        # Account ID is not accepted by the observed endpoint; account context comes from auth.
        if account_id is not None: raise ValueError("Finger_desk endpoint has no account_id parameter; account is selected by the authenticated session.")
        return self.c._get("/api/mob/trade/order-entity/getHoldingListByIsUsd", params={"type":order_status,"isUsd":str(is_usd).lower()})


class Orders:
    def __init__(self,c): self.c=c
    def submit(self, *, is_buy, is_usd, limit_time, market, order_id, order_type,
               price, quantity, ticker, is_create, margin_ratio=None, stop_loss="0", take_profit="0"):
        if Decimal(str(quantity)) <= 0: raise ValueError("quantity must be positive")
        payload={"isBuy":is_buy,"isUsd":is_usd,"limitTime":limit_time,"market":market,"orderId":order_id,"orderType":order_type,"price":str(price),"quantity":quantity,"ticker":ticker,"isCreate":is_create,"marginRatio":margin_ratio,"stopLose":str(stop_loss),"takeProfit":str(take_profit)}
        return self.c._post("/api/mob/trade/order-entity/order", payload)
    def history(self, *, page=1, limit=20, filters=None): return self.c._get(f"/api/mob/trade/order-entity/getOrderHistory/{page}/{limit}", params=filters or {})
    def update_limit(self, *, order_id, price=None, quantity=None, stop_loss=None, take_profit=None):
        return self.c._post("/api/mob/trade/order-entity/updateLimitOrder", {"id":order_id,"price":price,"quantity":quantity,"stopLose":stop_loss,"takeProfit":take_profit})
    def cancel_limit(self, order_id): return self.c._post("/api/mob/trade/order-entity/cancelLimitOrder", params={"orderId":order_id})
    def set_take_profit_loss(self, *, order_id, stop_loss, take_profit): return self.c._post("/api/mob/trade/order-entity/setTakeProfitAndLoss", {"orderId":order_id,"stopLoss":str(stop_loss),"takeProfit":str(take_profit)})
    def executions(self): raise NotImplementedError("Finger_desk API provider has no confirmed executions endpoint.")


class FingerTraderClient:
    def __init__(self, *, token=None, token_type="Bearer", base_url=None, auth_url=None, socket_auth_url=None, timeout=10, environment="prod"):
        if environment not in {"prod","dev","local"}: raise ValueError("environment must be prod, dev, or local")
        local = "http://127.0.0.1:9999"
        self._api = _HTTP(base_url or (PROD_API if environment=="prod" else local+"/finger-bff-app"), timeout, token, token_type)
        self._auth = _HTTP(auth_url or (PROD_AUTH if environment=="prod" else local+"/finger-auth"), timeout, basic_auth=_CLIENT_ID)
        self._socket_auth_url = socket_auth_url or (PROD_SOCKET_AUTH if environment=="prod" else local+"/finger-bff-socket")
        self.auth, self.market_data, self.accounts, self.positions, self.orders = Auth(self), MarketData(self), Accounts(self), Positions(self), Orders(self)
    def set_token(self, access_token, token_type="Bearer", refresh_token=None, expires_in=None):
        self._api.token, self._api.token_type = access_token, token_type
        self.refresh_token, self.expires_at = refresh_token, (time.time()+expires_in if expires_in else None)
    def _get(self,path,params=None): return self._api.request("GET",path,params=params,authenticated=True,retry_safe=True)
    def _post(self,path,data=None,params=None): return self._api.request("POST",path,body=data,params=params,authenticated=True)
    def websocket(self):
        from .websocket import MarketWebSocket
        return MarketWebSocket(self._socket_auth_url, token=self._api.token, timeout=self._api.timeout)
