"""Real Host death must not leave an isolated worker group alive (POSIX)."""

from __future__ import annotations

import errno
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "contracts/quant/v1/messages.json").read_text())["cases"]


def example(name):
    return json.loads(
        json.dumps(next(c["value"] for c in CASES if c["definition"] == name and c["valid"]))
    )


def gone(pid, *, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except OSError as error:
        if error.errno == errno.ESRCH:
            return True
        raise
    return False


def wait_absent(worker, child, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if gone(worker) and gone(child) and gone(worker, group=True):
            return True
        time.sleep(0.02)
    return False


def host(source_root, directory, phase):
    """Separate real parent process. The test SIGKILLs this after a sealed stage."""
    strategy = directory / "strategy.py"
    strategy.write_text("""from finger_trader.hosted import Strategy
import subprocess,sys
class UserStrategy(Strategy):
    def on_start(self, ctx):
        self.child = subprocess.Popen(
            [sys.executable, '-I', '-B', '-c', 'import time;time.sleep(600)'])
        ctx.log('child=' + str(self.child.pid))
    def on_bar(self, bar):
        mode = self.parameters['phase']
        if mode == 'busy':
            self.context.log('busy')
            while True: pass
        elif mode == 'query': self.context.account()
        elif mode == 'error': raise RuntimeError('controlled callback failure')
    def on_stop(self): self.context.log('stop')
""")
    config = {
        "source": str(strategy),
        "class_name": "UserStrategy",
        "callback_timeout_ms": 10000,
        "parameters": {"phase": phase},
        "record": {"run_id": "disconnect", "binding_id": "fixed-test"},
        "instrument": example("Instrument"),
        "timeframe": "1m",
        "granted_capabilities": ["account.read"],
    }
    (directory / "config.json").write_text(json.dumps(config))
    with (directory / "worker.log").open("wb") as log:
        worker = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-B",
                "-u",
                "-c",
                "import sys,runpy;sys.path.insert(0,sys.argv.pop(1));"
                'runpy.run_module("finger_trader.hosted.worker",run_name="__main__")',
                str(source_root / "src"),
                str(directory / "config.json"),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log,
            bufsize=0,
        )
        child = None
        stops = 0
        owned = directory / "owned.json"
        owned.write_text(json.dumps({"host": os.getpid(), "worker": worker.pid, "child": None}))

        def send(message):
            worker.stdin.write(json.dumps(message).encode() + b"\n")
            worker.stdin.flush()

        def ready(outcome=None):
            data = {
                "phase": phase,
                "worker": worker.pid,
                "child": child,
                "host": os.getpid(),
                "outcome": outcome,
                "stops": stops,
            }
            temp = directory / "ready.tmp"
            temp.write_text(json.dumps(data))
            temp.replace(directory / "ready.json")

        def receive(until, *, blocked=False):
            nonlocal child, stops
            while True:
                raw = worker.stdout.readline()
                if not raw:
                    raise RuntimeError(
                        "Worker exited before stage: " + (directory / "worker.log").read_text()
                    )
                message = json.loads(raw)
                method = message.get("method")
                if method == "context.log":
                    text = message["params"]["payload"]["message"]
                    if text.startswith("child="):
                        child = int(text[6:])
                        owned.write_text(
                            json.dumps({"host": os.getpid(), "worker": worker.pid, "child": child})
                        )
                    if text == "stop":
                        stops += 1
                    send({"jsonrpc": "2.0", "id": message["id"], "result": {"accepted": True}})
                    if blocked and text == "busy":
                        ready()
                        return
                elif method == "context.account" and blocked:
                    ready()  # Deliberately withhold response: SDK synchronous query is pending.
                    return
                elif message.get("id") == until and "result" in message:
                    return message["result"]

        hello = example("Handshake")
        hello["params"].update(
            run_id="disconnect", binding_id="fixed-test", granted_capabilities=["account.read"]
        )
        send(hello)
        receive(hello["id"])
        start = example("StartEvent")
        start.update(id="start")
        start["params"].update(run_id="disconnect", callback_id="start", event_seq=1)
        send(start)
        receive("start")
        if not child or os.getpgid(worker.pid) != worker.pid or os.getpgid(child) != worker.pid:
            raise RuntimeError("Worker/ordinary child not in the owned isolated group")
        if phase == "normal":
            stop = example("StopEvent")
            stop["id"] = "stop"
            stop["params"].update(run_id="disconnect", callback_id="stop", event_seq=2)
            send(stop)
            receive("stop")
            code = worker.wait(timeout=5)
            # Normal Host cleanup owns ordinary children, matching the Dart adapter.
            if not gone(worker.pid, group=True):
                os.killpg(worker.pid, signal.SIGKILL)
            ready(code)
            return
        if phase in ("busy", "query", "error"):
            bar = example("BarEvent")
            bar["id"] = "bar"
            bar["params"].update(run_id="disconnect", callback_id="bar", event_seq=2)
            send(bar)
            result = receive("bar", blocked=phase in ("busy", "query"))
            if phase == "error":
                if result.get("outcome") != "error":
                    raise RuntimeError("Expected a real callback failure")
                ready("error")
        else:
            ready()
        # Parent remains alive until killed by the independent test controller.
        while True:
            time.sleep(1)


class HostedDisconnect(unittest.TestCase):
    def run_case(self, phase, *, source_root=ROOT, timeout=5):
        with tempfile.TemporaryDirectory(prefix="hosted-disconnect-") as name:
            directory = Path(name)
            with (directory / "host.log").open("wb") as log:
                parent = subprocess.Popen(
                    [
                        sys.executable,
                        "-I",
                        "-B",
                        str(Path(__file__).resolve()),
                        "--host",
                        str(source_root),
                        name,
                        phase,
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                info = None
                try:
                    deadline = time.monotonic() + 10
                    while not (directory / "ready.json").exists():
                        if parent.poll() is not None or time.monotonic() > deadline:
                            self.fail(
                                "Parent did not reach stage: "
                                + (directory / "host.log").read_text()
                            )
                        time.sleep(0.01)
                    info = json.loads((directory / "ready.json").read_text())
                    self.assertEqual(info["phase"], phase)
                    self.assertGreater(info["worker"], 0)
                    self.assertGreater(info["child"], 0)
                    if phase != "normal":
                        parent.kill()
                        self.assertEqual(parent.wait(timeout=5), -signal.SIGKILL)
                    else:
                        self.assertEqual(parent.wait(timeout=5), 0)
                        self.assertEqual(info["outcome"], 0)
                        self.assertEqual(info["stops"], 1)
                    self.assertTrue(
                        wait_absent(info["worker"], info["child"], timeout),
                        f"{phase}: worker/child/group survived real Host exit: {info}",
                    )
                finally:
                    if parent.poll() is None:
                        parent.kill()
                    parent.wait(timeout=5)
                    if info is None and (directory / "owned.json").exists():
                        info = json.loads((directory / "owned.json").read_text())
                    if info:
                        # Fresh identities from this test's parent, never old run records.
                        worker, child = info["worker"], info["child"]
                        if not gone(worker):
                            self.assertEqual(os.getpgid(worker), worker)
                            os.killpg(worker, signal.SIGKILL)
                        elif child and not gone(child):
                            self.assertEqual(os.getpgid(child), worker)
                            os.killpg(worker, signal.SIGKILL)
                        if child:
                            self.assertTrue(wait_absent(worker, child, 5), "Test cleanup failed")

    def test_idle_parent_crash(self):
        for _ in range(3):
            self.run_case("idle")

    def test_busy_parent_crash(self):
        self.run_case("busy")

    def test_pending_query_parent_crash(self):
        self.run_case("query")

    def test_callback_error_parent_crash(self):
        self.run_case("error")

    def test_normal_stop_keeps_success_and_single_on_stop(self):
        self.run_case("normal")

    def test_cleanup_never_signals_an_unowned_group_or_reports_success(self):
        from finger_trader.hosted.worker import Wire

        for group, failure in [(12344, None), (12345, PermissionError("denied"))]:
            with (
                patch("os.getpid", return_value=12345),
                patch("os.getpgrp", return_value=group),
                patch("os.killpg", side_effect=failure) as kill,
                patch("os.write"),
                patch("os._exit", side_effect=SystemExit(70)),
            ):
                with self.assertRaises(SystemExit) as raised:
                    Wire._exit_disconnected_group()
                self.assertEqual(raised.exception.code, 70)
                if group == 12345:
                    kill.assert_called_once_with(group, signal.SIGKILL)
                else:
                    kill.assert_not_called()

    def test_daemon_watchdog_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="hosted-disconnect-mutant-") as name:
            mutant = Path(name)
            shutil.copytree(
                ROOT / "src", mutant / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
            file = mutant / "src/finger_trader/hosted/worker.py"
            source = file.read_text()
            self.assertEqual(source.count("watchdog.daemon = False"), 1)
            file.write_text(source.replace("watchdog.daemon = False", "watchdog.daemon = True"))
            with self.assertRaisesRegex(AssertionError, "survived real Host exit"):
                self.run_case("idle", source_root=mutant, timeout=2)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--host":
        host(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
    else:
        unittest.main()
