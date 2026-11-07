"""Small tolerant models for Finger Trader's envelope API."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    # Response payloads can contain private account information or credentials.
    data: Any = field(repr=False)
    code: Any = None
    message: str = ""
    raw: Any = field(default=None, repr=False)


@dataclass(frozen=True)
class AuthToken:
    """OAuth token response; repr deliberately excludes all credential values."""

    access_token: str = field(repr=False)
    token_type: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)
    expires_in: int | None = None


@dataclass(frozen=True)
class Instrument:
    ticker: str
    market: str | None = None
    name: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d):
        return cls(str(d.get("ticker", d.get("symbol", ""))), d.get("market"), d.get("name"), d)


@dataclass(frozen=True)
class Bar:
    timestamp: int | str | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d):
        def dec(*keys):
            v = next((d[k] for k in keys if d.get(k) is not None), None)
            return Decimal(str(v)) if v is not None else None

        return cls(
            d.get("timestamp", d.get("time", d.get("t"))),
            dec("open", "o"),
            dec("high", "h"),
            dec("low", "l"),
            dec("close", "c"),
            dec("volume", "v"),
            d,
        )


@dataclass(frozen=True)
class Quote:
    ticker: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, d):
        return cls(str(d.get("ticker", d.get("symbol", ""))), d)


@dataclass(frozen=True)
class Market:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Account:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Balance:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Position:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Order:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Execution:
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class TradingRule:
    raw: dict[str, Any] = field(repr=False)
