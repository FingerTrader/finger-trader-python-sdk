"""Regression evidence for the three remaining P0 review items."""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/quant"))
from core_dependencies import boundaries  # noqa: E402
from opening_reference import opening_result  # noqa: E402
from python_api_check import check_api  # noqa: E402


class CoreAllowlist(unittest.TestCase):
    def workspace(self, tmp):
        root = Path(tmp)
        path = root / "contracts/quant/v1/core-dependencies.json"
        path.parent.mkdir(parents=True)
        path.write_bytes((ROOT / "contracts/quant/v1/core-dependencies.json").read_bytes())
        (root / "lib/app/quant").mkdir(parents=True)
        return root

    def test_get_unknown_packages_and_all_internal_edges_fail(self):
        for edge in (
            "import 'bridge.dart';",
            "export 'bridge.dart';",
            "part 'bridge.dart';",
            "import 'safe.dart' if (dart.library.io) 'bridge.dart';",
            "import 'package:finger_desk/bridge.dart';",
            "import 'package:get/get.dart';",
        ):
            with self.subTest(edge=edge), tempfile.TemporaryDirectory() as tmp:
                root = self.workspace(tmp)
                (root / "lib/app/quant/host.dart").write_text(
                    edge + "\nclass Host extends GetxController {}"
                )
                (root / "lib/app/quant/safe.dart").write_text("import 'dart:collection';")
                (root / "lib/app/quant/bridge.dart").write_text(
                    "import /* hidden */ 'package:get/get.dart';"
                )
                (root / "lib/bridge.dart").write_text("export 'app/quant/bridge.dart';")
                with self.assertRaisesRegex(ValueError, "unreviewed external package"):
                    boundaries(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.workspace(tmp)
            (root / "lib/app/quant/core.dart").write_text(
                "import 'package:unknown_pure/pure.dart';"
            )
            with self.assertRaisesRegex(ValueError, "unreviewed external package"):
                boundaries(root)

    def test_pure_dart_passes_and_adapter_cannot_flow_into_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.workspace(tmp)
            (root / "lib/app/quant/core.dart").write_text(
                "import 'dart:collection'; export 'pure.dart';"
            )
            (root / "lib/app/quant/pure.dart").write_text(
                "// import 'package:get/get.dart';\nimport 'dart:math';"
            )
            adapter = root / "lib/app/quant/presentation/view.dart"
            adapter.parent.mkdir()
            adapter.write_text("import 'package:flutter/widgets.dart';")
            self.assertEqual(boundaries(root)["core_files"], 2)
            (root / "lib/app/quant/core.dart").write_text("export 'presentation/view.dart';")
            with self.assertRaisesRegex(ValueError, "adapter"):
                boundaries(root)

    def test_controlled_get_violation_fails_unified_entry(self):
        # Reentrant child verifies the injected root directly, preventing
        # recursive CLI spawning while still executing the same test suite.
        if os.environ.get("QUANT_BOUNDARY_MUTATION_CHILD") == "1":
            with self.assertRaisesRegex(ValueError, "unreviewed external package"):
                boundaries(ROOT)
            return
        # Exercise the actual CLI used by CI, beyond calling boundaries alone.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = json.loads((ROOT / "ci/quant-files.json").read_text())
            for name in list(inventory["files"]) + ["ci/quant-files.json"]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            (root / "lib/app/quant/host.dart").write_text(
                "import 'package:get/get.dart'; class Host extends GetxController {}"
            )
            command = [
                sys.executable,
                "-B",
                str(root / "tools/quant/quality.py"),
                "--local-only",
                "--report-dir",
                str(root / "report"),
            ]
            dart = shutil.which("dart")
            if dart:
                command += ["--dart", dart]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "QUANT_BOUNDARY_MUTATION_CHILD": "1"},
            )
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((root / "report/report.json").read_text())
            item = next(c for c in report["checks"] if c["name"] == "architecture-boundaries")
            self.assertEqual(item["status"], "failed")
            self.assertIn("unreviewed external package", item["error"])


class OpeningCompetition(unittest.TestCase):
    def cases(self):
        folder = ROOT / "contracts/quant/v1"
        return (
            json.loads((folder / "opening-competition.json").read_text())["cases"],
            json.loads((folder / "policy.json").read_text()),
        )

    def test_every_step_matches_frozen_hand_accounting(self):
        cases, policy = self.cases()
        self.assertEqual(
            {c["name"] for c in cases},
            {
                "market_stop_limit_resource_competition",
                "market_same_priority_submission_resource_competition",
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(opening_result(case, policy), case["expected"])

    def test_priority_and_submit_sequence_have_financial_consequences(self):
        cases, policy = self.cases()
        changed = copy.deepcopy(policy)
        changed["opening_priority"] = ["protective_stop", "market", "limit"]
        self.assertNotEqual(opening_result(cases[0], changed), cases[0]["expected"])
        changed = copy.deepcopy(cases[1])
        changed["orders"][0]["submit_seq"] = 1
        self.assertNotEqual(opening_result(changed, policy), cases[1]["expected"])
        result = opening_result(cases[0], policy)
        self.assertEqual(result["steps"][-1]["outcome"], "ignored_terminal")
        self.assertNotIn("take", [f["order_id"] for f in result["final"]["fills"]])


class PythonPublicAPI(unittest.TestCase):
    def test_declarations_wire_types_defaults_and_errors_agree(self):
        self.assertEqual(check_api(ROOT)["context_methods"], 10)

    def test_wrong_type_default_mapping_or_error_cannot_pass(self):
        for mutation in ("type", "default", "model-default", "mutable-model", "mapping", "error"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(ROOT / "contracts", root / "contracts")
                spec = root / "contracts/quant/v1/python-api.json"
                api = json.loads(spec.read_text())
                declaration = root / api["declaration"]
                source = declaration.read_text()
                if mutation == "type":
                    declaration.write_text(source.replace("cash: Decimal", "cash: float", 1))
                elif mutation == "default":
                    declaration.write_text(source.replace("limit: int = 100", "limit: int = 101"))
                elif mutation == "model-default":
                    declaration.write_text(source.replace('Decimal("0")', 'Decimal("1")', 1))
                elif mutation == "mutable-model":
                    declaration.write_text(source.replace("frozen=True", "frozen=False", 1))
                elif mutation == "mapping":
                    api["methods"]["account"]["payload"]["extra"] = "extra"
                else:
                    del api["errors"]["STOPPING"]
                spec.write_text(json.dumps(api))
                with self.assertRaises(ValueError):
                    check_api(root)


if __name__ == "__main__":
    unittest.main()
