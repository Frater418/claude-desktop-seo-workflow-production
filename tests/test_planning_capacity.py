from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from services.operator_api.planning_capacity import PlanningCapacityError, PlanningCapacityService
from tests.test_provider_location_upgrade import FixedClock, PROJECT, TENANT, _project, _repository


ROOT = Path(__file__).resolve().parents[1]


def _bound_project() -> dict[str, object]:
    project = _project()
    project["schema_version"] = "1.2.0"
    project["market_deployments"][0]["provider_location_verification"] = {
        "status": "verified",
        "provider_id": "agentseo",
        "target_id": "agentseo-de-country",
        "target_type": "country",
        "location_name": "Germany",
        "provider_location_code": 2276,
        "verified_at": "2026-08-17T00:00:00Z",
        "verification_source": "provider_response",
    }
    return project


class PlanningCapacityTests(unittest.TestCase):
    def test_operator_confirmation_updates_project_intake_and_logical_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _repository(workspace, _bound_project())
            service = PlanningCapacityService(repository, ROOT)

            preview = service.preview(
                TENANT,
                PROJECT,
                minimum=10,
                maximum=10,
                actor_id="operator-heartweb-admin",
                confirmed_at=FixedClock().now(),
            )
            self.assertTrue(preview.changed)
            self.assertEqual(10, preview.capacity["min"])
            self.assertEqual(10, preview.capacity["max"])
            self.assertEqual("operator_confirmed", preview.capacity["source"])

            applied = service.apply(
                preview,
                idempotency_key="planning-capacity-test-0001",
                confirmed=True,
            )

            project = repository.project_v2(TENANT, PROJECT)
            intake = repository.intake(TENANT, PROJECT)
            logical_session = repository.logical_session(TENANT, PROJECT)
            intake_sha256 = hashlib.sha256(
                json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            self.assertEqual("1.3.0", project["schema_version"])
            self.assertEqual(preview.capacity, project["planning_capacity"])
            self.assertEqual(project, intake["reviewed"]["project_v2"])
            self.assertEqual(intake_sha256, logical_session["project_source"]["content_sha256"])
            self.assertEqual([], json.loads((workspace / "v2/operator/approvals.json").read_text(encoding="utf-8")))
            self.assertTrue(
                (workspace / "v2/operator/project-v2-upgrades" / f"{applied['upgrade_id']}.json").is_file()
            )

    def test_invalid_range_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _repository(workspace, _bound_project())
            service = PlanningCapacityService(repository, ROOT)

            with self.assertRaisesRegex(PlanningCapacityError, "ERROR_PLANNING_CAPACITY_INVALID"):
                service.preview(
                    TENANT,
                    PROJECT,
                    minimum=12,
                    maximum=10,
                    actor_id="operator-heartweb-admin",
                    confirmed_at=FixedClock().now(),
                )

            self.assertNotIn("planning_capacity", repository.project_v2(TENANT, PROJECT))


if __name__ == "__main__":
    unittest.main()
