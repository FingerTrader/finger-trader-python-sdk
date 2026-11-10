"""Reviewed local/CI pins. No download, discovery, fallback or installation."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(root=ROOT):
    pin = json.loads((root / "ci/quant-toolchain.json").read_text())
    if (
        set(pin)
        != {
            "schema_version",
            "flutter",
            "framework_revision",
            "engine_revision",
            "dart",
            "python",
        }
        or pin["schema_version"] != 1
    ):
        raise ValueError("Invalid toolchain pin schema")
    for name in ("flutter", "dart", "python"):
        if not isinstance(pin[name], str) or not re.fullmatch(r"\d+\.\d+\.\d+", pin[name]):
            raise ValueError("Exact toolchain version required: " + name)
    for name in ("framework_revision", "engine_revision"):
        if not isinstance(pin[name], str) or not re.fullmatch(r"[a-f0-9]{40}", pin[name]):
            raise ValueError("Full toolchain revision required: " + name)
    return pin


def require_dart(version, pin=None):
    pin = pin or load()
    if not version.startswith("Dart SDK version: " + pin["dart"] + " "):
        raise ValueError("Pinned Dart " + pin["dart"] + " required, got: " + version)


def require_flutter(version, pin=None):
    pin = pin or load()
    expected = {
        "frameworkVersion": pin["flutter"],
        "frameworkRevision": pin["framework_revision"],
        "engineRevision": pin["engine_revision"],
        "dartSdkVersion": pin["dart"],
    }
    if any(version.get(name) != value for name, value in expected.items()):
        raise ValueError("Flutter/framework/engine/Dart differs from reviewed pin")


def flutter_bootstrap(pin):
    revision, version = pin["framework_revision"], pin["flutter"]
    return (
        'git init "$RUNNER_TEMP/flutter"\n'
        'git -C "$RUNNER_TEMP/flutter" remote add origin https://github.com/flutter/flutter.git\n'
        f'git -C "$RUNNER_TEMP/flutter" fetch --depth=1 origin {revision}\n'
        'git -C "$RUNNER_TEMP/flutter" fetch --depth=1 origin '
        f"refs/tags/{version}:refs/tags/{version}\n"
        f'test "$(git -C "$RUNNER_TEMP/flutter" rev-parse refs/tags/{version}^{{commit}})" '
        f'= "{revision}"\n'
        f'git -C "$RUNNER_TEMP/flutter" checkout --detach {revision}\n'
        '"$RUNNER_TEMP/flutter/bin/flutter" --version\n'
        '"$RUNNER_TEMP/flutter/bin/flutter" pub get --enforce-lockfile'
    )


def check_desktop(root):
    """Fail on pin drift, disabled jobs, weakened invocations or floating Actions."""
    from workflow_spec import CHECKOUT, DART, PYTHON

    pin = load(root)
    if json.loads((root / ".fvmrc").read_text())["flutter"] != pin["flutter"]:
        raise ValueError("FVM differs from reviewed toolchain pin")
    editor = json.loads((root / ".vscode/settings.json").read_text())
    if editor.get("dart.flutterSdkPath") != ".fvm/flutter_sdk":
        raise ValueError("Editor must use the project FVM SDK link")
    source = json.loads((root / ".github/workflows/quant-host.yml").read_text())
    if source["on"] != {
        "push": None,
        "pull_request": None,
        "workflow_dispatch": None,
        "schedule": [{"cron": "17 3 * * 1"}],
    } or source["permissions"] != {"contents": "read"}:
        raise ValueError("Host CI trigger/permissions changed")
    jobs = source["jobs"]
    if set(jobs) != {"quant-host", "quant-ui", "quant-performance"}:
        raise ValueError("Host CI jobs missing")
    commands = {
        "quant-host": (
            "Headless Host required checks",
            'python -B tools/quant/check_host.py --dart "$(command -v dart)"'
            ' --sdk "$GITHUB_WORKSPACE/peer-sdk" --python "$(command -v python)"'
            ' --report-dir "$RUNNER_TEMP/quant-host"',
        ),
        "quant-ui": (
            "Actual application panel required checks",
            'python -B tools/quant/check_ui.py --flutter "$RUNNER_TEMP/flutter/bin/flutter"'
            ' --sdk "$GITHUB_WORKSPACE/peer-sdk" --python "$(command -v python)"'
            ' --report-dir "$RUNNER_TEMP/quant-ui"',
        ),
    }
    for name, job in jobs.items():
        condition = (
            "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
            if name == "quant-performance"
            else None
        )
        if job.get("if") != condition or job.get("continue-on-error", False):
            raise ValueError("Host CI job disabled or weakened: " + name)
        steps = job["steps"]
        if len({step.get("name") for step in steps}) != len(steps):
            raise ValueError("Duplicate Host CI steps")
        by_name = {step["name"]: step for step in steps}
        for step in steps:
            if step.get("continue-on-error", False) or (
                "if" in step
                and not (step["name"].endswith(" evidence") and step["if"] == "always()")
            ):
                raise ValueError("Host CI step disabled or weakened")
            if "uses" in step and step["uses"] not in {CHECKOUT, DART, PYTHON}:
                raise ValueError("Unreviewed Host CI Action")
        expected_python = {
            "name": "Fixed Python",
            "uses": PYTHON,
            "with": {"python-version": pin["python"], "check-latest": False},
        }
        if by_name.get("Fixed Python") != expected_python:
            raise ValueError("Host CI Python pin differs")
        if name == "quant-ui":
            if by_name.get("Fixed Flutter source") != {
                "name": "Fixed Flutter source",
                "run": flutter_bootstrap(pin),
            }:
                raise ValueError("Host CI Flutter bootstrap differs")
        elif by_name.get("Fixed Dart") != {
            "name": "Fixed Dart",
            "uses": DART,
            "with": {"sdk": pin["dart"]},
        }:
            raise ValueError("Host CI Dart pin differs")
        if name in commands:
            label, command = commands[name]
            if by_name.get(label) != {"name": label, "run": command}:
                raise ValueError("Host CI required invocation differs")
    return pin
