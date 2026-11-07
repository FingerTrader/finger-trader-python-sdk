"""A small chronological bar dispatcher; it does not simulate executions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from finger_trader.market_data import Bar
from finger_trader.signals import BuySignal, CloseSignal, SellSignal, Signal
from finger_trader.strategy import Strategy, StrategyContext


class RuntimeState(Enum):
    CREATED = "created"
    RUNNING = "running"
    FINISHED = "finished"


class StrategyRunner:
    """Run one Strategy instance once over bars ordered by timestamp per symbol."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy
        self.state = RuntimeState.CREATED
        self.context = StrategyContext(parameters=strategy.parameters)
        self._last_timestamp: dict[str, datetime] = {}

    def run(self, bars: Iterable[Bar]) -> list[Signal]:
        if self.state is not RuntimeState.CREATED:
            raise RuntimeError("a StrategyRunner instance can only be run once")

        self.state = RuntimeState.RUNNING
        self.strategy._attach_context(self.context)
        started = False
        signals: list[Signal] = []
        try:
            self.strategy.on_start(self.context)
            started = True
            for bar in bars:
                previous = self._last_timestamp.get(bar.symbol)
                if previous is not None and bar.timestamp < previous:
                    raise ValueError(f"bars for {bar.symbol!r} must be chronological")
                self._last_timestamp[bar.symbol] = bar.timestamp
                self.context.current_bar = bar
                result = self.strategy.on_bar(bar)
                if result is None:
                    continue
                emitted = [result] if isinstance(result, Signal) else list(result)
                for signal in emitted:
                    if not isinstance(signal, (BuySignal, SellSignal, CloseSignal)):
                        raise TypeError("strategies must return SDK signal objects")
                signals.extend(emitted)
            return signals
        finally:
            try:
                if started:
                    self.strategy.on_stop()
            finally:
                self.state = RuntimeState.FINISHED
