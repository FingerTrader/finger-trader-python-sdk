"""P0 tests must actually execute; empty discovery and skips fail the gate."""

import sys
import unittest
from pathlib import Path


def require_complete(result):
    if result.testsRun < 21 or result.skipped or not result.wasSuccessful():
        raise ValueError("incomplete, skipped, or failed P0 regression suite")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    suite = unittest.defaultTestLoader.discover(str(root / "tests/quant_contracts"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    try:
        require_complete(result)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
