from __future__ import annotations

import hashlib
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from services.operator_api.production_bundles import ProductionBundleAssembler
from services.operator_api.provider_outputs import ProviderOutput, ProviderOutputSet


ROOT = Path(__file__).resolve().parents[1]


class ProductionBundleContractVersionTests(unittest.TestCase):
    def test_step0_gate_uses_manifest_v2_contract_identity(self) -> None:
        manifest = json.loads(
            (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("2.0.0", manifest["schema_version"])
        content = json.dumps(
            manifest,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        output = ProviderOutput(
            contract_id="https://heartweb.example/schema/manifest-v2.schema.json",
            content_bytes=content,
            content_sha256=hashlib.sha256(content).hexdigest(),
            content_type="application/json",
            tenant_id="tenant-neutral",
            project_id="project-neutral",
            run_id="run-neutral-0001",
            step_id="0",
            idempotency_key="idem-neutral-step0-contract-version",
            parent_revision=1,
            target_revision=2,
            created_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        )
        assembler = object.__new__(ProductionBundleAssembler)
        assembler.prompt_registry = json.loads(
            (ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")
        )

        context = assembler._gate_context(
            output,
            {"manifest": manifest},
            (),
            actor_id="operator-neutral",
            decided_at="2026-08-25T12:00:00Z",
        )

        evidence = context.evidence_by_gate["qg-domain-contract"]
        self.assertEqual("https://heartweb.example/schema/manifest-v2.schema.json", evidence["schema_id"])
        self.assertEqual("2.0.0", evidence["schema_version"])
        self.assertEqual(output.content_sha256, evidence["artifact_sha256"])

    def test_step0_bundle_keeps_canonical_project_v2_separate_from_manifest(self) -> None:
        manifest = json.loads(
            (ROOT / "tests/fixtures/operator/neutral-step0-manifest.json").read_text(encoding="utf-8")
        )
        project = json.loads(
            (ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8")
        )
        project["schema_version"] = "1.2.0"
        project["project_id"] = "project-neutral"
        project["tenant"]["tenant_id"] = "tenant-neutral"
        project["market_deployments"][0]["provider_location_verification"] = manifest["deployment_binding"]["provider_location_verification"]
        content = json.dumps(
            manifest,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        output = ProviderOutput(
            contract_id="https://heartweb.example/schema/manifest-v2.schema.json",
            content_bytes=content,
            content_sha256=hashlib.sha256(content).hexdigest(),
            content_type="application/json",
            tenant_id="tenant-neutral",
            project_id="project-neutral",
            run_id="run-neutral-0001",
            step_id="0",
            idempotency_key="idem-neutral-step0-project-binding",
            parent_revision=1,
            target_revision=2,
            created_at=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        )
        registry = json.loads(
            (ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8")
        )

        class RepositoryStub:
            def run(self, tenant_id: str, project_id: str, run_id: str) -> dict[str, object]:
                return {"run_id": run_id, "step_id": "0", "revision": 1, "status": "in_progress"}

            def project_v2(self, tenant_id: str, project_id: str) -> dict[str, object]:
                return project

            def intake(self, tenant_id: str, project_id: str) -> dict[str, object]:
                return {"source_sha256": "a" * 64, "reviewed": {"project_name": "National B2B", "project_v2": project}}

            def artifacts(self, tenant_id: str, project_id: str) -> list[object]:
                return []

        class GatewayEvidenceStub:
            def list_evidence(self, tenant_id: str, project_id: str, run_id: str) -> list[object]:
                return [
                    {
                        "operation_id": "prepare_kickoff_preflight",
                        "operation_binding": {
                            "operation_id": "prepare_kickoff_preflight",
                            "target_revision": 2,
                            "llm_run_request_id": "llm-request-neutral-0001",
                        },
                    }
                ]

        assembler = ProductionBundleAssembler(
            repository=RepositoryStub(),
            repository_root=ROOT,
            revisions=None,
            gateway_evidence=GatewayEvidenceStub(),
        )

        assembled = assembler.assemble(
            ProviderOutputSet.from_registry(registry, primary=output),
            llm_run_request_id="llm-request-neutral-0001",
            actor_id="operator-neutral",
            decided_at="2026-08-25T12:00:00Z",
        )

        self.assertEqual(project, assembled.bundle["project"])
        self.assertIn("market_deployments", assembled.bundle["project"])
        self.assertNotEqual(manifest, assembled.bundle["project"])


if __name__ == "__main__":
    unittest.main()
