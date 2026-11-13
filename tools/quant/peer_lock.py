"""Validate exact SDK candidate identity before emitting CI outputs."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_peer(root):
    lock = json.loads((root / "ci/quant-peer.json").read_text())
    # Only the upstream public SDK or an explicitly reviewed same-name fork.
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/fingertrader-python-sdk", lock["repository"]):
        raise ValueError("unexpected SDK repository")
    if not re.fullmatch(r"[0-9a-f]{40}", lock["commit"]):
        raise ValueError("unpublished or floating SDK candidate")
    return lock


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    lock = load_peer(ROOT)
    with args.github_output.open("a") as stream:
        stream.write("repository=" + lock["repository"] + "\ncommit=" + lock["commit"] + "\n")
