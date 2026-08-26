from __future__ import annotations

import hashlib
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.production_bundles import ProductionBundleAssembler, ProductionBundleError
from services.operator_api.provider_outputs import ProviderOutput


ROOT = Path(__file__).resolve().parents[1]


def _gateway_record(
    *,
    operation_id: str,
    evidence_id: str,
    result: dict[str, object],
) -> dict[str, object]:
    content = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return {
        "evidence_id": evidence_id,
        "logical_ref": f"runtime:agent-evidence/{evidence_id}",
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "created_at": "2026-08-25T12:00:00Z",
        "operation_binding": {"operation_id": operation_id},
        "request": {"deployment_id": "deployment-neutral"},
        "result": result,
    }


class Step1AgentEvidenceBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        content = b"{}"
        self.output = ProviderOutput(
            contract_id="https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json",
            content_bytes=content,
            content_sha256=hashlib.sha256(content).hexdigest(),
            content_type="application/json",
            tenant_id="tenant-neutral",
            project_id="project-neutral",
            run_id="run-neutral-step1",
            step_id="1",
            idempotency_key="idem-neutral-step1-evidence",
            parent_revision=1,
            target_revision=2,
            created_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        )
        self.lineage = type("Lineage", (), {"artifact": {"artifact_id": "artifact-step0-neutral"}})()
        self.project = {
            "market_deployments": [
                {
                    "deployment_id": "deployment-neutral",
                    "country_code": "DE",
                }
            ]
        }
        self.crawl = _gateway_record(
            operation_id="run_screaming_frog_crawl",
            evidence_id="evidence-crawl-neutral",
            result={
                "schema_version": "1.1.0",
                "run_id": "crawl-run-neutral",
                "deployment_id": "deployment-neutral",
                "start_url": "https://example.invalid/",
                "url_count": 1,
                "tool": {"name": "Screaming Frog SEO Spider", "version": "22.2"},
                "exports": [],
                "findings": [],
            },
        )

    def test_preserves_complete_serp_gateway_evidence_beside_crawl_evidence(self) -> None:
        serp = _gateway_record(
            operation_id="request_serp_intent_evidence",
            evidence_id="evidence-serp-neutral",
            result={
                "status": "completed",
                "complete": True,
                "provider_evidence_records": [
                    {
                        "evidence_id": "provider-evidence-serp-neutral",
                        "request_id": "request-serp-neutral",
                        "provider_id": "provider-agentseo",
                    }
                ],
            },
        )
        assembler = object.__new__(ProductionBundleAssembler)

        bundle = assembler._step1_crawl_bundle(
            self.output,
            (self.crawl, serp),
            self.lineage,
            self.project,
        )

        evidence = {item["evidence_id"]: item for item in bundle["evidence_records"]}
        self.assertEqual(
            {"evidence-crawl-neutral", "evidence-serp-neutral"},
            set(evidence),
        )
        self.assertEqual("dataset", evidence["evidence-serp-neutral"]["source_type"])
        self.assertEqual("provider-agentseo", evidence["evidence-serp-neutral"]["publisher"])
        self.assertEqual(serp["content_sha256"], evidence["evidence-serp-neutral"]["content_sha256"])

    def test_rejects_incomplete_serp_gateway_evidence(self) -> None:
        incomplete = _gateway_record(
            operation_id="request_serp_intent_evidence",
            evidence_id="evidence-serp-incomplete",
            result={"status": "failed", "complete": False, "provider_evidence_records": []},
        )
        assembler = object.__new__(ProductionBundleAssembler)

        with self.assertRaisesRegex(ProductionBundleError, "incomplete or failed"):
            assembler._step1_crawl_bundle(
                self.output,
                (self.crawl, incomplete),
                self.lineage,
                self.project,
            )


if __name__ == "__main__":
    unittest.main()
