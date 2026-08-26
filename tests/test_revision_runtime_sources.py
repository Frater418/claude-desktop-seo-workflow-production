from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from services.operator_api.runtime import _runtime_sources
from tests.test_local_runtime import PROJECT, RUN, TENANT, _seed, _write


class RevisionRuntimeSourceTests(unittest.TestCase):
    def test_current_quality_gate_is_an_active_revision_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = _seed(workspace, "0")
            artifact_id = "artifact-revision-source-0001"
            content = b"rejected candidate"
            content_sha256 = hashlib.sha256(content).hexdigest()
            content_path = workspace / "v2/operator/artifact-content" / f"{artifact_id}.md"
            content_path.parent.mkdir(parents=True, exist_ok=True)
            content_path.write_bytes(content)
            _write(
                workspace,
                "artifacts.json",
                [
                    {
                        "artifact_id": artifact_id,
                        "tenant_id": TENANT,
                        "project_id": PROJECT,
                        "run_id": RUN,
                        "step_id": "0",
                        "revision": 1,
                        "content_sha256": content_sha256,
                    }
                ],
            )
            _write(
                workspace,
                "gates.json",
                [
                    {
                        "quality_gate_run_id": "qgr-revision-source-0001",
                        "quality_gate_id": "qg-domain-contract",
                        "tenant_id": TENANT,
                        "project_id": PROJECT,
                        "run_id": RUN,
                        "step_id": "0",
                        "artifact_id": artifact_id,
                        "artifact_revision": 1,
                        "artifact_sha256": content_sha256,
                        "result": "passed",
                    }
                ],
            )
            revision_request_id = "revision-request-source-0001"
            steering_id = "steering-source-0001"
            repository.write_operator_record(
                TENANT,
                PROJECT,
                "revision-request",
                {
                    "revision_request_id": revision_request_id,
                    "tenant_id": TENANT,
                    "project_id": PROJECT,
                    "run_id": RUN,
                    "step_id": "0",
                },
            )
            repository.write_operator_record(
                TENANT,
                PROJECT,
                "production-steering",
                {
                    "steering_id": steering_id,
                    "tenant_id": TENANT,
                    "project_id": PROJECT,
                    "run_id": RUN,
                    "step_id": "0",
                },
            )
            source_bytes: dict[str, bytes] = {}

            sources, _, _, _ = _runtime_sources(
                repository,
                {
                    "tenant_id": TENANT,
                    "project_id": PROJECT,
                    "run_id": RUN,
                    "step_id": "0",
                    "trigger": "revision",
                    "revision_request_id": revision_request_id,
                    "steering_id": steering_id,
                    "steering_logical_ref": f"operator:steering/{steering_id}",
                    "rejected_artifact_id": artifact_id,
                    "rejected_artifact_sha256": content_sha256,
                },
                source_bytes,
            )

            quality_gate = next(source for source in sources if source["source_kind"] == "quality_gate_run")
            self.assertEqual("active", quality_gate["source_status"])
            self.assertEqual("trusted", quality_gate["trust_level"])
            self.assertIn(quality_gate["logical_ref"], source_bytes)


if __name__ == "__main__":
    unittest.main()
