"""Exact, reviewed P0 workflow specification (JSON is valid YAML).

Compare parsed workflow data, not textual markers. No untrusted shell inputs,
job/step conditions, path filters, or continue-on-error are accepted.
"""

import json

from toolchain import load

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
DART = "dart-lang/setup-dart@6afc89df92d6eb3834022f73cd65adc8cdfcb92d"


def expected_workflow(role, pin=None):
    pin = pin or load()
    if role not in ("desktop", "sdk"):
        raise ValueError("unknown gate role")
    steps = [
        {
            "name": "Checkout candidate",
            "uses": CHECKOUT,
            "with": {"persist-credentials": False},
        },
        {
            "name": "Fixed Python",
            "uses": PYTHON,
            "with": {"python-version": pin["python"], "check-latest": False},
        },
        {"name": "Fixed Dart", "uses": DART, "with": {"sdk": pin["dart"]}},
    ]
    if role == "desktop":
        steps += [
            {
                "name": "Local preflight (not pair acceptance)",
                "run": (
                    "python -B tools/quant/quality.py --local-only"
                    ' --dart "$(command -v dart)" --report-dir "$RUNNER_TEMP/quant-local"'
                ),
            },
            {
                "name": "Read fixed peer candidate",
                "id": "peer",
                "run": 'python -B tools/quant/peer_lock.py --github-output "$GITHUB_OUTPUT"',
            },
            {
                "name": "Checkout fixed SDK candidate",
                "uses": CHECKOUT,
                "with": {
                    "repository": "${{ steps.peer.outputs.repository }}",
                    "ref": "${{ steps.peer.outputs.commit }}",
                    "path": "peer-sdk",
                    "persist-credentials": False,
                },
            },
        ]
    args = ' --peer "$GITHUB_WORKSPACE/peer-sdk"' if role == "desktop" else ""
    steps += [
        {
            "name": "Required P0 checks",
            "run": 'python -B tools/quant/quality.py --dart "$(command -v dart)"'
            + args
            + ' --report-dir "$RUNNER_TEMP/quant-p0"',
        },
        {
            "name": "Required evidence",
            "if": "always()",
            "run": (
                'python -B tools/quant/report_summary.py "$RUNNER_TEMP/quant-p0/report.json"'
                ' "$GITHUB_STEP_SUMMARY"'
            ),
        },
    ]
    return {
        "name": "Quant contracts",
        "on": {
            "pull_request": None,
            "push": None,
            "merge_group": None,
            "workflow_dispatch": None,
        },
        "permissions": {"contents": "read"},
        "concurrency": {
            "group": "quant-${{ github.workflow }}-${{ github.ref }}",
            "cancel-in-progress": True,
        },
        "jobs": {
            "quant-quality": {
                "name": "quant-quality",
                "runs-on": "ubuntu-24.04",
                "timeout-minutes": 10,
                "steps": steps,
            }
        },
    }


def check_workflow(root):
    role = json.loads((root / "ci/quant-role.json").read_text())["role"]
    actual = json.loads((root / ".github/workflows/quant-contracts.yml").read_text())
    pin = load(root)
    if actual != expected_workflow(role, pin):
        raise ValueError("workflow differs from reviewed executable specification")
    return {
        "role": role,
        "required_status": "quant-quality",
        "dart": pin["dart"],
        "python": pin["python"],
    }
