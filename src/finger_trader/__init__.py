"""Public API for the Finger Trader Python SDK foundation."""

from finger_trader.indicators import SMA, crosses_above, crosses_below, sma
from finger_trader.market_data import Bar, Timeframe
from finger_trader.runtime import RuntimeState, StrategyRunner
from finger_trader.signals import BuySignal, CloseSignal, SellSignal, Signal
from finger_trader.strategy import Strategy, StrategyContext, StrategyParameter

__all__ = [
    "Bar",
    "BuySignal",
    "CloseSignal",
    "RuntimeState",
    "SMA",
    "SellSignal",
    "Signal",
    "Strategy",
    "StrategyContext",
    "StrategyParameter",
    "StrategyRunner",
    "Timeframe",
    "crosses_above",
    "crosses_below",
    "sma",
]

__version__ = "0.1.0"
