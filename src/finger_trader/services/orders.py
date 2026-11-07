"""Order endpoints; state-changing requests are never retried."""

from decimal import Decimal, InvalidOperation
from typing import NoReturn

from ..exceptions import APIError, NetworkError, UnknownOutcomeError
from ..models import ApiResponse


def _positive(value, name):
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be a finite positive number") from None
    if not decimal.is_finite() or decimal <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return decimal


def _finite_decimal(value, name):
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be a finite decimal") from None
    if not decimal.is_finite():
        raise ValueError(f"{name} must be a finite decimal")
    return decimal


def _raise_unknown(error) -> NoReturn:
    if isinstance(error, NetworkError) or (
        isinstance(error, APIError)
        and (error.status is None or 300 <= error.status < 400 or error.status >= 500)
    ):
        raise UnknownOutcomeError(path=error.path) from None
    raise error


def _validate_order_id(order_id):
    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError("order_id must not be empty")


class Orders:
    def __init__(self, client):
        self._client = client

    def submit(
        self,
        *,
        is_buy: bool,
        is_usd: bool,
        limit_time: int,
        market: int,
        order_id: str,
        order_type: int,
        price,
        quantity: int,
        ticker: str,
        is_create: int,
        margin_ratio: int | None = None,
        stop_loss="0",
        take_profit="0",
    ) -> ApiResponse:
        _validate_order_id(order_id)
        qty = _positive(quantity, "quantity")
        if isinstance(quantity, bool):
            raise ValueError("quantity must be a positive integer")
        if qty != qty.to_integral_value():
            raise ValueError("quantity must be an integer for the confirmed Finger_desk order DTO")
        px = _finite_decimal(price, "price")
        if not px.is_finite() or px < 0:
            raise ValueError("price must be finite and non-negative")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("ticker must not be empty")
        if not isinstance(is_buy, bool) or not isinstance(is_usd, bool):
            raise TypeError("is_buy and is_usd must be booleans")
        if (
            isinstance(limit_time, bool)
            or isinstance(market, bool)
            or isinstance(order_type, bool)
            or isinstance(is_create, bool)
            or not isinstance(limit_time, int)
            or not isinstance(market, int)
            or not isinstance(order_type, int)
            or not isinstance(is_create, int)
        ):
            raise TypeError(
                "limit_time, market, order_type, and is_create must be backend integer enum values"
            )
        stop = _finite_decimal(stop_loss, "stop_loss")
        take = _finite_decimal(take_profit, "take_profit")
        payload = {
            "isBuy": is_buy,
            "isUsd": is_usd,
            "limitTime": limit_time,
            "market": market,
            "orderId": order_id,
            "orderType": order_type,
            "price": str(px),
            "quantity": int(qty),
            "ticker": ticker,
            "isCreate": is_create,
            "marginRatio": margin_ratio,
            "stopLose": str(stop),
            "takeProfit": str(take),
        }
        try:
            return self._client._post("/api/mob/trade/order-entity/order", payload)
        except APIError as exc:
            _raise_unknown(exc)

    def history(self, *, page: int = 1, limit: int = 20, filters=None) -> ApiResponse:
        if page < 1 or limit < 1:
            raise ValueError("page and limit must be positive")
        return self._client._get(
            f"/api/mob/trade/order-entity/getOrderHistory/{page}/{limit}",
            params=filters or {},
        )

    def update_limit(
        self, *, order_id: str, price=None, quantity=None, stop_loss=None, take_profit=None
    ) -> ApiResponse:
        _validate_order_id(order_id)
        if price is not None:
            price = str(_positive(price, "price"))
        if quantity is not None:
            qty = _positive(quantity, "quantity")
            if isinstance(quantity, bool) or qty != qty.to_integral_value():
                raise ValueError(
                    "quantity must be an integer for the confirmed Finger_desk order DTO"
                )
            quantity = int(qty)
        try:
            return self._client._post(
                "/api/mob/trade/order-entity/updateLimitOrder",
                {
                    "id": order_id,
                    "price": price,
                    "quantity": quantity,
                    "stopLose": stop_loss,
                    "takeProfit": take_profit,
                },
            )
        except APIError as exc:
            _raise_unknown(exc)

    def cancel_limit(self, order_id: str) -> ApiResponse:
        _validate_order_id(order_id)
        try:
            return self._client._post(
                "/api/mob/trade/order-entity/cancelLimitOrder",
                params={"orderId": order_id},
            )
        except APIError as exc:
            _raise_unknown(exc)

    def set_take_profit_loss(self, *, order_id: str, stop_loss, take_profit) -> ApiResponse:
        _validate_order_id(order_id)
        stop = _finite_decimal(stop_loss, "stop_loss")
        take = _finite_decimal(take_profit, "take_profit")
        try:
            return self._client._post(
                "/api/mob/trade/order-entity/setTakeProfitAndLoss",
                {"orderId": order_id, "stopLoss": str(stop), "takeProfit": str(take)},
            )
        except APIError as exc:
            _raise_unknown(exc)

    def executions(self):
        raise NotImplementedError("Finger_desk API provider has no confirmed executions endpoint.")
