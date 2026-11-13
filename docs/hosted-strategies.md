# Desktop-hosted Python strategies

[English](hosted-strategies.md) | [日本語](hosted-strategies.md) | [繁體中文](hosted-strategies.md) | [한국어](ko/hosted-strategies.md) | [العربية](hosted-strategies.md)


The source now includes the P1 `finger_trader.hosted` API and worker, integrated from SDK commit `ec94ca4a170974808af416e6b00487917497eeda`. This guide describes that implementation. The package remains alpha (`0.1.0`); merging the implementation into `main` does not complete overall P1/P4 platform acceptance or enable live trading.

## Select the right API

| API | Purpose | Execution |
|---|---|---|
| `FingerTraderClient` | HTTP queries and optional WebSocket quotes | Your Python application |
| `finger_trader.hosted.Strategy` | A strategy managed by the Desktop Host | A Host-created worker process |
| Root-level `Strategy` and `StrategyRunner` | Local bar dispatch and intent signals | Caller-supplied bars, no fills or orders |

The types are distinct. Hosted `Bar` uses `instrument_id`, `timeframe`, UTC open/close times, and Decimal OHLCV. Local signal `Bar` uses the independent float-based model. Do not mix imports or return local signals from a hosted callback.

## Minimal observation strategy

Save this as a strategy source file for a compatible Desktop Host:

```python
from finger_trader.hosted import Bar, Context, Strategy


class ObserveClose(Strategy):
    def on_start(self, context: Context) -> None:
        context.log("Observation strategy started")

    def on_bar(self, bar: Bar) -> None:
        if bar.is_warmup:
            return
        self.context.log(f"Close: {bar.close}")

    def on_stop(self) -> None:
        self.context.log("Observation strategy stopped")
```

Select the source and class entry point in the compatible Desktop hosted-strategy workflow, configure the product/timeframe and parameters, validate the environment, and let the Host start the run. Desktop development builds require an exact SDK commit and source inventory. Use the revision pinned by that build rather than substituting `main` into an existing bundle.

This file does not have a standalone execution command. A normal Python import can inspect the models and class, but only a Host-created worker can bind a usable Context. `Context` is a Protocol, not a constructible account client. The private `finger_trader.hosted.worker` entry point expects the initialization/handshake and bidirectional protocol; invoking it manually does not launch a supported strategy run.

## Parameters and data

`Strategy(**parameters)` freezes JSON-compatible parameter values into an immutable mapping. Lists become tuples and mappings become read-only. Supported scalar values are strings, booleans, `None`, and integers within the JSON-safe range ±9007199254740991. Floats are rejected. Store decimal parameters as strings and convert them explicitly at the financial API boundary:

```python
from decimal import Decimal

from finger_trader.hosted import Strategy

strategy = Strategy(quantity="1.25", lookback=20)
quantity = Decimal(str(strategy.parameters["quantity"]))
assert quantity == Decimal("1.25")
```

Financial service arguments must be actual finite `Decimal` values, subject to the contract's precision, range, and instrument constraints. Integers, floats, strings, and booleans are not silently converted into financial amounts. Datetime values must carry a zero UTC offset; naive and nonzero-offset values are rejected.

Public dataclasses are frozen and keyword-only. Returned collections and parameters are snapshots. Optional fields absent on the wire decode to `None`; encoding omits absent optional values. See [models](models.md) and the [type declarations](../contracts/quant/python/finger_trader/hosted/__init__.pyi).

## Lifecycle

| Callback | Behavior |
|---|---|
| `on_start(context)` | Runs once after binding. Trading is forbidden. |
| `on_bar(bar)` | Runs serially for each Host-dispatched bar; warmup is explicit. |
| `on_stop()` | Attempted once after a successful start, including callback failure cleanup. Forced termination cannot guarantee it runs. |

Callbacks are ordinary synchronous methods and return `None`. Async methods, generators, and non-`None` returns fail validation. Returning `BuySignal` or `SellSignal` does not submit an order.

Context service calls are synchronous. A dedicated reader continues to handle Host responses while the strategy waits. The Host owns the callback deadline and completion barrier; the worker does not impose an unrelated ten-second query timer.

