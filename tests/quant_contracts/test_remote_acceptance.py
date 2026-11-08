"""Remote gate verdicts have the same fail-closed regressions in both repos."""

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/quant"))
from remote_acceptance import (  # noqa: E402
    REQUIRED,
    accepted_manual,
    checks_passed,
    protected,
)


class RemoteAcceptanceTests(unittest.TestCase):
    def test_unreadable_protection_is_failure(self):
        self.assertFalse(protected({"ok": False, "data": {}}, REQUIRED["desktop"]))

    def test_every_required_check_and_protection_is_needed(self):
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


if __name__ == "__main__":
    unittest.main()
