"""Strategy intent signals. These are not orders, executions, or fills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Signal:
    symbol: str
    timestamp: datetime
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("signal symbol must not be empty")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("signal timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class BuySignal(Signal):
    """Strategy intent to enter a long position."""


@dataclass(frozen=True, slots=True)
class SellSignal(Signal):
    """Strategy intent to enter a short position."""


@dataclass(frozen=True, slots=True)
class CloseSignal(Signal):
    """Strategy intent to close an existing position."""
