"""Fail closed on absent, incomplete, or failed required reports."""

import json
import sys
from pathlib import Path


def validate(report):
    if report["role"] not in {"desktop", "sdk"}:
        raise ValueError("unknown report role")
    required = {
        "bundle-integrity",
        "architecture-boundaries",
        "protected-workflow-source",
        "contracts-and-goldens",
        "dart-shared-messages",
        "candidate-files",
        "sensitive-content",
    }
    if report["role"] == "desktop":
        required.add("peer-candidate-contracts")
    checks = report["checks"]
    names = [c["name"] for c in checks]
    if len(names) != len(set(names)) or set(names) != required:
        raise ValueError("required check set incomplete or duplicated")
    if report["status"] != "passed" or any(c["status"] != "passed" for c in checks):
        raise ValueError("required check failed")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    report = json.loads(path.read_text())
    with Path(sys.argv[2]).open("a") as stream:
        stream.write("\n```json\n" + json.dumps(report, indent=2) + "\n```\n")
    validate(report)
