from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from finger_trader import (
    Bar,
    RuntimeState,
    Strategy,
    StrategyContext,
    StrategyParameter,
    StrategyRunner,
)


def bar(minute: int, close: float = 10.0) -> Bar:
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minute)
    return Bar(
        symbol="TEST",
        timestamp=timestamp,
        timeframe="1m",
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=1,
    )


class RecordingStrategy(Strategy):
    PARAMETERS = {"window": StrategyParameter(default=5, minimum=1)}

    def __init__(self) -> None:
        super().__init__()
        self.events: list[object] = []

    def on_start(self, context: StrategyContext) -> None:
        self.events.append(("start", context.parameters["window"]))

    def on_bar(self, item: Bar) -> None:
        self.events.append((item.timestamp, item.close, self.context.current_bar))

    def on_stop(self) -> None:
        self.events.append(("stop", None))


class StrategyRunnerTests(unittest.TestCase):
    def test_import_public_api(self) -> None:
        from finger_trader import (
            SMA,
            BuySignal,
            CloseSignal,
            SellSignal,
        )
        from finger_trader import (
            Bar as PublicBar,
        )
        from finger_trader import (
            StrategyRunner as PublicRunner,
        )

        self.assertIs(PublicBar, Bar)
        self.assertTrue(BuySignal and CloseSignal and SellSignal and SMA and PublicRunner)

    def test_lifecycle_context_and_chronological_processing(self) -> None:
        strategy = RecordingStrategy()
        runner = StrategyRunner(strategy)
        runner.run([bar(0, 10), bar(1, 11), bar(2, 12)])

        self.assertEqual(runner.state, RuntimeState.FINISHED)
        self.assertEqual(strategy.events[0], ("start", 5))
        self.assertEqual([event[1] for event in strategy.events[1:4]], [10, 11, 12])
        self.assertEqual(strategy.events[-1], ("stop", None))
        self.assertEqual(runner.context.current_bar, bar(2, 12))

    def test_out_of_order_bars_fail_and_stop_hook_runs(self) -> None:
        strategy = RecordingStrategy()
        runner = StrategyRunner(strategy)
        with self.assertRaisesRegex(ValueError, "chronological"):
            runner.run([bar(1), bar(0)])
        self.assertEqual(strategy.events[-1], ("stop", None))
        self.assertEqual(runner.state, RuntimeState.FINISHED)

    def test_runner_is_single_use(self) -> None:
        runner = StrategyRunner(RecordingStrategy())
        runner.run([bar(0)])
        with self.assertRaisesRegex(RuntimeError, "only be run once"):
            runner.run([bar(1)])


if __name__ == "__main__":
    unittest.main()
