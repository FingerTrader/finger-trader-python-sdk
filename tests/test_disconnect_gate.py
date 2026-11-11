"""Execute the required CI entry against empty/skipped/incomplete suites."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "test_busy_parent_crash",
    "test_callback_error_parent_crash",
    "test_cleanup_never_signals_an_unowned_group_or_reports_success",
    "test_cleanup_rejects_unowned_group_and_permission_failure",
    "test_cleanup_tolerates_worker_and_group_exit_races",
    "test_daemon_watchdog_mutation_is_rejected",
    "test_deadline_failure_is_preserved_before_cleanup",
    "test_diagnostic_failure_does_not_mask_deadline_failure",
    "test_idle_parent_crash",
    "test_normal_stop_keeps_success_and_single_on_stop",
    "test_pending_query_parent_crash",
)


class DisconnectGate(unittest.TestCase):
    def test_entry_requires_exact_complete_unskipped_suite(self):
        for count, skipped, failed, named in [
            (0, False, False, True),
            (10, False, False, True),
            (11, True, False, True),
            (11, False, True, True),
            (11, False, False, False),
            (11, False, False, True),
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
                        method = NAMES[i] if named else f"test_{i}"
                        source += (
                            f"    def {method}(self): self.assertTrue({not (failed and i == 0)})\n"
                        )
                    (tests / "test_hosted_disconnect.py").write_text(source)
                    result = subprocess.run(
                        [sys.executable, "-B", str(entry), "--report-dir", str(root / "report")],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    accepted = count == 11 and not skipped and not failed and named
                    report = json.loads((root / "report/report.json").read_text())
                    self.assertEqual(result.returncode, 0 if accepted else 1)
                    self.assertEqual(report["status"], "passed" if accepted else "failed")
                    self.assertEqual(report["tests_run"], count)
