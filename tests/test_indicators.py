from __future__ import annotations

import unittest

from finger_trader import SMA, crosses_above, crosses_below, sma


class MovingAverageTests(unittest.TestCase):
    def test_sma_series_uses_none_until_window_is_full(self) -> None:
        self.assertEqual(sma([1, 2, 3, 4, 5], 3), [None, None, 2.0, 3.0, 4.0])

    def test_streaming_sma_and_reset(self) -> None:
        indicator = SMA(2)
        self.assertIsNone(indicator.update(10))
        self.assertEqual(indicator.update(12), 11)
        self.assertEqual(indicator.update(14), 13)
        indicator.reset()
        self.assertIsNone(indicator.update(4))

    def test_sma_rejects_invalid_period(self) -> None:
        for period in (0, -1):
            with self.subTest(period=period), self.assertRaises(ValueError):
                SMA(period)

    def test_cross_above(self) -> None:
        self.assertTrue(crosses_above(1, 2, 3, 2))
        self.assertTrue(crosses_above(2, 2, 2.1, 2))
        self.assertFalse(crosses_above(3, 2, 4, 2))
        self.assertFalse(crosses_above(None, 2, 3, 2))

    def test_cross_below(self) -> None:
        self.assertTrue(crosses_below(3, 2, 1, 2))
        self.assertTrue(crosses_below(2, 2, 1.9, 2))
        self.assertFalse(crosses_below(1, 2, 0, 2))
        self.assertFalse(crosses_below(3, 2, float("nan"), 2))


if __name__ == "__main__":
    unittest.main()
