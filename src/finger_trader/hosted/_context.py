"""Worker-only binding, strict scalar conversion and synchronous services."""

from __future__ import annotations

import dataclasses
import json
import threading
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, get_type_hints

import finger_trader.hosted as public_module

from . import (
    Account,
    Acknowledgement,
    Bar,
    Context,
    ExitResult,
    HostedError,
    Instrument,
    InvalidArgumentError,
    LogLevel,
    OrderKind,
    OrderSnapshot,
    OrderSubmission,
    ParameterValue,
    PermissionDeniedError,
    Phase,
    Position,
    Protection,
    ProtocolMismatchError,
    Side,
    StaleCallbackError,
)
from ._schema import ContractError, Schema

public = vars(public_module)

DATA = Path(__file__).parent
SCHEMA = Schema(json.loads((DATA / "schema.json").read_text()))
API = json.loads((DATA / "python-api.json").read_text())
POLICY = json.loads((DATA / "policy.json").read_text())


def freeze_parameters(value: Any) -> Any:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int and abs(value) <= 9007199254740991:
        return value
    if isinstance(value, (tuple, list)):
        return tuple(freeze_parameters(item) for item in value)
    if isinstance(value, Mapping) and all(type(key) is str for key in value):
        return MappingProxyType({key: freeze_parameters(item) for key, item in value.items()})
    raise InvalidArgumentError("Parameters must contain immutable JSON values; floats forbidden")


