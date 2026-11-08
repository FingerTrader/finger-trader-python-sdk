"""Private hosted entry. JSON-RPC on original stdout; all user output on stderr.

The reader thread stays live while a synchronous strategy waits for a Host
response. Only the main thread imports code and executes serial callbacks.
This is a trusted-local-code process boundary, not a security sandbox.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import platform
import queue
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

from finger_trader import __version__

from . import ProtocolMismatchError, Strategy
from ._context import SCHEMA, BoundContext, model
from ._schema import parse_json

MAX_MESSAGE = 1048576
MAX_QUEUE_BYTES = 16777216
MAX_QUEUE_ITEMS = 1000


class Wire:
    def __init__(self) -> None:
        self.output = os.fdopen(os.dup(1), "wb", buffering=0)
        os.dup2(2, 1)  # print, os.write(1, ...) and native stdout cannot corrupt IPC.
        self.lock = threading.Lock()
        self.pending: dict[str, queue.Queue[Any]] = {}
        self.incoming: queue.Queue[Any] = queue.Queue(MAX_QUEUE_ITEMS)
        self.queued_bytes = 0
        self._input = bytearray()
        self.closed = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def send(self, value: Any) -> None:
        data = json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        if len(data) > MAX_MESSAGE:
            raise ProtocolMismatchError("Outgoing message limit")
        with self.lock:
            self.output.write(data)

    def request(self, value: Any) -> Any:
        waiter: queue.Queue[Any] = queue.Queue(1)
        with self.lock:
            if self.closed:
                raise ProtocolMismatchError("Host transport closed")
            self.pending[value["id"]] = waiter
        try:
            self.send(value)
            result = waiter.get(timeout=10)
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            with self.lock:
                self.pending.pop(value["id"], None)

    def _readline(self) -> bytes:
        # Raw fd I/O avoids CPython's buffered-stdin lock at daemon shutdown.
        while True:
            newline = self._input.find(b"\n")
            if newline >= 0:
                result = bytes(self._input[: newline + 1])
                del self._input[: newline + 1]
                return result
            if len(self._input) > MAX_MESSAGE:
                raise ProtocolMismatchError("Incoming message limit")
            chunk = os.read(0, 4096)
            if not chunk:
                result = bytes(self._input)
                self._input.clear()
                return result
            self._input.extend(chunk)

    def _read(self) -> None:
        try:
            while True:
                raw = self._readline()
                if not raw:
                    raise EOFError("Host disconnected")
                if len(raw) > MAX_MESSAGE or not raw.endswith(b"\n"):
                    raise ProtocolMismatchError("Incoming message limit or incomplete frame")
                value = parse_json(raw)
                if not isinstance(value, dict) or value.get("jsonrpc") != "2.0":
                    raise ProtocolMismatchError("Invalid RPC envelope")
                if "method" not in value:
                    with self.lock:
                        waiter = self.pending.get(str(value.get("id")))
                    if waiter is None:
                        raise ProtocolMismatchError("Unmatched response")
                    waiter.put_nowait(value)
                else:
                    with self.lock:
                        self.queued_bytes += len(raw)
                        if self.queued_bytes > MAX_QUEUE_BYTES:
                            raise ProtocolMismatchError("Incoming queue byte limit")
                    self.incoming.put_nowait((value, len(raw)))
        except BaseException as error:
            with self.lock:
                self.closed = True
                for waiter in self.pending.values():
                    try:
                        waiter.put_nowait(ProtocolMismatchError(str(error)))
                    except queue.Full:
                        pass
            # A callback may be stuck in user code. Parent still owns termination.
            try:
                self.incoming.put_nowait((error, 0))
            except queue.Full:
                os._exit(70)

    def next(self) -> Any:
        value, size = self.incoming.get()
        with self.lock:
            self.queued_bytes -= size
        if isinstance(value, BaseException):
            raise value
        return value


def load_strategy(config: dict[str, Any], context: BoundContext) -> Strategy:
    source = Path(config["source"]).resolve(strict=True)
    spec = importlib.util.spec_from_file_location("_finger_user_strategy", source)
    if spec is None or spec.loader is None:
        raise ProtocolMismatchError("Invalid Python strategy file")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cls = getattr(module, config["class_name"])
    if not inspect.isclass(cls) or not issubclass(cls, Strategy) or cls is Strategy:
        raise ProtocolMismatchError("Entry must inherit finger_trader.hosted.Strategy")
    for name in ("on_start", "on_bar", "on_stop"):
        callback = getattr(cls, name)
        if (
            inspect.iscoroutinefunction(callback)
            or inspect.isgeneratorfunction(callback)
            or inspect.isasyncgenfunction(callback)
        ):
            raise ProtocolMismatchError("Lifecycle must be synchronous and non-generator")
    strategy = cls(**context.parameters)
    if strategy.parameters != context.parameters:
        raise ProtocolMismatchError("Strategy parameters differ from frozen run parameters")
    strategy._context = context
    return strategy


def main() -> int:
    if os.name != "posix":
        raise RuntimeError("Development worker currently requires POSIX process groups")
    os.setsid()  # Before any strategy import. The adapter owns this process group.
    wire = Wire()
    config = parse_json(Path(sys.argv[1]).read_bytes())
    context = BoundContext(config, wire.request)
    first = wire.next()
    SCHEMA.check("Handshake", first)
    params = first["params"]
    if (
        params["run_id"] != context.run_id
        or params["binding_id"] != config["record"]["binding_id"]
        or params["granted_capabilities"] != config["granted_capabilities"]
    ):
        raise ProtocolMismatchError("Handshake does not match frozen configuration")
    strategy = load_strategy(config, context)
    wire.send(
        {
            "jsonrpc": "2.0",
            "id": first["id"],
            "result": {
                "protocol": "1.0",
                "api_major": "1",
                "sdk_version": __version__,
                "worker_version": "1.0-dev",
                "adapter_version": "1.0-dev",
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
                "platform": platform.system() + "-" + platform.machine(),
            },
        }
    )
    started = False
    stopped = False
    last_event = 0
    seen_callbacks: set[str] = set()
    while True:
        message = wire.next()
        method = message.get("method")
        definition = {
            "runtime.on_start": "StartEvent",
            "runtime.on_bar": "BarEvent",
            "runtime.on_stop": "StopEvent",
        }.get(method)
        if definition is None:
            raise ProtocolMismatchError("Unknown lifecycle method")
        SCHEMA.check(definition, message)
        params = message["params"]
        if (
            params["run_id"] != context.run_id
            or params["callback_id"] in seen_callbacks
            or params["event_seq"] != last_event + 1
            or stopped
        ):
            raise ProtocolMismatchError("Stale, out-of-order or cross-run lifecycle")
        if (method == "runtime.on_start") == started:
            raise ProtocolMismatchError("Invalid lifecycle order")
        seen_callbacks.add(params["callback_id"])
        last_event = params["event_seq"]
        phase = "start" if method == "runtime.on_start" else "stop"
        timestamp = params.get("simulation_time")
        if method == "runtime.on_bar":
            phase = "warmup" if params["bar"]["is_warmup"] else "bar"
            timestamp = params["bar"]["close_time"]
        context._callback = {"id": params["callback_id"], "phase": phase, "time": timestamp}
        context._owner = threading.get_ident()
        context._seq = 0
        outcome = "ok"
        try:
            if method == "runtime.on_start":
                callback: Any = strategy.on_start
                result = callback(context)
                started = True
            elif method == "runtime.on_bar":
                callback = strategy.on_bar
                result = callback(model("Bar", params["bar"]))
            else:
                stopped = True
                callback = strategy.on_stop
                result = callback()
            if result is not None:
                raise ProtocolMismatchError("Lifecycle return must be None")
        except BaseException:
            outcome = "error"
            traceback.print_exc(file=sys.stderr)
        finally:
            context._callback = None
            context._owner = None
        wire.send(
            {
                "jsonrpc": "2.0",
                "method": "runtime.callback_complete",
                "params": {
                    "run_id": context.run_id,
                    "callback_id": params["callback_id"],
                    "last_request_seq": context._seq,
                    "outcome": outcome,
                },
            }
        )
        wire.send(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"callback_id": params["callback_id"], "outcome": outcome},
            }
        )
        if outcome == "error" or stopped:
            return 1 if outcome == "error" else 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        exit_code = 70
    sys.exit(exit_code)
