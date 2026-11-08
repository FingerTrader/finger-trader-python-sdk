from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "quant"))

from quality import (  # noqa: E402
    boundaries,
    bundle,
    sensitive_content,
    shared_candidate,
    workflow,
)
from report_summary import validate as validate_report  # noqa: E402
from run_tests import require_complete  # noqa: E402
from workflow_spec import expected_workflow  # noqa: E402


class NegativeQualityTests(unittest.TestCase):
    def test_peer_comparison_covers_new_shared_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / role for role in ("desktop", "sdk")]
            for root in roots:
                (root / "ci").mkdir(parents=True)
                (root / "ci/quant-files.json").write_text(
                    json.dumps({"files": {"new-check.py": "hash"}})
                )
                (root / "new-check.py").write_text("same")
            self.assertEqual(shared_candidate(*roots), 1)
            (roots[1] / "new-check.py").write_text("different")
            with self.assertRaisesRegex(ValueError, "shared file mismatch"):
                shared_candidate(*roots)
            (roots[1] / "ci/quant-files.json").write_text(json.dumps({"files": {}}))
            with self.assertRaisesRegex(ValueError, "shared inventory mismatch"):
                shared_candidate(*roots)

    def test_empty_or_skipped_suite_cannot_pass(self):
        from types import SimpleNamespace

        require_complete(SimpleNamespace(testsRun=27, skipped=[], wasSuccessful=lambda: True))
        for count, skipped, success in [
            (0, [], True),
            (26, [], True),
            (27, [("test", "missing environment")], True),
            (27, [], False),
        ]:
            result = SimpleNamespace(
                testsRun=count, skipped=skipped, wasSuccessful=lambda success=success: success
            )
            with self.subTest(count=count, skipped=skipped), self.assertRaises(ValueError):
                require_complete(result)

    def test_flutter_dependency_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "lib/app/quant/host"
            core.mkdir(parents=True)
            (core / "host.dart").write_text("import 'package:flutter/widgets.dart';\n")
            with self.assertRaisesRegex(ValueError, "prohibited dependency"):
                boundaries(root)

    def test_transitive_ui_dependency_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "lib/app/quant"
            core.mkdir(parents=True)
            (core / "host.dart").write_text("export '../adapter.dart';\n")
            (root / "lib/app/adapter.dart").write_text("import 'dart:ui';\n")
            with self.assertRaisesRegex(ValueError, "prohibited dependency"):
                boundaries(root)

    def test_mutated_fixture_is_a_failure(self):
        import shutil

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "contracts", root / "contracts")
            target = root / "contracts/quant/v1/goldens.json"
            target.write_text(target.read_text().replace('"800"', '"801"', 1))
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                bundle(root)

    def test_mutated_workflow_fails_closed(self):
        for mutation in (
            "floating-action",
            "job-if",
            "step-if",
            "skip-dart",
            "paths-filter",
            "ignore-failure",
            "unfixed-python",
            "comment-only",
            "fake-run",
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target = root / ".github/workflows/quant-contracts.yml"
                target.parent.mkdir(parents=True)
                (root / "ci").mkdir()
                (root / "ci/quant-role.json").write_text('{"role":"sdk"}')
                source = expected_workflow("sdk")
                job = source["jobs"]["quant-quality"]
                if mutation == "floating-action":
                    job["steps"][0]["uses"] = "actions/checkout@main"
                elif mutation == "job-if":
                    job["if"] = "false"
                elif mutation == "step-if":
                    job["steps"][3]["if"] = "false"
                elif mutation == "skip-dart":
                    del job["steps"][2]
                elif mutation == "paths-filter":
                    source["on"]["pull_request"] = {"paths": ["docs/**"]}
                elif mutation == "ignore-failure":
                    job["continue-on-error"] = True
                elif mutation == "unfixed-python":
                    job["steps"][1]["with"]["python-version"] = "3.x"
                elif mutation == "fake-run":
                    job["steps"][3]["run"] = "echo quality.py"
                target.write_text(
                    "# pull_request: contents: read quality.py"
                    if mutation == "comment-only"
                    else json.dumps(source)
                )
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    workflow(root)

    def test_missing_own_package_import_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "lib/app/quant"
            core.mkdir(parents=True)
            (core / "host.dart").write_text("import 'package:finger_desk/missing.dart';")
            with self.assertRaisesRegex(ValueError, "missing package dependency"):
                boundaries(root)

    def test_conditional_import_ui_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "lib/app/quant"
            core.mkdir(parents=True)
            (core / "host.dart").write_text(
                "import 'safe.dart' if (dart.library.ui) 'package:flutter/widgets.dart';"
            )
            (core / "safe.dart").write_text("")
            with self.assertRaisesRegex(ValueError, "prohibited dependency"):
                boundaries(root)

    def test_report_cannot_hide_missing_or_failed_checks(self):
        names = [
            "candidate-files",
            "sensitive-content",
            "bundle-integrity",
            "architecture-boundaries",
            "protected-workflow-source",
            "contracts-and-goldens",
            "dart-shared-messages",
        ]
        valid = {
            "role": "sdk",
            "status": "passed",
            "checks": [{"name": name, "status": "passed"} for name in names],
        }
        validate_report(valid)
        import copy

        for mutation in ("missing", "duplicate", "skipped", "cancelled", "failed", "unknown-role"):
            report = copy.deepcopy(valid)
            if mutation == "missing":
                report["checks"].pop()
            elif mutation == "duplicate":
                report["checks"].append(report["checks"][0])
            elif mutation == "unknown-role":
                report["role"] = "unknown"
            else:
                report["checks"][0]["status"] = mutation
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_report(report)
        valid["role"] = "desktop"
        valid["status"] = "local-passed"
        with self.assertRaises(ValueError):
            validate_report(valid)

    def test_known_secret_cannot_enter_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ci").mkdir()
            (root / "ci/quant-files.json").write_text(
                json.dumps({"files": {"unsafe.txt": "not-used-here"}})
            )
            (root / "unsafe.txt").write_text("-----BEGIN " + "PRIVATE KEY-----")
            with self.assertRaisesRegex(ValueError, "sensitive-content"):
                sensitive_content(root)


if __name__ == "__main__":
    unittest.main()
