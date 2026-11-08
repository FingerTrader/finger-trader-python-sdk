"""Execute the required CI entry against empty/skipped/incomplete suites."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DisconnectGate(unittest.TestCase):
    def test_entry_requires_exact_complete_unskipped_suite(self):
        for count, skipped, failed in [
            (0, False, False),
            (6, False, False),
            (7, True, False),
            (7, False, True),
            (7, False, False),
        ]:
            with self.subTest(count=count, skipped=skipped, failed=failed):
                with tempfile.TemporaryDirectory(prefix="disconnect-gate-") as name:
                    root = Path(name)
                    tools = root / "tools/quant"
                    tools.mkdir(parents=True)
                    entry = tools / "check_disconnect.py"
                    shutil.copyfile(ROOT / "tools/quant/check_disconnect.py", entry)
                    tests = root / "tests"
                    tests.mkdir()
                    source = "import unittest\nclass Fixture(unittest.TestCase):\n    pass\n"
                    for i in range(count):
                        source += "    @unittest.skip('controlled skip')\n" if skipped else ""
                        source += (
                            f"    def test_{i}(self): self.assertTrue({not (failed and i == 0)})\n"
                        )
                    (tests / "test_hosted_disconnect.py").write_text(source)
                    result = subprocess.run(
                        [sys.executable, "-B", str(entry), "--report-dir", str(root / "report")],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    accepted = count == 7 and not skipped and not failed
                    report = json.loads((root / "report/report.json").read_text())
                    self.assertEqual(result.returncode, 0 if accepted else 1)
                    self.assertEqual(report["status"], "passed" if accepted else "failed")
                    self.assertEqual(report["tests_run"], count)
