from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from services.operator_api.provisioning import ProvisionedWorkspaceResolver
from services.operator_api.recovery_inventory import RecoveryInventory, RecoveryReplayIdentity, RecoverySidecar
from services.operator_api.repository import RepositoryError, WorkspaceRegistration, WorkspaceRegistry


class RecoveryInventorySafetyTests(unittest.TestCase):
    @staticmethod
    def operator(root: Path, tenant_id: str = "tenant-provisioned", project_id: str = "project-provisioned") -> Path:
        operator = root / tenant_id / project_id / "v2/operator"
        operator.mkdir(parents=True)
        (operator / "project.json").write_text(
            json.dumps({"tenant_id": tenant_id, "project_id": project_id}, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return operator

    @staticmethod
    def inventory(root: Path) -> RecoveryInventory:
        return RecoveryInventory(ProvisionedWorkspaceResolver(WorkspaceRegistry(()), root, True))

    def test_symlinked_recovery_family_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operator = self.operator(root)
            outside = operator / "outside"
            outside.mkdir()
            os.symlink(outside, operator / "projection-recovery")

            with self.assertRaisesRegex(RepositoryError, "^Operator API recovery inventory is invalid\\.$") as raised:
                self.inventory(root).sidecars()
            self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", raised.exception.code)

    def test_symlink_nested_directory_and_fifo_entries_fail_closed(self) -> None:
        cases = ("symlink", "directory", "fifo")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                if case == "fifo" and (os.name == "nt" or not hasattr(os, "mkfifo")):
                    continue
                root = Path(temporary)
                operator = self.operator(root)
                recovery = operator / "delivery/recovery"
                recovery.mkdir(parents=True)
                entry = recovery / "unsafe"
                if case == "symlink":
                    target = root / "target.json"
                    target.write_text("{}", encoding="utf-8")
                    os.symlink(target, entry)
                elif case == "directory":
                    entry.mkdir()
                else:
                    os.mkfifo(entry)

                with self.assertRaisesRegex(RepositoryError, "^Operator API recovery inventory is invalid\\.$") as raised:
                    self.inventory(root).sidecars()
                self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", raised.exception.code)

    def test_recovery_inventory_is_canonically_sorted_across_workspaces_and_families(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registrations = (
                WorkspaceRegistration("tenant-zulu", "project-zulu", root / "z"),
                WorkspaceRegistration("tenant-alpha", "project-bravo", root / "b"),
                WorkspaceRegistration("tenant-alpha", "project-alpha", root / "a"),
            )
            for registration in registrations:
                operator = registration.workspace / "v2/operator"
                operator.mkdir(parents=True)
                for relative in ("runtime-recovery/z.json", "delivery/recovery/z.json", "delivery/recovery/a.json"):
                    sidecar = operator / relative
                    sidecar.parent.mkdir(parents=True, exist_ok=True)
                    sidecar.write_text("{}", encoding="utf-8")
            inventory = RecoveryInventory(WorkspaceRegistry(registrations))

            sidecars = inventory.sidecars()

            self.assertEqual(tuple(sorted(sidecars, key=lambda item: (item.tenant_id, item.project_id, item.family, item.relative_path))), sidecars)

    def test_exact_recovery_authorization_is_order_independent(self) -> None:
        authorizations = []
        for order in (("tenant-zulu", "tenant-provisioned"), ("tenant-provisioned", "tenant-zulu")):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for tenant_id in order:
                    self.operator(root, tenant_id, "project-provisioned")
                operator = root / "tenant-provisioned/project-provisioned/v2/operator"
                recovery = operator / "delivery/recovery"
                recovery.mkdir(parents=True)
                sidecar = recovery / "exact.json"
                sidecar.write_text("{}", encoding="utf-8")
                identity = RecoveryReplayIdentity("tenant-provisioned", "project-provisioned", "delivery-recovery", "delivery/recovery/exact.json")

                authorizations.append(self.inventory(root).authorize(identity))

        expected = RecoverySidecar("tenant-provisioned", "project-provisioned", "delivery-recovery", "delivery/recovery/exact.json")
        self.assertEqual((expected, expected), tuple(item.replay.sidecar() for item in authorizations if item.replay is not None))


if __name__ == "__main__":
    unittest.main()
