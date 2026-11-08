"""Remote gate verdicts have the same fail-closed regressions in both repos."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/quant"))
from remote_acceptance import (  # noqa: E402
    REQUIRED,
    accepted_manual,
    checks_passed,
    development_verdict,
    load_policy,
    local_checks,
    protected,
)


class RemoteAcceptanceTests(unittest.TestCase):
    def test_unreadable_protection_is_failure(self):
        self.assertFalse(protected({"ok": False, "data": {}}, REQUIRED["desktop"]))

    def test_protection_observation_requires_actual_settings(self):
        record = {
            "ok": True,
            "data": {
                "required_status_checks": {"strict": True, "contexts": sorted(REQUIRED["sdk"])},
                "enforce_admins": {"enabled": True},
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "require_code_owner_reviews": True,
                    "dismiss_stale_reviews": True,
                },
            },
        }
        self.assertTrue(protected(record, REQUIRED["sdk"]))
        for key in ("enforce_admins", "required_pull_request_reviews", "required_status_checks"):
            invalid = copy.deepcopy(record)
            del invalid["data"][key]
            self.assertFalse(protected(invalid, REQUIRED["sdk"]))
        invalid = copy.deepcopy(record)
        invalid["data"]["required_status_checks"]["contexts"] = ["quant-quality"]
        self.assertFalse(protected(invalid, REQUIRED["sdk"]))

    def test_exact_candidate_latest_check_cannot_hide_failure(self):
        sha = "a" * 40
        rows = [
            {
                "id": i,
                "name": name,
                "head_sha": sha,
                "app": {"slug": "github-actions"},
                "status": "completed",
                "conclusion": "success",
            }
            for i, name in enumerate(sorted(REQUIRED["sdk"]))
        ]
        payload = {"ok": True, "data": {"check_runs": rows}}
        self.assertTrue(checks_passed(payload, sha, REQUIRED["sdk"]))
        self.assertFalse(checks_passed(payload, "b" * 40, REQUIRED["sdk"]))
        self.assertFalse(checks_passed(payload, sha, REQUIRED["sdk"] | {"missing"}))
        for conclusion in ("skipped", "neutral", "cancelled", "failure", None):
            invalid = copy.deepcopy(payload)
            newer = {**rows[0], "id": 100, "conclusion": conclusion}
            invalid["data"]["check_runs"].append(newer)
            self.assertFalse(checks_passed(invalid, sha, REQUIRED["sdk"]))
        invalid = copy.deepcopy(payload)
        invalid["data"]["check_runs"][0]["app"]["slug"] = "other-app"
        self.assertFalse(checks_passed(invalid, sha, REQUIRED["sdk"]))

    def test_human_evidence_must_identify_fixed_pair(self):
        commits = {"desktop": "a" * 40, "sdk": "b" * 40}
        self.assertFalse(accepted_manual({}, commits))
        from remote_acceptance import MANUAL_ITEMS

        record = {
            "status": "approved",
            "candidates": commits,
            "reviews": {
                name: {
                    "decision": "approved",
                    "reviewer": "fixture-reviewer",
                    "reviewed_at": "2026-01-01T00:00:00Z",
                    "evidence": "fixture-only",
                }
                for name in MANUAL_ITEMS
            },
        }
        self.assertTrue(accepted_manual(record, commits))
        self.assertFalse(accepted_manual(record, {**commits, "sdk": "c" * 40}))
        invalid = copy.deepcopy(record)
        invalid["reviews"]["accounting"]["reviewed_at"] = "invalid"
        self.assertFalse(accepted_manual(invalid, commits))

    def test_owner_policy_keeps_all_technical_requirements(self):
        self.assertEqual(load_policy(ROOT)["scope"], "development-P0-only")
        for field in ("required", "non_blocking_observations", "scope", "approved_by"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "ci/quant-acceptance-policy.json"
                path.parent.mkdir()
                record = json.loads((ROOT / "ci/quant-acceptance-policy.json").read_text())
                record[field] = [] if isinstance(record[field], list) else "unknown"
                path.write_text(json.dumps(record))
                with self.assertRaises(ValueError):
                    load_policy(Path(tmp))

    def test_development_release_ignores_protection_without_faking_it(self):
        records = {
            repo: {"checks_passed": True, "local_checks_passed": True,
                   "candidate_identity_passed": True, "protection_passed": False}
            for repo in ("finger-cloud/finger_desk", "FingerTrader/finger-trader-python-sdk")
        }
        self.assertTrue(development_verdict(records, True))
        self.assertTrue(all(r["protection_passed"] is False for r in records.values()))
        self.assertFalse(development_verdict(records, False))
        for repo in records:
            for field in ("checks_passed", "local_checks_passed", "candidate_identity_passed"):
                for value in (False, None, "passed"):
                    invalid = copy.deepcopy(records)
                    invalid[repo][field] = value
                    self.assertFalse(development_verdict(invalid, True))
        self.assertFalse(development_verdict({}, True))

    def test_dirty_or_wrong_local_candidate_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            for git_outputs in (["b" * 40], ["a" * 40, " M source.py"]):
                with patch("subprocess.check_output", side_effect=git_outputs):
                    result = local_checks("sdk", Path(tmp), "a" * 40, "dart", Path(tmp) / "evidence")
                self.assertFalse(result["passed"])

    def test_failed_unified_entry_cannot_pass_development_gate(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            with patch("subprocess.check_output", side_effect=["a" * 40, "", "tree"]):
                with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, "FAILED", "")):
                    result = local_checks("sdk", Path(tmp), "a" * 40, "dart", Path(tmp) / "evidence")
            self.assertFalse(result["passed"])
            self.assertEqual(result["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
