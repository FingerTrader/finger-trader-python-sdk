"""Required local/CI real-process disconnect gate; no installation or network."""

import argparse
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_NAMES = (
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
EXPECTED_TESTS = len(EXPECTED_NAMES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    os.environ["QUANT_DISCONNECT_EVIDENCE"] = str(args.report_dir.resolve() / "cases")
    sys.path.insert(0, str(ROOT / "src"))
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_hosted_disconnect.py"
    )

    def identities(tests):
        for item in tests:
            if isinstance(item, unittest.TestSuite):
                yield from identities(item)
            else:
                yield item.id().rsplit(".", 1)[-1]

    names = sorted(identities(suite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "scope": "POSIX real Host death, worker and ordinary-child process groups",
        "tests_run": result.testsRun,
        "test_names": names,
        "expected_tests": EXPECTED_TESTS,
        "skipped": len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
    }
    complete = (
        result.testsRun == EXPECTED_TESTS
        and names == sorted(EXPECTED_NAMES)
        and not result.skipped
        and result.wasSuccessful()
    )
    report["status"] = "passed" if complete else "failed"
    (args.report_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
