from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.operator_api.artifact_revisions import ArtifactRevisionService
from services.operator_api.next_runs import NextRunService
from services.operator_api.provisioning import ProvisionedWorkspaceResolver
from services.operator_api.recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from services.operator_api.repository import RepositoryError, WorkspaceRegistry
from services.operator_api.runtime import LocalRuntimeService


class RecoveryInventoryTests(unittest.TestCase):
    def test_production_mutators_require_recovery_inventory_at_construction(self) -> None:
        with self.assertRaises(TypeError):
            ArtifactRevisionService(None, {})
        with self.assertRaises(TypeError):
            LocalRuntimeService("simulated", None)
        with self.assertRaises(TypeError):
            NextRunService(None, {})

    def test_provisioned_workspace_sidecar_blocks_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "tenant-provisioned" / "project-provisioned"
            operator = workspace / "v2" / "operator"
            operator.mkdir(parents=True)
            (operator / "project.json").write_text(json.dumps({"tenant_id": "tenant-provisioned", "project_id": "project-provisioned"}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            sidecar = operator / "next-run-recovery" / "run-provisioned-0001.json"
            sidecar.parent.mkdir()
            sidecar.write_text("{}", encoding="utf-8")
            inventory = RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True))
            self.assertTrue(inventory.blocked())
            self.assertEqual("next-run-recovery", inventory.sidecars()[0].family)

    def test_authorizes_only_one_matching_exact_replay_sidecar(self) -> None:
        # Given: one recoverable artifact transaction and one unrelated workspace sidecar
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator = root / "tenant-provisioned" / "project-provisioned" / "v2" / "operator"
            operator.mkdir(parents=True)
            (operator / "project.json").write_text(json.dumps({"tenant_id": "tenant-provisioned", "project_id": "project-provisioned"}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            for family, name in (("artifact-recovery", "artifact.json"), ("runtime-recovery", "run-a.json")):
                path = operator / family / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
            inventory = RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True))
            replay = RecoveryReplayIdentity("tenant-provisioned", "project-provisioned", "artifact-recovery", "artifact-recovery/artifact.json")

            # When: the requested replay matches only one of several pending sidecars
            with self.assertRaisesRegex(RepositoryError, "recovery is pending"):
                inventory.authorize(replay)

            # Then: unrelated sidecars continue to block the workspace
            self.assertTrue(inventory.blocked())

    def test_authorizes_each_single_matching_sidecar_family(self) -> None:
        families = (
            "projection-recovery",
            "transition-recovery",
            "runtime-recovery",
            "artifact-recovery",
            "next-run-recovery",
        )
        for family in families:
            with self.subTest(family=family), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                operator = root / "tenant-provisioned" / "project-provisioned" / "v2" / "operator"
                operator.mkdir(parents=True)
                (operator / "project.json").write_text(json.dumps({"tenant_id": "tenant-provisioned", "project_id": "project-provisioned"}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                path = operator / family / "recover.json"
                path.parent.mkdir()
                path.write_text("{}", encoding="utf-8")
                replay = RecoveryReplayIdentity("tenant-provisioned", "project-provisioned", family, f"{family}/recover.json")

                authorization = RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True)).authorize(replay)

                self.assertEqual(replay, authorization.replay)

    def test_ignores_the_non_produced_validated_artifact_recovery_directory(self) -> None:
        # Given: a workspace containing the retired, never-produced recovery directory
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator = root / "tenant-provisioned" / "project-provisioned" / "v2" / "operator"
            operator.mkdir(parents=True)
            (operator / "project.json").write_text(json.dumps({"tenant_id": "tenant-provisioned", "project_id": "project-provisioned"}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            stale = operator / "validated-artifact-recovery" / "recover.json"
            stale.parent.mkdir()
            stale.write_text("{}", encoding="utf-8")

            # When: recovery inventory is built from real emitted sidecar families
            inventory = RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True))

            # Then: the retired directory cannot block unrelated operator work
            self.assertFalse(inventory.blocked())

    def test_rejects_a_mismatched_replay_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator = root / "tenant-provisioned" / "project-provisioned" / "v2" / "operator"
            operator.mkdir(parents=True)
            (operator / "project.json").write_text(json.dumps({"tenant_id": "tenant-provisioned", "project_id": "project-provisioned"}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            path = operator / "transition-recovery" / "command-a.json"
            path.parent.mkdir()
            path.write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(RepositoryError, "recovery is pending"):
                RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True)).authorize(RecoveryReplayIdentity("tenant-provisioned", "project-provisioned", "transition-recovery", "transition-recovery/command-b.json"))
