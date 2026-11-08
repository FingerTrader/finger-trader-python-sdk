"""Dependency-free P0 contract validator and arithmetic acceptance oracle.

This is not the runtime, broker, or backtest engine. Production implementations
must consume the same fixtures; passing this checker alone is not P1/P3 proof.
The schema interpreter deliberately rejects unknown keywords rather than
silently pretending to implement the whole JSON Schema specification.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
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
                or (number.is_zero() and abs(number.as_tuple().exponent) > 6144)
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


def align(value, step, rounding):
    if step <= 0:
        raise ContractError("step must be positive")
    # Rounding to a step is an exact rational operation. Dividing Decimals
    # first at 34 digits can turn a value just below the boundary into a tie.
    ratio = Fraction(value) / Fraction(step)
    floor = ratio.numerator // ratio.denominator
    if rounding == ROUND_FLOOR:
        units = floor
    elif rounding == ROUND_CEILING:
        units = -((-ratio.numerator) // ratio.denominator)
    elif rounding == ROUND_HALF_UP:
        sign = -1 if ratio < 0 else 1
        n, d = abs(ratio.numerator), ratio.denominator
        q, r = divmod(n, d)
        units = sign * (q + (2 * r >= d))
    else:
        raise ContractError("unsupported alignment rounding")
    # Preserve the selected step exactly, independently of caller context.
    with localcontext() as ctx:
        ctx.prec = max(34, len(str(abs(units))) + len(step.as_tuple().digits) + 2)
        return Decimal(units) * step


def golden_result(case):
    """Small independent equations for human-reviewed examples, not a matcher."""
    with localcontext() as ctx:
        ctx.prec = 34
        ctx.Emax = 6144
        ctx.Emin = -6143
        ctx.rounding = ROUND_HALF_EVEN

        def d(key):
            return Decimal(case[key])

        kind = case["kind"]
        if kind in {"reservation", "fill"}:
            gross = d("price") * d("quantity")
            fee = align(
                max(gross * d("fee_rate"), d("minimum_fee")), d("money_step"), ROUND_HALF_UP
            )
            if kind == "reservation":
                reserved = align(gross + fee, d("money_step"), ROUND_CEILING)
                second_gross = d("price") * d("second_quantity")
                second_fee = align(
                    max(second_gross * d("fee_rate"), d("minimum_fee")),
                    d("money_step"),
                    ROUND_HALF_UP,
                )
                second = align(second_gross + second_fee, d("money_step"), ROUND_CEILING)
                return {
                    "reservation": reserved,
                    "second_accepted": d("cash") - d("existing_reserved") - reserved >= second,
                }
            debit = align(gross + fee, d("money_step"), ROUND_HALF_UP)
            accepted = debit <= d("cash") - d("other_reserved")
            cash = d("cash") - debit if accepted else d("cash")
            return {
                "accepted": accepted,
                "cash": cash,
                "reserved_cash": d("other_reserved"),
                "available_cash": cash - d("other_reserved"),
                "position_cost": debit if accepted else Decimal(0),
            }
        if kind == "release":
            available = d("cash") - d("reserved") + d("release")
            return {"available_cash": available, "accepted": available >= d("new_reservation")}
        if kind == "oco":
            if d("open") <= d("stop"):
                return {"winner": "stop", "price": d("open")}
            if d("open") >= d("take"):
                return {"winner": "take", "price": d("open")}
            if d("low") <= d("stop"):
                return {"winner": "stop", "price": d("stop")}
            if d("high") >= d("take"):
                return {"winner": "take", "price": d("take")}
            return {"winner": None, "price": None}
        if kind == "protection":
            stop = (
                align(d("fill_price") * (1 - d("stop_percent") / 100), d("price_step"), ROUND_FLOOR)
                if d("stop_percent")
                else None
            )
            take = (
                align(
                    d("fill_price") * (1 + d("take_percent") / 100), d("price_step"), ROUND_CEILING
                )
                if d("take_percent")
                else None
            )
            valid = (stop is None or 0 < stop < d("fill_price")) and (
                take is None or take > d("fill_price")
            )
            return {"stop": stop, "take": take, "valid": valid}
        if kind == "slippage":
            buy = case["side"] == "buy"
            price = d("price") * (1 + d("bps") / 10000 if buy else 1 - d("bps") / 10000)
            return {"price": align(price, d("price_step"), ROUND_CEILING if buy else ROUND_FLOOR)}
        if kind == "cost":
            quantity = sum(Decimal(row["quantity"]) for row in case["buys"])
            cost = sum(Decimal(row["gross"]) + Decimal(row["fee"]) for row in case["buys"])
            allocated = (
                cost if d("sell_quantity") == quantity else cost * d("sell_quantity") / quantity
            )
            return {
                "initial_cost": cost,
                "allocated_cost": allocated,
                "remaining_cost": cost - allocated,
                "realized_pnl": d("sell_gross") - d("sell_fee") - allocated,
            }
        if kind == "protected_exit":
            return {
                "protected": d("quantity") - d("exit_quantity"),
                "exit_reserved": d("exit_quantity"),
                "total_reserved": d("quantity"),
            }
        raise ContractError(f"unknown golden kind {kind}")


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


def validate_trace(events, policy):
    """Contract sequence oracle; no worker, threads, clock, or orders are run."""
    active = None
    last_request = 0
    pending = set()
    stopping = False
    for event in events:
        kind = event["type"]
        if kind == "begin":
            if active is not None:
                raise ContractError("callback reentry")
            active = event
            if event["phase"] not in policy["phases"] or (stopping and event["phase"] != "stop"):
                raise ContractError("invalid callback after stopping")
            last_request = 0
        elif kind == "stop":
            stopping = True
        elif kind == "request":
            if active is None or event["callback_id"] != active["callback_id"]:
                raise ContractError("stale callback")
            if (
                type(event["seq"]) is not int
                or type(event["write"]) is not bool
                or event["seq"] != last_request + 1
            ):
                raise ContractError("request sequence gap or duplicate")
            if event["write"] and (stopping or not policy["phases"][active["phase"]]["trade"]):
                raise ContractError("write denied")
            last_request = event["seq"]
            pending.add(last_request)
        elif kind == "response":
            if (
                active is None
                or event.get("callback_id") != active["callback_id"]
                or event["seq"] not in pending
            ):
                raise ContractError("unknown response")
            pending.remove(event["seq"])
        elif kind == "complete":
            if (
                active is None
                or pending
                or event["callback_id"] != active["callback_id"]
                or event["last_seq"] != last_request
            ):
                raise ContractError("callback barrier not settled")
            active = None
        elif kind == "advance":
            if active is not None or pending or stopping:
                raise ContractError("cannot advance")
        else:
            raise ContractError("unknown trace event")
    if active is not None or pending:
        raise ContractError("incomplete trace")


def transaction(payload):
    return (
        canonical({"payload": payload, "sha256": hashlib.sha256(canonical(payload)).hexdigest()})
        + b"\n"
    )


def recover(data):
    """P0 reference framing: does not perform I/O, mutate accounts, or fsync."""
    committed = []
    previous = "0" * 64
    next_event = 1
    for line in data.splitlines(keepends=True):
        if not line.endswith(b"\n"):
            break
        try:
            wrapper = parse_json(line)
            payload = wrapper["payload"]
            digest = hashlib.sha256(canonical(payload)).hexdigest()
            if canonical(wrapper) + b"\n" != line or set(wrapper) != {"payload", "sha256"}:
                raise ContractError("noncanonical transaction")
            if digest != wrapper["sha256"] or payload["previous_sha256"] != previous:
                raise ContractError("broken transaction digest chain")
            if (
                type(payload["batch_seq"]) is not int
                or type(payload["first_event_seq"]) is not int
                or type(payload["last_event_seq"]) is not int
            ):
                raise ContractError("transaction sequences must be integers")
            if not isinstance(payload["batch_id"], str) or not payload["batch_id"]:
                raise ContractError("invalid batch ID")
            if any(old["batch_id"] == payload["batch_id"] for old in committed):
                raise ContractError("duplicate batch ID")
            if not isinstance(payload["events"], list):
                raise ContractError("events must be an array")
            if (
                payload["batch_seq"] != len(committed) + 1
                or payload["first_event_seq"] != next_event
            ):
                raise ContractError("non-contiguous transaction")
            if (
                not payload["events"]
                or payload["last_event_seq"] != next_event + len(payload["events"]) - 1
            ):
                raise ContractError("invalid transaction event range")
            committed.append(payload)
            previous = digest
            next_event = payload["last_event_seq"] + 1
        except (ValueError, KeyError, TypeError) as exc:
            raise ContractError(f"corrupt committed record: {exc}") from exc
    return committed
