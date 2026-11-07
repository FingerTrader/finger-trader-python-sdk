"""Simple moving average helpers."""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Iterable


class SMA:
    """Streaming simple moving average with O(1) updates."""

    def __init__(self, period: int) -> None:
        if isinstance(period, bool) or period <= 0:
            raise ValueError("period must be a positive integer")
        if not isinstance(period, int):
            raise TypeError("period must be an integer")
        self.period = period
        self._values: deque[float] = deque()
        self._total = 0.0

    def update(self, value: float) -> float | None:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("SMA values must be finite")
        self._values.append(number)
        self._total += number
        if len(self._values) > self.period:
            self._total -= self._values.popleft()
        if len(self._values) < self.period:
            return None
        return self._total / self.period

    def reset(self) -> None:
        self._values.clear()
        self._total = 0.0


def sma(values: Iterable[float], period: int) -> list[float | None]:
    """Return a same-length series; entries before the first full window are None."""

    indicator = SMA(period)
    return [indicator.update(value) for value in values]
