"""Public API for client-hosted strategies. No HTTP or trading fallback."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol, TypeAlias

ParameterValue: TypeAlias = (
    str | int | bool | None | tuple["ParameterValue", ...] | Mapping[str, "ParameterValue"]
)
Side: TypeAlias = Literal["buy", "sell"]
OrderKind: TypeAlias = Literal["market", "limit"]
Phase: TypeAlias = Literal["start", "warmup", "bar", "stop"]
LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Bar:
    instrument_id: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_closed: Literal[True]
    is_warmup: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class Instrument:
    instrument_id: str
    quote_currency: str
    price_step: Decimal
    quantity_step: Decimal
    minimum_quantity: Decimal
    minimum_notional: Decimal
    money_step: Decimal
    timezone: str
    calendar_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Account:
    cash: Decimal
    reserved_cash: Decimal
    available_cash: Decimal
    position_quantity: Decimal
    position_cost: Decimal
    realized_pnl: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class Position:
    instrument_id: str
    quantity: Decimal
    available_quantity: Decimal
    reserved_quantity: Decimal
    cost: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class Protection:
    stop_loss_percent: Decimal = Decimal("0")
    take_profit_percent: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderSnapshot:
    order_id: str
    client_order_id: str
    side: Side
    kind: OrderKind
    quantity: Decimal
    status: Literal["accepted", "filled", "cancelled", "rejected", "ended"]
    reason: str
    run_id: str
    filled_quantity: Decimal
    fee: Decimal
    reserved_cash: Decimal
    reserved_quantity: Decimal
    limit_price: Decimal | None = None
    fill_price: Decimal | None = None
    group_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ProtectionGroup:
    group_id: str
    entry_order_id: str
    quantity: Decimal
    active_from_event_seq: int
    stop_price: Decimal | None = None
    take_price: Decimal | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderSubmission:
    order_id: str
    status: Literal["accepted", "rejected"]
    code: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ExitResult:
    order_id: str
    group_id: str
    remaining_quantity: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class Acknowledgement:
    accepted: bool


class HostedError(Exception):
    code = "PROTOCOL_MISMATCH"

    def __init__(self, message: str, rpc_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.rpc_code = rpc_code


class InvalidArgumentError(HostedError):
    code = "INVALID_ARGUMENT"


class InsufficientCashError(HostedError):
    code = "INSUFFICIENT_CASH"


class InsufficientPositionError(HostedError):
    code = "INSUFFICIENT_POSITION"


class PermissionDeniedError(HostedError):
    code = "PERMISSION_DENIED"


class StaleCallbackError(HostedError):
    code = "STALE_CALLBACK"


class ProtocolMismatchError(HostedError):
    code = "PROTOCOL_MISMATCH"


class ProtectionInvalidError(HostedError):
    code = "PROTECTION_INVALID"


class StoppingError(HostedError):
    code = "STOPPING"


class HostedIOError(HostedError):
    code = "IO_FAILURE"


class UnsupportedCapabilityError(HostedError):
    code = "UNSUPPORTED_CAPABILITY"


class Context(Protocol):
    @property
    def run_id(self) -> str: ...
    @property
    def mode(self) -> Literal["backtest"]: ...
    @property
    def now(self) -> datetime: ...
    @property
    def phase(self) -> Phase: ...
    @property
    def is_warmup(self) -> bool: ...
    @property
    def instrument(self) -> Instrument: ...
    @property
    def parameters(self) -> Mapping[str, ParameterValue]: ...
    def history(
        self,
        *,
        instrument_id: str | None = None,
        timeframe: str | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> tuple[Bar, ...]: ...
    def account(self) -> Account: ...
    def position(self) -> Position: ...
    def submit_order(
        self,
        *,
        client_order_id: str,
        side: Side,
        quantity: Decimal,
        kind: OrderKind = "market",
        limit_price: Decimal | None = None,
        protection: Protection | None = None,
    ) -> OrderSubmission: ...
    def cancel_order(self, order_id: str) -> OrderSnapshot: ...
    def get_order(self, order_id: str) -> OrderSnapshot: ...
    def exit_protected(self, group_id: str, quantity: Decimal) -> ExitResult: ...
    def log(self, message: str, *, level: LogLevel = "INFO") -> Acknowledgement: ...
    def plot(
        self, series_id: str, value: Decimal, *, timestamp: datetime | None = None
    ) -> Acknowledgement: ...
    def marker(
        self, marker_id: str, *, label: str, price: Decimal, timestamp: datetime | None = None
    ) -> Acknowledgement: ...


class Strategy:
    def __init__(self, **parameters: ParameterValue) -> None:
        from ._context import freeze_parameters

        self._parameters = freeze_parameters(parameters)
        self._context: Context | None = None

    @property
    def parameters(self) -> Mapping[str, ParameterValue]:
        return self._parameters

    @property
    def context(self) -> Context:
        if self._context is None:
            raise StaleCallbackError("Strategy is not bound to a hosted run")
        return self._context

    def on_start(self, context: Context) -> None:
        pass

    def on_bar(self, bar: Bar) -> None:
        pass

    def on_stop(self) -> None:
        pass


__all__ = [
    "Bar",
    "Instrument",
    "Account",
    "Position",
    "Protection",
    "ProtectionGroup",
    "ExitResult",
    "OrderSnapshot",
    "Acknowledgement",
    "OrderSubmission",
    "Strategy",
    "Context",
    "HostedError",
    "InvalidArgumentError",
    "InsufficientCashError",
    "InsufficientPositionError",
    "PermissionDeniedError",
    "StaleCallbackError",
    "ProtocolMismatchError",
    "ProtectionInvalidError",
    "StoppingError",
    "HostedIOError",
    "UnsupportedCapabilityError",
    "ParameterValue",
    "Side",
    "OrderKind",
    "Phase",
    "LogLevel",
]