def wire(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise InvalidArgumentError("Decimal must be finite")
        if (
            len(value.as_tuple().digits) > 34
            or abs(value.adjusted()) > 6144
            or (value.is_zero() and abs(int(value.as_tuple().exponent)) > 6144)
        ):
            raise InvalidArgumentError("Decimal exceeds decimal128 domain")
        result = format(value, "f")
        try:
            SCHEMA.check("Decimal", result)
        except ContractError as error:
            raise InvalidArgumentError(str(error)) from error
        return result
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise InvalidArgumentError("Datetime must have UTC timezone")
        result = value.isoformat(timespec="microseconds").replace("+00:00", "Z")
        SCHEMA.check("Timestamp", result)
        return result
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: wire(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if getattr(value, field.name) is not None
        }
    if isinstance(value, Mapping):
        return {key: wire(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [wire(item) for item in value]
    if value is None or type(value) in (str, bool, int):
        return value
    raise InvalidArgumentError("Unsupported public value type")


def model(name: str, payload: Any) -> Any:
    definition = API["models"][name]
    if name == "OrderSubmission":
        definition = "context_submit_order_response"
        SCHEMA.check(definition, {"jsonrpc": "2.0", "id": "decode", "result": payload})
    else:
        SCHEMA.check(definition, payload)
    cls = public[name]
    hints = get_type_hints(cls)
    values = {}
    for key, value in payload.items():
        annotation = hints[key]
        if annotation is Decimal or Decimal in getattr(annotation, "__args__", ()):
            value = Decimal(value)
        elif annotation is datetime:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        values[key] = value
    return cls(**values)


def rpc_error(payload: dict[str, Any]) -> HostedError:
    rpc_code = payload.get("code")
    data = payload.get("data", {})
    name = API["errors"].get(data.get("code")) if rpc_code == -32000 else None
    name = name or API["jsonrpc_errors"].get(str(rpc_code), "ProtocolMismatchError")
    return public[name](str(payload.get("message", "Remote error")), rpc_code)


class BoundContext(Context):
    """Constructed only by the worker; Host independently checks every token."""

    def __init__(self, config: dict[str, Any], transport: Callable[..., Any]) -> None:
        self._config = config
        self._transport = transport
        self._parameters = freeze_parameters(config["parameters"])
        self._instrument = model("Instrument", config["instrument"])
        self._callback: dict[str, Any] | None = None
        self._owner: int | None = None
        self._seq = 0

    @property
    def run_id(self) -> str:
        return self._config["record"]["run_id"]

    @property
    def mode(self) -> Literal["backtest"]:
        return "backtest"

    @property
    def parameters(self) -> Mapping[str, ParameterValue]:
        return self._parameters

    @property
    def instrument(self) -> Instrument:
        return self._instrument

    def _active(self) -> dict[str, Any]:
        if self._callback is None:
            raise StaleCallbackError("No active callback")
        if self._owner != threading.get_ident():
            raise PermissionDeniedError("Only the callback owner thread can call context")
        return self._callback

    @property
    def phase(self) -> Phase:
        return self._active()["phase"]

    @property
    def now(self) -> datetime:
        return datetime.fromisoformat(self._active()["time"].replace("Z", "+00:00"))

    @property
    def is_warmup(self) -> bool:
        return self.phase == "warmup"

    def _call(self, name: str, payload: dict[str, Any]) -> Any:
        callback = self._active()
        spec = API["methods"][name]
        permission = spec["permission"]
        capability = spec["capability"]
        if not POLICY["phases"][self.phase][permission] or (
            capability != "basic.log" and capability not in self._config["granted_capabilities"]
        ):
            raise PermissionDeniedError("Phase or granted capability denies this request")
        sequence = self._seq + 1
        request = {
            "jsonrpc": "2.0",
            "id": f"w:{callback['id']}:{sequence}",
            "method": spec["ipc"],
            "params": {
                "run_id": self.run_id,
                "callback_id": callback["id"],
                "request_seq": sequence,
                "payload": wire(payload),
            },
        }
        definition = json.loads((DATA / "methods.json").read_text())["requests"][spec["ipc"]]
        try:
            SCHEMA.check(definition, request)
        except ContractError as error:
            raise InvalidArgumentError(str(error)) from error
        self._seq = sequence
        response = self._transport(request)
        if "error" in response:
            SCHEMA.check("Error", response)
            raise rpc_error(response["error"])
        try:
            SCHEMA.check(spec["ipc"].replace(".", "_") + "_response", response)
        except ContractError as error:
            raise ProtocolMismatchError(str(error)) from error
        return response["result"]

    def history(
        self,
        *,
        instrument_id: str | None = None,
        timeframe: str | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> tuple[Bar, ...]:
        instrument_id = self.instrument.instrument_id if instrument_id is None else instrument_id
        timeframe = self._config["timeframe"] if timeframe is None else timeframe
        end_time = self.now if end_time is None else end_time
        if not isinstance(end_time, datetime):
            raise InvalidArgumentError("History time must be a UTC datetime")
        wire(end_time)
        if (
            instrument_id != self.instrument.instrument_id
            or timeframe != self._config["timeframe"]
            or not isinstance(end_time, datetime)
            or end_time > self.now
        ):
            raise InvalidArgumentError("History must stay inside the bound product and clock")
        result = self._call(
            "history",
            {
                "instrument_id": instrument_id,
                "timeframe": timeframe,
                "end_time": end_time,
                "limit": limit,
            },
        )
        return tuple(model("Bar", item) for item in result)

    def account(self) -> Account:
        return model("Account", self._call("account", {}))

    def position(self) -> Position:
        return model(
            "Position", self._call("position", {"instrument_id": self.instrument.instrument_id})
        )

    def submit_order(
        self,
        *,
        client_order_id: str,
        side: Side,
        quantity: Decimal,
        kind: OrderKind = "market",
        limit_price: Decimal | None = None,
        protection: Protection | None = None,
    ) -> OrderSubmission:
        if not isinstance(quantity, Decimal) or (
            limit_price is not None and not isinstance(limit_price, Decimal)
        ):
            raise InvalidArgumentError("Order numbers must be Decimal")
        payload: dict[str, Any] = {
            "client_order_id": client_order_id,
            "side": side,
            "quantity": quantity,
            "kind": kind,
        }
        if limit_price is not None:
            payload["limit_price"] = limit_price
        if protection is not None:
            if not isinstance(protection, Protection) or any(
                not isinstance(getattr(protection, field), Decimal)
                for field in ("stop_loss_percent", "take_profit_percent")
            ):
                raise InvalidArgumentError("Protection percentages must be Decimal")
            payload["protection"] = protection
        return model("OrderSubmission", self._call("submit_order", payload))

    def cancel_order(self, order_id: str) -> OrderSnapshot:
        return model("OrderSnapshot", self._call("cancel_order", {"order_id": order_id}))

    def get_order(self, order_id: str) -> OrderSnapshot:
        return model("OrderSnapshot", self._call("get_order", {"order_id": order_id}))

    def exit_protected(self, group_id: str, quantity: Decimal) -> ExitResult:
        if not isinstance(quantity, Decimal):
            raise InvalidArgumentError("Quantity must be Decimal")
        return model(
            "ExitResult", self._call("exit_protected", {"group_id": group_id, "quantity": quantity})
        )

    def log(self, message: str, *, level: LogLevel = "INFO") -> Acknowledgement:
        return model("Acknowledgement", self._call("log", {"message": message, "level": level}))

    def plot(
        self, series_id: str, value: Decimal, *, timestamp: datetime | None = None
    ) -> Acknowledgement:
        if not isinstance(value, Decimal):
            raise InvalidArgumentError("Plot value must be Decimal")
        return model(
            "Acknowledgement",
            self._call(
                "plot",
                {
                    "series_id": series_id,
                    "value": value,
                    "timestamp": self.now if timestamp is None else timestamp,
                },
            ),
        )

    def marker(
        self, marker_id: str, *, label: str, price: Decimal, timestamp: datetime | None = None
    ) -> Acknowledgement:
        if not isinstance(price, Decimal):
            raise InvalidArgumentError("Marker price must be Decimal")
        return model(
            "Acknowledgement",
            self._call(
                "marker",
                {
                    "marker_id": marker_id,
                    "label": label,
                    "price": price,
                    "timestamp": self.now if timestamp is None else timestamp,
                },
            ),
        )
