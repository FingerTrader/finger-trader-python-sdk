"""Moving-series crossover predicates."""

from __future__ import annotations

import math


def _valid(*values: float | None) -> bool:
    return all(value is not None and math.isfinite(value) for value in values)


def crosses_above(
    previous_left: float | None,
    previous_right: float | None,
    current_left: float | None,
    current_right: float | None,
) -> bool:
    """True when left moves from at/below right to strictly above it."""

    if not _valid(previous_left, previous_right, current_left, current_right):
        return False
    assert previous_left is not None and previous_right is not None
    assert current_left is not None and current_right is not None
    return previous_left <= previous_right and current_left > current_right


def crosses_below(
    previous_left: float | None,
    previous_right: float | None,
    current_left: float | None,
    current_right: float | None,
) -> bool:
    """True when left moves from at/above right to strictly below it."""

    if not _valid(previous_left, previous_right, current_left, current_right):
        return False
    assert previous_left is not None and previous_right is not None
    assert current_left is not None and current_right is not None
    return previous_left >= previous_right and current_left < current_right
