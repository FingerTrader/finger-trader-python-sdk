"""Dependency-free market-data models used by strategies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math


class Timeframe(str, Enum):
    """Common candle intervals. Custom interval strings are also accepted by Bar."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass(frozen=True, slots=True)
class Bar:
    """One OHLCV candle. Timestamps must be timezone-aware; UTC is recommended."""

    symbol: str
    timestamp: datetime
    timeframe: str | Timeframe
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if not str(self.timeframe).strip():
            raise ValueError("timeframe must not be empty")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")

        prices = (self.open, self.high, self.low, self.close)
        if not all(math.isfinite(value) for value in prices):
            raise ValueError("OHLC prices must be finite")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be >= open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be <= open, close, and high")
        if not math.isfinite(self.volume) or self.volume < 0:
            raise ValueError("volume must be finite and non-negative")
