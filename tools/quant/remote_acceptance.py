"""Read-only P0 acceptance audit; absent remote or human evidence fails closed.

This is an evidence collector, not a replacement for protected human review.
It never changes repository settings, account data, or reviews.
"""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPOSITORIES = {
    "desktop": "finger-cloud/finger_desk",
    "sdk": "FingerTrader/finger-trader-python-sdk",
}
SDK_TESTS = {f"test ({version})" for version in ("3.10", "3.11", "3.12", "3.13", "3.14")}
REQUIRED = {
    "desktop": {"quant-quality"},
    "sdk": {"quant-quality", "dependency-audit", "secrets"} | SDK_TESTS,
}
MANUAL_ITEMS = {
    "accounting", "confidentiality", "compatibility",
    "negative_merge_desktop", "negative_merge_sdk",
}


def get(endpoint):
    completed = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, text=True, timeout=60
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        data = {"message": completed.stderr.strip()}
    return {"ok": completed.returncode == 0, "data": data}


def protected(payload, required):
    if not payload["ok"]:
        return False
    record = payload["data"]
    statuses = record.get("required_status_checks") or {}
    names = set(statuses.get("contexts", [])) | {
        row["context"] for row in statuses.get("checks", [])
    }
    reviews = record.get("required_pull_request_reviews") or {}
    return bool(
        required <= names and statuses.get("strict")
        and record.get("enforce_admins", {}).get("enabled")
        and reviews.get("required_approving_review_count", 0) >= 1
        and reviews.get("require_code_owner_reviews")
        and reviews.get("dismiss_stale_reviews")
        and not record.get("allow_force_pushes", {}).get("enabled")
        and not record.get("allow_deletions", {}).get("enabled")
        and not any(reviews.get("bypass_pull_request_allowances", {}).values())
    )


def checks_passed(payload, sha, required):
    if not payload["ok"] or not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{40}", sha):
        return False
    latest = {}
    for row in payload["data"].get("check_runs", []):
        if row.get("app", {}).get("slug") != "github-actions" or row.get("head_sha") != sha:
            continue
        name = row.get("name")
        if name not in latest or row["id"] > latest[name]["id"]:
            latest[name] = row
    return required <= latest.keys() and all(
        latest[name]["status"] == "completed" and latest[name]["conclusion"] == "success"
        for name in required
    )


def accepted_manual(record, commits):
    if record.get("status") != "approved":
        return False
    if not all(
        isinstance(sha, str) and re.fullmatch("[0-9a-f]{40}", sha) for sha in commits.values()
    ):
        return False
    if record.get("candidates") != commits or set(record.get("reviews", {})) != MANUAL_ITEMS:
        return False
    for review in record["reviews"].values():
        if review.get("decision") != "approved":
            return False
        if not all(
            isinstance(review.get(key), str) and review[key].strip()
            for key in ("reviewer", "reviewed_at", "evidence")
        ):
            return False
        try:
            when = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
        except ValueError:
            return False
        if when.tzinfo is None or when > datetime.now(timezone.utc):
            return False
    # Human attestations must also be reviewed through protected changes.
    # A populated JSON file alone cannot prove that a human approved it.
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--desktop-commit", required=True)
    parser.add_argument("--sdk-commit", required=True)
    parser.add_argument("--manual", required=True, type=Path)
    args = parser.parse_args()
    commits = {"desktop": args.desktop_commit, "sdk": args.sdk_commit}
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True, "candidates": commits, "repositories": {},
    }
    remote_ok = True
    for role, repo in REPOSITORIES.items():
        info = get("repos/" + repo)
        protection = get("repos/" + repo + "/branches/main/protection")
        rules = get("repos/" + repo + "/rulesets")
        sha = commits[role]
        if re.fullmatch("[0-9a-f]{40}", sha):
            checks = get("repos/" + repo + "/commits/" + sha + "/check-runs?per_page=100")
        else:
            checks = {"ok": False, "data": {"message": "exact candidate SHA required"}}
        check_ok = checks_passed(checks, sha, REQUIRED[role])
        # Fail closed if the API response is truncated. Larger histories need
        # an explicitly paginated collector before they can be accepted.
        check_ok = check_ok and checks.get("data", {}).get("total_count", 0) <= 100
        protection_ok = protected(protection, REQUIRED[role])
        remote_ok = remote_ok and check_ok and protection_ok
        result["repositories"][repo] = {
            "permissions": info.get("data", {}).get("permissions", {}),
            "branch_protection": protection, "rulesets": rules,
            "candidate_checks": checks, "required_checks": sorted(REQUIRED[role]),
            "checks_passed": check_ok, "protection_passed": protection_ok,
        }
        print(repo, "candidate_checks=" + str(check_ok), "protected=" + str(protection_ok))
    manual = json.loads(args.manual.read_text())
    result["manual_accepted"] = accepted_manual(manual, commits)
    result["p0_released"] = bool(remote_ok and result["manual_accepted"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if result["p0_released"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
