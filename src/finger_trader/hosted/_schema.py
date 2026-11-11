"""Frozen P0 wire validator; checked against the shared contract fixtures."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from decimal import (
    ROUND_HALF_EVEN,
    Decimal,
    localcontext,
)
from fractions import Fraction
from pathlib import Path


class ContractError(ValueError):
    pass


MAX_INTEGER = 9007199254740991


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid(value):
        raise ContractError(f"non-finite JSON token: {value}")

    def integer(text):
        if len(text.lstrip("-")) > 16:
            raise ContractError("JSON integer exceeds interoperable range")
        value = int(text)
        if abs(value) > MAX_INTEGER:
            raise ContractError("JSON integer exceeds interoperable range")
        return value

    def floating(text):
        value = float(text)
        if not math.isfinite(value):
            invalid(text)
        return value

    try:
        return json.loads(
            text,
            object_pairs_hook=unique,
            parse_constant=invalid,
            parse_int=integer,
            parse_float=floating,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContractError(str(exc)) from exc


def load_json(path: Path):
    return parse_json(path.read_text(encoding="utf-8"))


class Schema:
    KEYWORDS = {
        "$ref",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "pattern",
        "minLength",
        "minimum",
        "maximum",
        "const",
        "enum",
    }

    def __init__(self, document):
        self.document = document

    def check(self, definition, value):
        try:
            with localcontext() as context:
                context.prec = 34
                context.Emax = 6144
                context.Emin = -6143
                context.rounding = ROUND_HALF_EVEN
                self._check(self.document["$defs"][definition], value, definition)
                self._semantic(definition, value)
        except (KeyError, TypeError, ArithmeticError) as exc:
            raise ContractError(str(exc)) from exc

    def _check(self, schema, value, path):
        unknown = set(schema) - self.KEYWORDS
        if unknown:
            raise ContractError(f"unsupported schema keywords: {sorted(unknown)}")
        if "$ref" in schema:
            name = schema["$ref"].removeprefix("#/$defs/")
            self._check(self.document["$defs"][name], value, path)
            self._semantic(name, value)
            return
        if "const" in schema and (
            type(value) is not type(schema["const"]) or value != schema["const"]
        ):
            raise ContractError(f"{path}: const mismatch")
        if "enum" in schema and not any(
            type(value) is type(item) and value == item for item in schema["enum"]
        ):
            raise ContractError(f"{path}: enum mismatch")
        kind = schema.get("type")
        types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
        if kind and (kind not in types or type(value) is not types[kind]):
            raise ContractError(f"{path}: expected {kind}")
        if kind == "object":
            props = schema.get("properties", {})
            if set(schema.get("required", [])) - set(value):
                raise ContractError(f"{path}: missing fields")
            if schema.get("additionalProperties") is False and set(value) - set(props):
                raise ContractError(f"{path}: unknown fields")
            for key, item in value.items():
                if key in props:
                    self._check(props[key], item, f"{path}.{key}")
        elif kind == "array":
            for index, item in enumerate(value):
                self._check(schema["items"], item, f"{path}[{index}]")
        elif kind == "string":
            if len(value) < schema.get("minLength", 0):
                raise ContractError(f"{path}: empty string")
            if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
                raise ContractError(f"{path}: invalid string")
            if schema.get("pattern") in {
                r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$",
                r"^(0|[1-9][0-9]*)(\.[0-9]+)?$",
            }:
                self._semantic("Decimal", value)
        elif kind == "integer":
            if value < schema.get("minimum", -MAX_INTEGER):
                raise ContractError(f"{path}: below minimum")
            if value > schema.get("maximum", MAX_INTEGER):
                raise ContractError(f"{path}: above maximum")

    def _semantic(self, name, value):
        if name in {"Decimal", "NonNegativeDecimal"}:
            number = Decimal(value)
            if (
                len(number.as_tuple().digits) > 34
                or abs(number.adjusted()) > 6144
                or (number.is_zero() and abs(int(number.as_tuple().exponent)) > 6144)
            ):
                raise ContractError("decimal exceeds decimal128 domain")
        elif name == "Order":
            if Decimal(value["quantity"]) <= 0:
                raise ContractError("quantity must be positive")
            if (value["kind"] == "limit") != ("limit_price" in value):
                raise ContractError("limit_price must occur exactly for limit orders")
            if "limit_price" in value and Decimal(value["limit_price"]) <= 0:
                raise ContractError("price must be positive")
            if "protection" in value and value["side"] != "buy":
                raise ContractError("only entry buys may attach protection")
        elif name == "Protection":
            if not 0 <= Decimal(value["stop_loss_percent"]) < 100:
                raise ContractError("stop loss must be in [0, 100)")
        elif name == "Timestamp":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.year < 1:
                    raise ValueError("year must be positive")
            except ValueError as exc:
                raise ContractError("invalid calendar timestamp") from exc
        elif name == "Bar":
            prices = [Decimal(value[key]) for key in ("open", "high", "low", "close")]
            if min(prices) <= 0 or prices[1] < max(prices) or prices[2] > min(prices):
                raise ContractError("invalid positive OHLC range")
            if datetime.fromisoformat(
                value["open_time"].replace("Z", "+00:00")
            ) >= datetime.fromisoformat(value["close_time"].replace("Z", "+00:00")):
                raise ContractError("bar interval must increase")
        elif name == "Account":
            if Fraction(value["cash"]) - Fraction(value["reserved_cash"]) != Fraction(
                value["available_cash"]
            ):
                raise ContractError("cash reservation invariant failed")
            if Decimal(value["cash"]) < 0 or Decimal(value["available_cash"]) < 0:
                raise ContractError("cash account cannot borrow")
        elif name == "Position":
            if Fraction(value["available_quantity"]) + Fraction(
                value["reserved_quantity"]
            ) != Fraction(value["quantity"]):
                raise ContractError("position reservation invariant failed")
        elif name == "Strategy":
            path = value["entrypoint"]["file"]
            if any(part in {"", ".", ".."} for part in path.split("/")):
                raise ContractError("entrypoint must be normalized relative path")
            if len(value["requested_capabilities"]) != len(set(value["requested_capabilities"])):
                raise ContractError("duplicate capabilities")
            canonical(value["parameters"])
        elif name == "Instrument":
            for field in ("price_step", "quantity_step", "money_step"):
                if Decimal(value[field]) <= 0:
                    raise ContractError("product steps must be positive")
        elif name == "Dataset":
            if datetime.fromisoformat(
                value["first_open"].replace("Z", "+00:00")
            ) >= datetime.fromisoformat(value["last_close"].replace("Z", "+00:00")):
                raise ContractError("dataset interval must increase")
        elif name == "ProtectionGroup":
            if Decimal(value["quantity"]) <= 0 or not any(
                key in value for key in ("stop_price", "take_price")
            ):
                raise ContractError("protection needs quantity and at least one trigger")
            if any(
                Decimal(value[key]) <= 0 for key in ("stop_price", "take_price") if key in value
            ):
                raise ContractError("protection prices must be positive")
        elif name == "RunEvent":
            self.check(self.document["event_payloads"][value["kind"]], value["payload"])
        elif name == "OrderState":
            if Decimal(value["quantity"]) <= 0 or Decimal(value["filled_quantity"]) > Decimal(
                value["quantity"]
            ):
                raise ContractError("invalid order quantity")
            if (value["kind"] == "limit") != ("limit_price" in value):
                raise ContractError("order state limit price mismatch")
            if value["status"] == "filled" and (
                value["quantity"] != value["filled_quantity"] or "fill_price" not in value
            ):
                if (
                    Decimal(value["quantity"]) != Decimal(value["filled_quantity"])
                    or "fill_price" not in value
                ):
                    raise ContractError("filled order requires full quantity and price")
        elif name == "ExitProtected":
            if Decimal(value["params"]["payload"]["quantity"]) <= 0:
                raise ContractError("exit quantity must be positive")


def canonical(payload):
    def no_float(value):
        if isinstance(value, float):
            raise ContractError("float not allowed in persistent transaction")
        if type(value) is int and abs(value) > MAX_INTEGER:
            raise ContractError("integer exceeds interoperable range")
        if isinstance(value, dict):
            for item in value.values():
                no_float(item)
        elif isinstance(value, list):
            for item in value:
                no_float(item)

    no_float(payload)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
