"""Owner-approved development P0 gate; technical failures still fail closed.

Runs fixed local candidates and reads remote evidence. Protection and independent
review remain truthful observations, not development gates. Never changes GitHub
settings, reviews, visibility, merges or releases.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
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
    "accounting",
    "confidentiality",
    "compatibility",
    "negative_merge_desktop",
    "negative_merge_sdk",
}


def get(endpoint):
    completed = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=60)
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
        required <= names
        and statuses.get("strict")
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


POLICY_ID = "owner-development-p0-2026-11-08"
TECHNICAL_REQUIREMENTS = {
    "exact_candidate_pair", "local_unified_checks", "positive_negative_regressions",
    "python_dart_contracts_and_accounting", "latest_candidate_remote_ci", "reports_versions_evidence",
}
OBSERVATIONS = {
    "github_plan", "branch_protection", "codeowners", "independent_manual_signatures",
    "protected_negative_pr",
}


def load_policy(root):
    policy = json.loads((root / "ci/quant-acceptance-policy.json").read_text())
    if (
        policy.get("id") != POLICY_ID
        or policy.get("scope") != "development-P0-only"
        or set(policy.get("required", [])) != TECHNICAL_REQUIREMENTS
        or set(policy.get("non_blocking_observations", [])) != OBSERVATIONS
        or policy.get("production_release_authorized") is not False
        or policy.get("merge_authorized") is not False
        or policy.get("approved_by") != "George (repository owner)"
    ):
        raise ValueError("unrecognized or weakened owner development policy")
    return policy


def development_verdict(repositories, fixed_pair):
    return bool(
        fixed_pair
        and set(repositories) == set(REPOSITORIES.values())
        and all(
            all(record.get(key) is True for key in (
                "checks_passed", "local_checks_passed", "candidate_identity_passed"
            ))
            for record in repositories.values()
        )
    )


def local_checks(role, checkout, sha, dart, evidence, peer=None):
    from report_summary import validate

    evidence.mkdir(parents=True, exist_ok=True)
    result = {"passed": False, "candidate": sha}
    try:
        def git(*args):
            return subprocess.check_output(
                ["git", *args], cwd=checkout, text=True, timeout=20
            ).strip()

        if git("rev-parse", "HEAD") != sha or git("status", "--porcelain"):
            raise ValueError("local candidate must be exact and clean")
        result["tree"] = git("rev-parse", "HEAD^{tree}")
        command = [sys.executable, "-B", "tools/quant/quality.py", "--dart", dart,
                   "--report-dir", str(evidence)]
        if peer is not None:
            command += ["--peer", str(peer)]
        run = subprocess.run(command, cwd=checkout, text=True, capture_output=True, timeout=180)
        (evidence / "execution.log").write_text(run.stdout + run.stderr)
        result["exit_code"] = run.returncode
        if run.returncode:
            raise ValueError("unified local checks failed")
        path = evidence / "report.json"
        report = json.loads(path.read_text())
        validate(report)
        if report["role"] != role or git("rev-parse", "HEAD") != sha or git("status", "--porcelain"):
            raise ValueError("candidate/report role changed during checks")
        result.update(passed=True, report=str(path),
                      report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        result["error"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--desktop-commit", required=True)
    parser.add_argument("--sdk-commit", required=True)
    parser.add_argument("--desktop-checkout", required=True, type=Path)
    parser.add_argument("--sdk-checkout", required=True, type=Path)
    parser.add_argument("--dart", required=True)
    parser.add_argument("--manual", type=Path, help="optional historical observation, never approval")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    policy = load_policy(root)
    commits = {"desktop": args.desktop_commit, "sdk": args.sdk_commit}
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "read_only_remote": True, "policy": policy, "candidates": commits,
        "repositories": {}, "release_scope": "development-P0-only",
    }
    directories = {"desktop": args.desktop_checkout.resolve(), "sdk": args.sdk_checkout.resolve()}
    try:
        peer = json.loads((directories["desktop"] / "ci/quant-peer.json").read_text())
        fixed_pair = peer["commit"] == commits["sdk"] and peer["repository"] == REPOSITORIES["sdk"]
    except (OSError, ValueError, KeyError):
        fixed_pair = False
    result["fixed_pair_passed"] = fixed_pair
    for role, repo in REPOSITORIES.items():
        sha = commits[role]
        exact = isinstance(sha, str) and re.fullmatch("[0-9a-f]{40}", sha)
        local = local_checks(
            role, directories[role], sha, args.dart,
            args.output.resolve().parent / (args.output.stem + "-" + role),
            directories["sdk"] if role == "desktop" else None,
        ) if exact else {"passed": False, "error": "full candidate SHA required"}
        info = get("repos/" + repo)
        protection = get("repos/" + repo + "/branches/main/protection")
        rules = get("repos/" + repo + "/rulesets")
        checks = get("repos/" + repo + "/commits/" + sha + "/check-runs?per_page=100") if exact else {
            "ok": False, "data": {"message": "exact candidate SHA required"}
        }
        commit_record = get("repos/" + repo + "/commits/" + sha) if exact else {"ok": False}
        identity = bool(commit_record["ok"] and commit_record.get("data", {}).get("sha") == sha)
        check_ok = checks_passed(checks, sha, REQUIRED[role])
        check_ok = check_ok and checks.get("data", {}).get("total_count", 0) <= 100
        protection_ok = protected(protection, REQUIRED[role])
        result["repositories"][repo] = {
            "permissions": info.get("data", {}).get("permissions", {}),
            "branch_protection": protection, "rulesets": rules,
            "candidate_checks": checks, "required_checks": sorted(REQUIRED[role]),
            "checks_passed": check_ok, "local_checks": local,
            "local_checks_passed": local["passed"], "candidate_identity_passed": identity,
            "protection_passed": protection_ok,
            "protection_status": "verified" if protection_ok else "not_configured_or_unverified",
            "protection_required_for_development": False,
        }
        print(repo, "local=" + str(local["passed"]), "candidate_checks=" + str(check_ok),
              "protected=" + str(protection_ok) + " (observation only)")
    manual = json.loads(args.manual.read_text()) if args.manual else {}
    result["manual_accepted"] = accepted_manual(manual, commits)
    result["manual_required_for_development"] = False
    result["p0_released"] = development_verdict(result["repositories"], fixed_pair)
    result["production_release_authorized"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if result["p0_released"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
