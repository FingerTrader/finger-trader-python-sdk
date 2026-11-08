#!/usr/bin/env python3
"""Single local/CI entry point for the implemented P0 quality checks.

Standard library only. No installation, network, credentials, or live accounts.
Missing requested tools fail; checks never convert missing environments to PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED_FILES = [
    "contracts/quant/v1/bundle.lock.json",
    "lib/app/quant/contracts/schema_validator.dart",
    "lib/app/quant/contracts/strict_json.dart",
    "tools/quant/check_contracts.dart",
    "tools/quant/contract_check.py",
    "tools/quant/quality.py",
    "tools/quant/workflow_spec.py",
    "tools/quant/report_summary.py",
    "tools/quant/run_tests.py",
    "tools/quant/peer_lock.py",
    "tests/quant_contracts/test_contracts.py",
    "tests/quant_contracts/test_quality.py",
]


def boundaries(root):
    root = root.resolve()
    failures = []
    core = root / "lib" / "app" / "quant"
    visited = set()

    def visit(path):
        path = path.resolve()
        if path in visited:
            return
        visited.add(path)
        source = path.read_text(encoding="utf-8")
        directives = re.findall(r"\b(?:import|export|part)\s+['\"][^;]+;", source, re.DOTALL)
        uris = [
            uri for directive in directives for uri in re.findall(r"['\"]([^'\"]+)['\"]", directive)
        ]
        for uri in uris:
            if uri.startswith(
                (
                    "package:flutter/",
                    "dart:ui",
                    "package:finger_desk/app/modules/",
                    "package:finger_desk/app/widgets/",
                )
            ):
                failures.append(f"{path.relative_to(root)}: prohibited dependency {uri}")
            elif uri.startswith("package:finger_desk/"):
                destination = root / "lib" / uri.removeprefix("package:finger_desk/")
                if destination.is_file():
                    visit(destination)
                else:
                    failures.append(f"missing package dependency {uri}")
            elif not uri.startswith(("package:", "dart:")):
                destination = path.parent / uri
                if not destination.is_file():
                    failures.append(f"{path.relative_to(root)}: missing internal dependency {uri}")
                else:
                    try:
                        destination.resolve().relative_to(root.resolve())
                    except ValueError:
                        failures.append(f"{path}: dependency escapes repository")
                    else:
                        visit(destination)

    for path in core.rglob("*.dart"):
        visit(path)
    if (root / ".fvmrc").is_file() and not visited:
        failures.append("Desktop quant core is missing; cannot pass an empty architecture check")
    if failures:
        raise ValueError("\n".join(failures))
    return {"core_files": len(list(core.rglob("*.dart"))), "transitive_files": len(visited)}


def bundle(root):
    directory = root / "contracts" / "quant" / "v1"
    lock = json.loads((directory / "bundle.lock.json").read_text())
    actual_files = {p.name for p in directory.iterdir() if p.is_file()} - {"bundle.lock.json"}
    if actual_files != set(lock["files"]):
        raise ValueError("bundle file inventory does not match lock")
    for name, expected in lock["files"].items():
        if Path(name).name != name:
            raise ValueError("invalid bundle path")
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(
                f"bundle digest mismatch: {name}; review schema/model impact before updating lock"
            )
    return {"bundle_version": lock["bundle_version"], "files": len(actual_files)}


def workflow(root):
    from workflow_spec import check_workflow

    return check_workflow(root)


def candidate_files(root):
    root = root.resolve()
    manifest = json.loads((root / "ci/quant-files.json").read_text())
    if not manifest["files"] or len(manifest["files"]) < 10:
        raise ValueError("candidate inventory incomplete")
    for relative, expected in manifest["files"].items():
        path = root / relative
        if path.is_symlink() or path.resolve() != path.absolute() or ".." in Path(relative).parts:
            raise ValueError("unsafe candidate path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"candidate code digest mismatch: {relative}")
    return {"files": len(manifest["files"])}


def sensitive_content(root):
    """Known-secret pattern check only; provenance still needs human review."""
    manifest = json.loads((root / "ci/quant-files.json").read_text())
    patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    ]
    for relative in manifest["files"]:
        source = (root / relative).read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in patterns):
            raise ValueError("known sensitive-content pattern in " + relative)
    return {"scope": "candidate text only; not complete confidentiality assurance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dart", help="explicit pinned Dart executable; missing executable fails")
    parser.add_argument(
        "--peer", type=Path, help="check identical candidate contract bundle in peer checkout"
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="diagnostic preflight only; cannot satisfy required CI report",
    )
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    report_dir = args.report_dir or Path(tempfile.mkdtemp(prefix="finger-quant-p0-"))
    report_dir.mkdir(parents=True, exist_ok=True)
    role = json.loads((ROOT / "ci/quant-role.json").read_text())["role"]
    if role not in {"desktop", "sdk"}:
        raise ValueError("unknown role")
    report = {
        "role": role,
        "scope": "P0 contract checks only; not P1/P3 or release acceptance",
        "python": sys.version,
        "checks": [],
        "pending_gates": [
            "remote_required_checks",
            "remote_branch_protection",
            "remote_negative_merge_test",
            "P1_process",
            "P3_engine",
            "P4_native_install",
        ],
    }

    def run(name, function):
        started = time.monotonic()
        try:
            details = function()
            item = {"name": name, "status": "passed", "details": details}
        except Exception as exc:
            item = {"name": name, "status": "failed", "error": str(exc)}
        item["elapsed_seconds"] = round(time.monotonic() - started, 4)
        report["checks"].append(item)
        print(f"{item['status'].upper()} {name}", flush=True)
        if "error" in item:
            print(item["error"], file=sys.stderr)

    def command(argv, name, environment=None):
        completed = subprocess.run(
            argv, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=120
        )
        (report_dir / f"{name}.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        print(completed.stdout + completed.stderr, end="", flush=True)
        if completed.returncode:
            raise ValueError(f"exit {completed.returncode}; see {name}.log")
        return {"command": argv, "exit_code": completed.returncode}

    run("candidate-files", lambda: candidate_files(ROOT))
    run("sensitive-content", lambda: sensitive_content(ROOT))
    run("bundle-integrity", lambda: bundle(ROOT))
    run("architecture-boundaries", lambda: boundaries(ROOT))
    run("protected-workflow-source", lambda: workflow(ROOT))
    run(
        "contracts-and-goldens",
        lambda: command([sys.executable, "-B", "tools/quant/run_tests.py"], "contracts"),
    )

    def dart_check():
        if not args.dart:
            raise ValueError("Dart is mandatory for P0; provide --dart pinned-executable")
        executable = str(Path(args.dart).resolve())
        version = subprocess.check_output(
            [executable, "--version"], text=True, stderr=subprocess.STDOUT
        )
        if "Dart SDK version: 3.5.1 " not in version:
            raise ValueError("Dart 3.5.1 required, got: " + version)
        return command([executable, "tools/quant/check_contracts.dart"], "dart")

    run("dart-shared-messages", dart_check)
    if role == "desktop" and not args.local_only:

        def peer():
            from peer_lock import load_peer

            if args.peer is None:
                raise ValueError("fixed SDK candidate required: --peer")
            lock = load_peer(ROOT)
            commit = subprocess.check_output(
                ["git", "-C", str(args.peer), "rev-parse", "HEAD"], text=True
            ).strip()
            if commit != lock["commit"]:
                raise ValueError("SDK candidate commit mismatch")
            bundle(args.peer)
            candidate_files(args.peer)
            for relative in SHARED_FILES:
                if (ROOT / relative).read_bytes() != (args.peer / relative).read_bytes():
                    raise ValueError("candidate shared file mismatch: " + relative)
            return {
                "candidate_bundle": "identical",
                "peer_commit": commit,
                "repository": lock["repository"],
            }

        run("peer-candidate-contracts", peer)
    report["status"] = (
        "passed" if all(item["status"] == "passed" for item in report["checks"]) else "failed"
    )
    if args.local_only and report["status"] == "passed":
        report["status"] = "local-passed"
    report_file = report_dir / "report.json"
    report_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Report: {report_file}")
    return 0 if report["status"] in {"passed", "local-passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