Only the active callback's owning thread may call services. The worker rejects user-thread calls before IPC, and the Host independently verifies run identity, callback identity, request sequence, stage, and capability. `now`, `phase`, and `is_warmup` are active-callback properties. The initial mode is `backtest`; it does not imply that a matcher or broker is implemented.

## Context services

Full signatures, defaults, field units, and wire mappings are in the [API contract](quant/python-managed-api-v1.md) and [type declarations](../contracts/quant/python/finger_trader/hosted/__init__.pyi).

| Method | Result | Capability |
|---|---|---|
| `history(...)` | Immutable tuple of hosted `Bar` | `history.read` |
| `account()` | `Account` snapshot | `account.read` |
| `position()` | Bound-instrument `Position` | `account.read` |
| `get_order(order_id)` | `OrderSnapshot` | `account.read` |
| `submit_order(...)` | `OrderSubmission` | `orders.write` |
| `cancel_order(order_id)` | `OrderSnapshot` | `orders.write` |
| `exit_protected(group_id, quantity)` | `ExitResult` | `orders.write` |
| `log(message, level="INFO")` | `Acknowledgement` | Basic logging permission |
| `plot(series_id, value, ...)` | `Acknowledgement` | `plots.write` |
| `marker(marker_id, label=..., price=..., ...)` | `Acknowledgement` | `plots.write` |

History is scoped to the bound instrument/timeframe and cannot read future bars. Missing data produces an empty tuple. Read/output services require explicit Host implementations and permissions; the SDK does not invent account, price, or order data.

Trading is forbidden in `on_start`, warmup, and `on_stop`. Plot/marker output is forbidden in `on_stop`. Ordinary bar callbacks still need the relevant granted capability. **The current P1 Desktop integration has no trading engine and returns `UNSUPPORTED_CAPABILITY` for trading requests.** Public order signatures preserve the contract for future capable Hosts; they do not implement simulated fills, a ledger, or live orders.

Inspect results: `Acknowledgement(accepted=False)` can indicate rejected/throttled output. `OrderSubmission(status="accepted")` means submission acceptance rather than a fill; `status="rejected"` carries a business code. The presence of these models does not imply current Host support.

## Errors and resource handling

Hosted exceptions derive from `HostedError`. Stable business codes include `INVALID_ARGUMENT`, `PERMISSION_DENIED`, `STALE_CALLBACK`, `PROTOCOL_MISMATCH`, `UNSUPPORTED_CAPABILITY`, `IO_FAILURE`, and `STOPPING`; the full mapping is in the contract. Do not match error message text. There is no implicit HTTP fallback or automatic write retry, and a failed callback does not undo already accepted operations.

User print/raw stdout is redirected to stderr so it cannot corrupt JSON-RPC output. Message and queue limits are enforced. On POSIX, the worker establishes its own process group before executing user code. An unrecoverable Host disconnect starts a non-daemon watchdog before waking waiters, allowing cleanup of a stuck callback and ordinary child processes. The Host must still confirm process/resource termination; sending a signal alone is not proof of cleanup.

Only run trusted local code. This process model is not a security sandbox and does not promise cleanup of code that deliberately escapes its process group. Keep credentials out of strategy source, parameters, logs, and plots. See [Security](security.md).

## Verification and remaining work

The source includes hosted public API/model checks, real-process disconnect checks, contract fixtures, and source inventories. The normal SDK checks remain in place. Contributor verification uses the checked-out source explicitly:

```sh
PYTHONPATH=src python -m pytest
PYTHONPATH=src python -B tools/quant/check_disconnect.py --report-dir /tmp/sdk-disconnect
python -B tools/quant/quality.py --dart /path/to/pinned/dart --report-dir /tmp/sdk-contracts
```

Use the Dart version in [the toolchain pin](../ci/quant-toolchain.json); it is required for cross-language contract checks, not for importing the Python SDK. Desktop Host/UI/platform checks belong to the matching Desktop checkout. Review [implementation status](quant/p1-hosted-status.md) and [the toolchain guide](quant/quality-toolchain.md) for the development boundary.

A standalone backtesting engine, optimization engine, trading ledger, live execution, complete signed Runtime installation/update, clean-machine platform verification, and unresolved native/stop behavior are not completed by this merge. No version tag, PyPI upload, or client release is created by integrating the source into `main`.
