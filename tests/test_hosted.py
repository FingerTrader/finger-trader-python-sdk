"""The frozen public declarations and actual transport obey the same contract."""

import ast
import hashlib
import json
import threading
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import finger_trader.hosted as hosted
from finger_trader.hosted._context import BoundContext, model, rpc_error, wire
from finger_trader.hosted._schema import ContractError, Schema, parse_json

ROOT = Path(__file__).resolve().parents[1]


class HostedAPI(unittest.TestCase):
    def test_owned_source_inventory(self):
        inventory = json.loads((ROOT / "ci/quant-hosted-files.json").read_text())
        for relative, digest in inventory["files"].items():
            self.assertEqual(
                hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative
            )
        sources = {
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "src/finger_trader").rglob("*")
            if p.is_file() and p.suffix in (".py", ".json")
        }
        self.assertEqual(sources, {name for name in inventory["files"] if name.startswith("src/")})

    def test_frozen_public_signatures_and_models(self):
        stub = ast.parse(
            (ROOT / "contracts/quant/python/finger_trader/hosted/__init__.pyi").read_text()
        )
        implementation = ast.parse(Path(hosted.__file__).read_text())
        bound = next(
            node
            for node in ast.parse((Path(hosted.__file__).parent / "_context.py").read_text()).body
            if isinstance(node, ast.ClassDef) and node.name == "BoundContext"
        )
        declared = {node.name: node for node in stub.body if isinstance(node, ast.ClassDef)}
        implemented = {
            node.name: node for node in implementation.body if isinstance(node, ast.ClassDef)
        }
        for name, specification in declared.items():
            self.assertIn(name, hosted.__all__)
            actual = implemented[name]
            if name in ("Context", "Strategy"):
                methods = {
                    node.name: node for node in actual.body if isinstance(node, ast.FunctionDef)
                }
                for method in specification.body:
                    if isinstance(method, ast.FunctionDef):
                        self.assertEqual(
                            ast.dump(method.args),
                            ast.dump(methods[method.name].args),
                            f"{name}.{method.name}",
                        )
                        self.assertEqual(
                            ast.dump(method.returns),
                            ast.dump(methods[method.name].returns),
                            f"{name}.{method.name}",
                        )
                        if name == "Context":
                            bound_method = next(
                                node
                                for node in bound.body
                                if isinstance(node, ast.FunctionDef) and node.name == method.name
                            )
                            self.assertEqual(ast.dump(method.args), ast.dump(bound_method.args))
                            self.assertEqual(
                                ast.dump(method.returns), ast.dump(bound_method.returns)
                            )
            fields = [
                ast.dump(node) for node in specification.body if isinstance(node, ast.AnnAssign)
            ]
            if fields and name != "HostedError":
                self.assertEqual(
                    fields,
                    [ast.dump(node) for node in actual.body if isinstance(node, ast.AnnAssign)],
                )
        with self.assertRaises(hosted.StaleCallbackError):
            _ = hosted.Strategy().context
        with self.assertRaises(TypeError):
            hosted.Context()

    def test_frozen_assets_and_all_shared_message_cases(self):
        package = Path(hosted.__file__).parent
        for name in ("schema", "methods", "python-api", "policy"):
            self.assertEqual(
                (package / f"{name}.json").read_bytes(),
                (ROOT / f"contracts/quant/v1/{name}.json").read_bytes(),
            )
        validator = Schema(json.loads((package / "schema.json").read_text()))
        for case in json.loads((ROOT / "contracts/quant/v1/messages.json").read_text())["cases"]:
            with self.subTest(case=case["name"]):
                try:
                    validator.check(
                        case["definition"],
                        parse_json(case["raw"]) if "raw" in case else case["value"],
                    )
                    passed = True
                except (ContractError, ValueError, TypeError):
                    passed = False
                self.assertEqual(passed, case["valid"])

    def context(self):
        cases = json.loads((ROOT / "contracts/quant/v1/messages.json").read_text())["cases"]
        instrument = next(
            case["value"] for case in cases if case["definition"] == "Instrument" and case["valid"]
        )
        account = {
            "cash": "0.1000000000000000001",
            "reserved_cash": "0",
            "available_cash": "0.1000000000000000001",
            "position_quantity": "0",
            "position_cost": "0",
            "realized_pnl": "0",
        }
        requests = []

        def transport(request):
            requests.append(request)
            return {"jsonrpc": "2.0", "id": request["id"], "result": account}

        context = BoundContext(
            {
                "record": {"run_id": "fixture"},
                "parameters": {"nested": [1]},
                "instrument": instrument,
                "timeframe": "1m",
                "granted_capabilities": ["account.read", "orders.write", "plots.write"],
            },
            transport,
        )
        context._callback = {"id": "callback", "phase": "bar", "time": "2026-01-01T00:00:00Z"}
        context._owner = threading.get_ident()
        return context, requests

    def test_decimal_thread_permissions_and_no_local_error_sequence_gap(self):
        context, requests = self.context()
        self.assertEqual(context.account().cash, Decimal("0.1000000000000000001"))
        with self.assertRaises(FrozenInstanceError):
            context.account().cash = Decimal("1")
        for value in (0.1, 1, "1", True, Decimal("NaN"), Decimal("1e999999")):
            with self.assertRaises(hosted.InvalidArgumentError):
                context.plot("x", value)
        with self.assertRaises(hosted.InvalidArgumentError):
            context.history(end_time=datetime(2026, 1, 1))
        context.account()
        self.assertEqual([request["params"]["request_seq"] for request in requests], [1, 2, 3])
        errors = []

        def other():
            try:
                context.account()
            except hosted.PermissionDeniedError:
                errors.append(True)

        thread = threading.Thread(target=other)
        thread.start()
        thread.join()
        self.assertEqual(errors, [True])
        context._callback["phase"] = "warmup"
        with self.assertRaises(hosted.PermissionDeniedError):
            context.submit_order(client_order_id="entry", side="buy", quantity=Decimal("1"))
        context._callback = None
        with self.assertRaises(hosted.StaleCallbackError):
            context.account()
        self.assertEqual(len(requests), 3)

    def test_all_error_mappings_and_immutable_parameters(self):
        api = json.loads((ROOT / "contracts/quant/v1/python-api.json").read_text())
        for code, name in api["errors"].items():
            error = rpc_error({"code": -32000, "message": "controlled", "data": {"code": code}})
            self.assertIsInstance(error, getattr(hosted, name))
            self.assertEqual(error.code, code)
            self.assertEqual(error.rpc_code, -32000)
        self.assertIsInstance(
            rpc_error({"code": -32000, "message": "unknown", "data": {"code": "BAD"}}),
            hosted.ProtocolMismatchError,
        )
        self.assertEqual(
            wire(datetime(2026, 1, 1, tzinfo=timezone.utc)), "2026-01-01T00:00:00.000000Z"
        )
        strategy = hosted.Strategy(nested={"items": [1, "0.1"]})
        with self.assertRaises(TypeError):
            strategy.parameters["nested"]["items"] = ()
        with self.assertRaises(hosted.InvalidArgumentError):
            hosted.Strategy(invalid=0.1)
        self.assertEqual(model("Acknowledgement", {"accepted": False}).accepted, False)
