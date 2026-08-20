"""Tests for crawl disposition and waiver policy.

Autor: Raphael Rechberger
"""

from __future__ import annotations

import unittest

from services.quality_gate_runner.disposition import evaluate_crawl_disposition, load_policy


class CrawlDispositionTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()
        self.artifact = {
            "artifact_id": "artifact-crawl-0001",
            "content_sha256": "a" * 64,
        }
        self.waiver = {
            "waiver_id": "waiver-resource-0001",
            "quality_gate_id": "qg-step1-crawl-snapshot",
            "artifact_id": "artifact-crawl-0001",
            "artifact_sha256": "a" * 64,
            "policy_id": "heartweb-crawl-disposition",
            "policy_version": "1.0.0",
            "step_ids": ["1"],
            "finding_keys": ["resource_4xx"],
            "approved_at": "2026-08-19T05:00:00Z",
            "expires_at": "2026-08-20T05:00:00Z",
        }

    def test_resource_404_requires_waiver_in_step1(self):
        result = evaluate_crawl_disposition({"resource_4xx": 1}, "1", policy=self.policy)
        self.assertEqual("blocked", result["result"])
        self.assertEqual("resource_4xx", result["waiver_required_findings"][0]["finding_key"])

    def test_matching_waiver_allows_step1_with_warning(self):
        result = evaluate_crawl_disposition(
            {"resource_4xx": 1},
            "1",
            policy=self.policy,
            waivers=[self.waiver],
            artifact=self.artifact,
            as_of="2026-08-19T06:00:00Z",
        )
        self.assertEqual("passed_with_warnings", result["result"])
        self.assertEqual(["waiver-resource-0001"], result["waiver_ids"])

    def test_resource_404_remains_blocking_in_step4b(self):
        result = evaluate_crawl_disposition(
            {"resource_4xx": 1},
            "4b",
            policy=self.policy,
            waivers=[self.waiver],
            artifact=self.artifact,
            as_of="2026-08-19T06:00:00Z",
        )
        self.assertEqual("blocked", result["result"])
        self.assertEqual("resource_4xx", result["blocking_findings"][0]["finding_key"])

    def test_server_error_cannot_be_waived(self):
        result = evaluate_crawl_disposition(
            {"status_5xx": 1},
            "1",
            policy=self.policy,
            waivers=[self.waiver],
            artifact=self.artifact,
            as_of="2026-08-19T06:00:00Z",
        )
        self.assertEqual("blocked", result["result"])
        self.assertEqual("status_5xx", result["blocking_findings"][0]["finding_key"])

    def test_expired_or_hash_mismatched_waiver_is_rejected(self):
        expired = dict(self.waiver, expires_at="2026-08-19T05:30:00Z")
        wrong_hash = dict(self.waiver, artifact_sha256="b" * 64)
        for waiver in (expired, wrong_hash):
            result = evaluate_crawl_disposition(
                {"resource_4xx": 1},
                "1",
                policy=self.policy,
                waivers=[waiver],
                artifact=self.artifact,
                as_of="2026-08-19T06:00:00Z",
            )
            self.assertEqual("blocked", result["result"])

    def test_hreflang_rule_only_applies_when_multilingual(self):
        mono = evaluate_crawl_disposition({"hreflang_issues": 2}, "4b", policy=self.policy, context={"multilingual": False})
        multi = evaluate_crawl_disposition({"hreflang_issues": 2}, "4b", policy=self.policy, context={"multilingual": True})
        self.assertEqual("passed", mono["result"])
        self.assertEqual("blocked", multi["result"])


if __name__ == "__main__":
    unittest.main()
