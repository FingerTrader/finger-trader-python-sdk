"""Strategy lifecycle and parameter declarations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import ClassVar

from finger_trader.market_data import Bar
from finger_trader.signals import Signal


@dataclass(frozen=True, slots=True)
class StrategyParameter:
    """A simple, declarative strategy parameter with an optional numeric range."""

    default: object
    description: str = ""
    minimum: float | None = None
    maximum: float | None = None

    def validate(self, name: str, value: object) -> object:
        default_type = type(self.default)
        if default_type is bool:
            valid_type = type(value) is bool
        elif default_type is int:
            valid_type = type(value) is int
        elif default_type is float:
            valid_type = isinstance(value, (int, float)) and not isinstance(value, bool)
        else:
            valid_type = isinstance(value, default_type)
        if not valid_type:
            raise TypeError(f"parameter {name!r} must be {default_type.__name__}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(float(value)):
                raise ValueError(f"parameter {name!r} must be finite")
            if self.minimum is not None and value < self.minimum:
                raise ValueError(f"parameter {name!r} must be >= {self.minimum}")
            if self.maximum is not None and value > self.maximum:
                raise ValueError(f"parameter {name!r} must be <= {self.maximum}")
        return value


@dataclass(slots=True)
class StrategyContext:
    """Per-run context; intentionally has no account or order-submission client."""

    parameters: Mapping[str, object]
    current_bar: Bar | None = None
    user_data: dict[str, object] = field(default_factory=dict)


class Strategy:
    """Base class for bar-driven strategies.

    Subclasses declare a PARAMETERS mapping and implement on_bar. Lifecycle hooks
    run locally; returned signals express intent only.
    """

    PARAMETERS: ClassVar[Mapping[str, StrategyParameter]] = {}

    def __init__(self, **parameters: object) -> None:
        unknown = set(parameters) - set(self.PARAMETERS)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"unknown strategy parameter(s): {names}")
        values = {
            name: spec.validate(name, parameters.get(name, spec.default))
            for name, spec in self.PARAMETERS.items()
        }
        self.parameters: Mapping[str, object] = MappingProxyType(values)
        self._context: StrategyContext | None = None

    @property
    def context(self) -> StrategyContext:
        if self._context is None:
            raise RuntimeError("strategy context is available after runtime starts")
        return self._context

    def _attach_context(self, context: StrategyContext) -> None:
        self._context = context

    def on_start(self, context: StrategyContext) -> None:
        """Called once before the first bar."""

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | tuple[Signal, ...] | None:
        """Called for each bar in chronological order."""
        raise NotImplementedError("strategies must implement on_bar")

    def on_stop(self) -> None:
        """Called after a run finishes, including a failure during on_bar."""
