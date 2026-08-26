from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from services.operator_api.provider_location_upgrade import (
    ProviderLocationUpgradeError,
    ProviderLocationUpgradeService,
)
from services.operator_api.repository import ProjectRepository, WorkspaceRegistration, WorkspaceRegistry


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-location-upgrade"
PROJECT = "project-location-upgrade"
RUN = "run-location-upgrade-0001"


class FixedClock:
    def now(self) -> str:
        return "2026-08-25T18:00:00Z"


def _write(workspace: Path, relative: str, value: object) -> None:
    path = workspace / "v2/operator" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _project() -> dict[str, object]:
    project = json.loads(
        (ROOT / "tests/fixtures/domain/real-customer-matrix/national-b2b.json").read_text(encoding="utf-8")
    )
    project["project_id"] = PROJECT
    project["tenant"]["tenant_id"] = TENANT
    project["market_deployments"][0]["target_regions"] = ["Germany", "Berlin", "Hamburg"]
    return project


def _repository(workspace: Path, project: dict[str, object]) -> ProjectRepository:
    intake = {
        "tenant_id": TENANT,
        "project_id": PROJECT,
        "source_sha256": "a" * 64,
        "reviewed": {"project_name": "National B2B", "project_v2": project},
        "accepted_by": "operator-test",
        "accepted_at": "2026-08-25T12:00:00Z",
    }
    _write(workspace, "project.json", {"tenant_id": TENANT, "project_id": PROJECT, "name": "National B2B"})
    _write(workspace, "project-v2.json", project)
    _write(workspace, "intake.json", intake)
    intake_sha256 = hashlib.sha256(
        json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    _write(
        workspace,
        "logical-session.json",
        {
            "logical_session_id": "logical-session-location-upgrade-0001",
            "schema_version": "1.0.0",
            "session_revision": 1,
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "binding_mode": "project_intake",
            "project_source": {
                "source_kind": "project_intake",
                "source_id": f"intake-{intake_sha256[:12]}",
                "revision": 1,
                "logical_ref": f"runtime:intake/intake-{intake_sha256[:12]}",
                "content_sha256": intake_sha256,
            },
            "created_at": "2026-08-25T12:00:00Z",
            "created_by": "operator-test",
            "state_authority": "local_core",
            "technical_session_policy": {
                "default_execution": "fresh_per_step_or_substantial_revision",
                "reuse_allowed": True,
                "reuse_authority": "cache_only",
                "lost_handle_recovery": "rebuild_from_context_package",
            },
        },
    )
    _write(
        workspace,
        f"runs/{RUN}.json",
        {
            "tenant_id": TENANT,
            "project_id": PROJECT,
            "run_id": RUN,
            "step_id": "0",
            "revision": 1,
            "input_hash": "b" * 64,
            "status": "awaiting_gate",
        },
    )
    _write(workspace, "approvals.json", [])
    return ProjectRepository(WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),)))


class ProviderLocationUpgradeTests(unittest.TestCase):
    def test_preview_and_apply_bind_all_briefing_regions_without_touching_gate_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _repository(workspace, _project())
            service = ProviderLocationUpgradeService(repository, ROOT, FixedClock())

            preview = service.preview(TENANT, PROJECT)

            self.assertTrue(preview.changed)
            self.assertTrue(preview.logical_source_stale)
            self.assertEqual("agentseo-de-country", preview.deployment_bindings[0]["provider_target_id"])
            self.assertEqual(2276, preview.deployment_bindings[0]["provider_location_code"])
            self.assertEqual(["Germany", "Berlin", "Hamburg"], preview.deployment_bindings[0]["target_regions"])

            applied = service.apply(
                TENANT,
                PROJECT,
                preview_hash=preview.preview_hash,
                expected_project_sha256=preview.current_project_sha256,
                actor_id="operator-test",
                idempotency_key="location-upgrade-test-0001",
                confirmed=True,
            )

            project = repository.project_v2(TENANT, PROJECT)
            intake = repository.intake(TENANT, PROJECT)
            logical_session = repository.logical_session(TENANT, PROJECT)
            run = repository.run(TENANT, PROJECT, RUN)
            verification = project["market_deployments"][0]["provider_location_verification"]
            self.assertEqual("1.2.0", project["schema_version"])
            self.assertEqual("verified", verification["status"])
            self.assertEqual(2276, verification["provider_location_code"])
            self.assertEqual(project, intake["reviewed"]["project_v2"])
            self.assertEqual(2, logical_session["session_revision"])
            self.assertEqual(
                hashlib.sha256(
                    json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                logical_session["project_source"]["content_sha256"],
            )
            self.assertEqual(
                "logical-session-location-upgrade-0001",
                logical_session["supersedes_logical_session_id"],
            )
            self.assertEqual("dep-national-b2b-de", run["deployment_id"])
            self.assertEqual([], json.loads((workspace / "v2/operator/approvals.json").read_text(encoding="utf-8")))
            self.assertTrue((workspace / "v2/operator/project-v2-upgrades" / f"{applied['upgrade_id']}.json").is_file())
            self.assertTrue(
                (
                    workspace
                    / "v2/operator/logical-session-history/logical-session-location-upgrade-0001-r1.json"
                ).is_file()
            )
            self.assertFalse(service.preview(TENANT, PROJECT).changed)

    def test_local_deployment_without_exact_city_target_fails_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project = _project()
            deployment = project["market_deployments"][0]
            deployment["seo_operating_model"] = "local"
            deployment["target_regions"] = ["Frankfurt am Main"]
            repository = _repository(workspace, project)
            service = ProviderLocationUpgradeService(repository, ROOT, FixedClock())

            with self.assertRaisesRegex(ProviderLocationUpgradeError, "ERROR_PROVIDER_LOCATION_TARGET_REQUIRED"):
                service.preview(TENANT, PROJECT)

            self.assertEqual("1.1.0", repository.project_v2(TENANT, PROJECT)["schema_version"])

    def test_unverified_country_target_fails_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project = _project()
            deployment = project["market_deployments"][0]
            deployment.update(
                {
                    "market_id": "de-at-austria",
                    "country_code": "AT",
                    "legal_jurisdiction": "AT",
                    "locale": "de-AT",
                    "target_regions": ["Austria"],
                }
            )
            repository = _repository(workspace, project)
            service = ProviderLocationUpgradeService(repository, ROOT, FixedClock())

            with self.assertRaisesRegex(ProviderLocationUpgradeError, "ERROR_PROVIDER_LOCATION_TARGET_REQUIRED"):
                service.preview(TENANT, PROJECT)

            self.assertIsNone(
                repository.project_v2(TENANT, PROJECT)["market_deployments"][0]["provider_location_verification"]["provider_location_code"]
            )


if __name__ == "__main__":
    unittest.main()
