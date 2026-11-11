import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/quant"))

from toolchain import load, require_dart, require_flutter  # noqa: E402
from workflow_spec import check_workflow, expected_workflow  # noqa: E402


class ToolchainContract(unittest.TestCase):
    def test_exact_dart_and_flutter_required(self):
        pin = load(ROOT)
        require_dart("Dart SDK version: " + pin["dart"] + " (stable)", pin)
        with self.assertRaisesRegex(ValueError, "Pinned Dart"):
            require_dart("Dart SDK version: 3.5.1 (stable)", pin)
        version = {
            "frameworkVersion": pin["flutter"],
            "frameworkRevision": pin["framework_revision"],
            "engineRevision": pin["engine_revision"],
            "dartSdkVersion": pin["dart"],
        }
        require_flutter(version, pin)
        for field in version:
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "differs from reviewed pin"),
            ):
                require_flutter({**version, field: "wrong"}, pin)

    def test_floating_versions_and_revisions_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ci").mkdir()
            for field, value in [
                ("dart", "3.x"),
                ("flutter", "stable"),
                ("python", "3.12"),
                ("framework_revision", "8495dee"),
                ("engine_revision", "main"),
            ]:
                (root / "ci/quant-toolchain.json").write_text(
                    json.dumps({**load(ROOT), field: value})
                )
                with (
                    self.subTest(field=field),
                    self.assertRaisesRegex(ValueError, "required"),
                ):
                    load(root)

    def test_both_roles_use_shared_pin_and_reject_workflow_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ci").mkdir()
            (root / ".github/workflows").mkdir(parents=True)
            (root / "ci/quant-toolchain.json").write_bytes(
                (ROOT / "ci/quant-toolchain.json").read_bytes()
            )
            for role in ("sdk", "desktop"):
                (root / "ci/quant-role.json").write_text(json.dumps({"role": role}))
                workflow = expected_workflow(role, load(root))
                target = root / ".github/workflows/quant-contracts.yml"
                target.write_text(json.dumps(workflow))
                self.assertEqual(check_workflow(root)["dart"], load(root)["dart"])
                workflow["jobs"]["quant-quality"]["steps"][2]["with"]["sdk"] = "3.5.1"
                target.write_text(json.dumps(workflow))
                with self.assertRaisesRegex(ValueError, "workflow differs"):
                    check_workflow(root)
