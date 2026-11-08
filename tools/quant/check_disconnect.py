"""Required local/CI real-process disconnect gate; no installation or network."""

import argparse
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TESTS = 7


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "src"))
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_hosted_disconnect.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "scope": "POSIX real Host death, worker and ordinary-child process groups",
        "tests_run": result.testsRun,
        "expected_tests": EXPECTED_TESTS,
        "skipped": len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
    }
    complete = result.testsRun == EXPECTED_TESTS and not result.skipped and result.wasSuccessful()
    report["status"] = "passed" if complete else "failed"
    (args.report_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
