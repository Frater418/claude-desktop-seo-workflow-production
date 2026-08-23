from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from services.delivery.inventory import collect_inventory
from services.operator_api.delivery_repository import DeliverySnapshotRepository
from services.operator_api.provisioning import ProvisionedWorkspaceResolver
from services.operator_api.repository import ProjectRepository
from services.operator_api.repository_types import RepositoryError, WorkspaceRegistration, WorkspaceRegistry
from tests.support.delivery_api import PROJECT, TENANT, seed_workspace, workspace_snapshot


class DeliverySnapshotRepositoryTests(unittest.TestCase):
    def repository(self, workspace: Path) -> ProjectRepository:
        registry = WorkspaceRegistry((WorkspaceRegistration(TENANT, PROJECT, workspace),))
        return ProjectRepository(registry)

    def test_snapshot_binds_canonical_records_content_and_inventory_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            seed_workspace(workspace)
            before = workspace_snapshot(workspace, include_delivery=True)

            snapshot = self.repository(workspace).delivery_snapshot(TENANT, PROJECT)

            inventory = collect_inventory(snapshot.inventory_request())
            self.assertEqual(TENANT, snapshot.workspace.tenant_id)
            self.assertEqual(PROJECT, snapshot.workspace.project_id)
            self.assertEqual(8, len(snapshot.records.runs))
            self.assertEqual(7, len(snapshot.selected_files))
            self.assertEqual(
                (
                    "strategy/artifact-strategy-0001.md",
                    "architecture/artifact-architecture-0001.md",
                    "design/artifact-design-0001.md",
                    "keyword-research/artifact-keyword-research-0001.md",
                    "roadmap/artifact-roadmap-0001.md",
                    "copywriter-handoff/artifact-copywriter-handoff-0001.md",
                    "developer-handoff/artifact-developer-handoff-0001.md",
                ),
                tuple(item.output_path for item in snapshot.selected_files),
            )
            self.assertEqual(7, len(snapshot.artifact_contents))
            self.assertEqual(7, len(inventory.files))
            with self.assertRaises(TypeError):
                snapshot.records.artifacts[0]["artifact_id"] = "artifact-mutated-0001"
            self.assertEqual(before, workspace_snapshot(workspace, include_delivery=True))

    def test_snapshot_rejects_malformed_optional_projection_and_artifact_hash_mismatch(self) -> None:
        cases = ("reviews", "artifact")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                root = workspace / "v2" / "operator"
                if case == "reviews":
                    (root / "reviews.json").write_text("{}", encoding="utf-8")
                else:
                    artifact = root / "artifact-content" / "artifact-strategy-0001.md"
                    artifact.write_bytes(b"tampered")

                with self.assertRaisesRegex(RepositoryError, "Canonical delivery"):
                    self.repository(workspace).delivery_snapshot(TENANT, PROJECT)

    def test_snapshot_rejects_cross_tenant_records_and_artifact_content_links(self) -> None:
        cases = ("cross-tenant", "link")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                seed_workspace(workspace)
                root = workspace / "v2" / "operator"
                if case == "cross-tenant":
                    artifacts = root / "artifacts.json"
                    artifacts.write_text(artifacts.read_text(encoding="utf-8").replace(TENANT, "tenant-other"), encoding="utf-8")
                else:
                    artifact = root / "artifact-content" / "artifact-strategy-0001.md"
                    target = root / "artifact-content" / "other.md"
                    target.write_bytes(artifact.read_bytes())
                    artifact.unlink()
                    artifact.symlink_to(target.name)

                with self.assertRaisesRegex(RepositoryError, "Canonical delivery"):
                    self.repository(workspace).delivery_snapshot(TENANT, PROJECT)

    def test_provisioned_workspace_snapshot_requires_the_effective_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provisioning_root = Path(temporary) / "provisioned"
            workspace = provisioning_root / TENANT / PROJECT
            seed_workspace(workspace)
            project = workspace / "v2/operator/project.json"
            project.write_text(f"{project.read_text(encoding='utf-8')}\n", encoding="utf-8")
            raw_registry = WorkspaceRegistry(())

            with self.assertRaisesRegex(RepositoryError, "not configured"):
                DeliverySnapshotRepository(raw_registry).snapshot(TENANT, PROJECT)

            snapshot = ProjectRepository(
                ProvisionedWorkspaceResolver(raw_registry, provisioning_root, True)
            ).delivery_snapshot(TENANT, PROJECT)

            self.assertEqual(workspace, snapshot.workspace.workspace_root)


if __name__ == "__main__":
    unittest.main()
