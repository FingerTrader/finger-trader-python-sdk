from __future__ import annotations

import unittest

from examples.dual_ma_strategy import (
    DualMovingAverageStrategy,
    create_demo_bars,
    run_example,
)
from finger_trader import BuySignal, CloseSignal, StrategyRunner


class DualMovingAverageExampleTests(unittest.TestCase):
    def test_example_emits_buy_and_close_intents_at_expected_bars(self) -> None:
        signals = run_example()
        self.assertEqual([type(signal) for signal in signals], [BuySignal, CloseSignal])
        bars = create_demo_bars()
        self.assertEqual(signals[0].timestamp, bars[4].timestamp)
        self.assertEqual(signals[1].timestamp, bars[7].timestamp)
        self.assertTrue(all(signal.symbol == "DEMO" for signal in signals))

    def test_example_strategy_accepts_parameter_overrides(self) -> None:
        strategy = DualMovingAverageStrategy(short_period=2, long_period=4)
        self.assertEqual(strategy.parameters["short_period"], 2)
        self.assertEqual(strategy.parameters["long_period"], 4)

    def test_sample_is_processed_in_historical_order(self) -> None:
        bars = create_demo_bars()
        timestamps = [item.timestamp for item in bars]
        self.assertEqual(timestamps, sorted(timestamps))
        signals = StrategyRunner(DualMovingAverageStrategy()).run(bars)
        self.assertEqual(len(signals), 2)


if __name__ == "__main__":
    unittest.main()
