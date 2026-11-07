"""Standalone local demo: python examples/dual_ma_strategy.py"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from finger_trader import (
    Bar,
    BuySignal,
    CloseSignal,
    SMA,
    Strategy,
    StrategyContext,
    StrategyParameter,
    StrategyRunner,
    crosses_above,
    crosses_below,
)


class DualMovingAverageStrategy(Strategy):
    """Buy a moving-average up-cross and close on a down-cross."""

    PARAMETERS = {
        "short_period": StrategyParameter(
            default=2, description="Fast SMA period", minimum=1
        ),
        "long_period": StrategyParameter(
            default=3, description="Slow SMA period", minimum=2
        ),
    }

    def __init__(self, **parameters: object) -> None:
        super().__init__(**parameters)
        self._short = SMA(int(self.parameters["short_period"]))
        self._long = SMA(int(self.parameters["long_period"]))
        self._previous_short: float | None = None
        self._previous_long: float | None = None

    def on_start(self, context: StrategyContext) -> None:
        self._short.reset()
        self._long.reset()
        self._previous_short = None
        self._previous_long = None

    def on_bar(self, bar: Bar) -> list[BuySignal | CloseSignal]:
        fast = self._short.update(bar.close)
        slow = self._long.update(bar.close)
        emitted: list[BuySignal | CloseSignal] = []

        if crosses_above(self._previous_short, self._previous_long, fast, slow):
            emitted.append(
                BuySignal(
                    symbol=bar.symbol,
                    timestamp=bar.timestamp,
                    reason="short SMA crossed above long SMA",
                )
            )
        elif crosses_below(self._previous_short, self._previous_long, fast, slow):
            emitted.append(
                CloseSignal(
                    symbol=bar.symbol,
                    timestamp=bar.timestamp,
                    reason="short SMA crossed below long SMA",
                )
            )

        self._previous_short = fast
        self._previous_long = slow
        return emitted


def create_demo_bars() -> list[Bar]:
    """Build deterministic OHLCV bars; no network or account is used."""
    closes = [3.0, 2.0, 1.0, 2.0, 3.0, 4.0, 2.0, 0.5]
    start = datetime(2026, 1, 5, 9, tzinfo=timezone.utc)
    return [
        Bar(
            symbol="DEMO",
            timestamp=start + timedelta(minutes=index),
            timeframe="1m",
            open=close,
            high=close + 0.5,
            low=max(0.0, close - 0.5),
            close=close,
            volume=100.0 + index,
        )
        for index, close in enumerate(closes)
    ]


def run_example() -> list[BuySignal | CloseSignal]:
    return StrategyRunner(DualMovingAverageStrategy()).run(create_demo_bars())


if __name__ == "__main__":
    output = run_example()
    if output:
        for signal in output:
            print(
                f"DEMO SIGNAL: {type(signal).__name__} "
                f"{signal.symbol} {signal.timestamp.isoformat()} — {signal.reason}"
            )
    else:
        print("No strategy signals were generated.")
    print("Signals only: no orders were submitted and no fills were simulated.")
