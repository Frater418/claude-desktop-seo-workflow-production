from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.context_builder import build_context_package, validate_context_package
from services.operator_api.runtime import _runtime_sources
from services.operator_api.production_bundles import ProductionBundleAssembler, ProductionBundleError
from services.runtime_contracts.llm_records import RuntimeContractValidator
from tests.support.pq0_2_step2 import load_pq0_2_fixture


ROOT = Path(__file__).resolve().parents[1]
TENANT = "tenant-demo"
PROJECT = "project-demo"
RUN = "run-demo-step2"


class _RepositoryStub:
    def __init__(self) -> None:
        step2_bytes = json.dumps(load_pq0_2_fixture()["candidate"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self._contents = {
            "artifact-step1-0001": b'{"step":"1"}',
            "artifact-step1b-0001": b'{"step":"1b"}',
            "artifact-step1c-design": b'{"step":"1c","kind":"design"}',
            "artifact-step1c-template": b'{"step":"1c","kind":"template"}',
            "artifact-step2-0001": step2_bytes,
        }
        self._releases = {
            step: {
                "release_id": f"release-{step.replace('b', 'bee').replace('c', 'cee')}-0001",
                "tenant_id": TENANT,
                "project_id": PROJECT,
                "run_id": RUN,
                "step_id": step,
                "artifact_id": artifact_id,
                "artifact_sha256": hashlib.sha256(self._contents[artifact_id]).hexdigest(),
                "artifact_revision": 1,
                "status": "released",
            }
            for step, artifact_id in (
                ("1", "artifact-step1-0001"),
                ("1b", "artifact-step1b-0001"),
                ("1c", "artifact-step1c-design"),
                ("2", "artifact-step2-0001"),
            )
        }
        self._artifacts = [
            {
                "artifact_id": artifact_id,
                "tenant_id": TENANT,
                "project_id": PROJECT,
                "run_id": RUN,
                "step_id": step,
                "revision": 1,
                "content_sha256": hashlib.sha256(content).hexdigest(),
            }
            for artifact_id, step, content in (
                ("artifact-step1-0001", "1", self._contents["artifact-step1-0001"]),
                ("artifact-step1b-0001", "1b", self._contents["artifact-step1b-0001"]),
                ("artifact-step1c-design", "1c", self._contents["artifact-step1c-design"]),
                ("artifact-step1c-template", "1c", self._contents["artifact-step1c-template"]),
                ("artifact-step2-0001", "2", self._contents["artifact-step2-0001"]),
            )
        ]

    def workflow(self, tenant_id: str, project_id: str) -> dict[str, object]:
        return {
            "steps": [
                {"step_id": step, "requires_released_predecessor": step != "0"}
                for step in ("0", "1", "1b", "1c", "2", "3")
            ],
            "initial_edges": [
                {"from_step_id": left, "to_step_id": right}
                for left, right in (("0", "1"), ("1", "1b"), ("1b", "1c"), ("1c", "2"), ("2", "3"))
            ],
        }

    def released_predecessor(self, tenant_id: str, project_id: str, step_id: str) -> dict[str, object] | None:
        return copy.deepcopy(self._releases.get(step_id))

    def source_bytes(self, tenant_id: str, project_id: str, source: str) -> bytes:
        if source != "project_v2":
            raise AssertionError(source)
        return b'{"project":"v2"}'

    def released_artifact_bytes(self, tenant_id: str, project_id: str, release: dict[str, object]) -> bytes:
        return self._contents[str(release["artifact_id"])]

    def artifacts(self, tenant_id: str, project_id: str) -> list[dict[str, object]]:
        return copy.deepcopy(self._artifacts)

    def artifact_bytes(self, tenant_id: str, project_id: str, artifact: dict[str, object]) -> bytes:
        return self._contents[str(artifact["artifact_id"])]


def _validator() -> RuntimeContractValidator:
    runtime = ROOT / "standards" / "runtime"
    names = (
        "logical-project-session",
        "official-prompt-registry",
        "worker-profile",
        "context-package",
        "llm-run-request",
        "llm-run-result",
    )
    schemas = {name: json.loads((runtime / f"{name}.schema.json").read_text(encoding="utf-8")) for name in names}
    registry = json.loads((runtime / "official-prompt-registry.json").read_text(encoding="utf-8"))
    return RuntimeContractValidator(schemas, registry)


def _registry_and_sources() -> tuple[dict[str, object], dict[str, bytes]]:
    registry = json.loads((ROOT / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    entry = next(item for item in registry["entries"] if item["step_id"] == "2")
    prompt_bytes = (ROOT / entry["prompt_path"]).read_bytes()
    entry["prompt_sha256"] = hashlib.sha256(prompt_bytes).hexdigest()
    source_bytes = {
        "runtime:project/project-demo": b'{"project":"v2"}',
        "runtime:artifact/artifact-step1-0001": b'{"step":"1"}',
        "runtime:artifact/artifact-step1b-0001": b'{"step":"1b"}',
        "runtime:artifact/artifact-step1c-design": b'{"step":"1c","kind":"design"}',
        "prompt:2": prompt_bytes,
    }
    for index, contract in enumerate(entry["output_contracts"], start=1):
        source_bytes[f"output-contract:2/{index}"] = (ROOT / contract["contract_path"]).read_bytes()
    return registry, source_bytes


class ContextSourceClosureTests(unittest.TestCase):
    def test_step2_bundle_reads_approved_pillars_from_released_step1_bytes(self) -> None:
        class Repository:
            def released_predecessor(self, tenant_id: str, project_id: str, step_id: str) -> dict[str, object] | None:
                return {"artifact_id": "artifact-step1-release", "step_id": "1", "status": "released"} if step_id == "1" else None

            def released_artifact_bytes(self, tenant_id: str, project_id: str, release: dict[str, object]) -> bytes:
                return b'{"pillars":[{"pillar_id":"pillar-alpha-001"},{"pillar_id":"pillar-beta-001"}]}'

        assembler = object.__new__(ProductionBundleAssembler)
        assembler.repository = Repository()

        self.assertEqual(
            ["pillar-alpha-001", "pillar-beta-001"],
            assembler._released_step1_pillar_ids(TENANT, PROJECT),
        )

    def test_step2_bundle_rejects_malformed_released_pillar_inventory(self) -> None:
        class Repository:
            def released_predecessor(self, tenant_id: str, project_id: str, step_id: str) -> dict[str, object] | None:
                return {"artifact_id": "artifact-step1-release", "step_id": "1", "status": "released"}

            def released_artifact_bytes(self, tenant_id: str, project_id: str, release: dict[str, object]) -> bytes:
                return b'{"pillars":[{"pillar_id":"pillar-duplicate"},{"pillar_id":"pillar-duplicate"}]}'

        assembler = object.__new__(ProductionBundleAssembler)
        assembler.repository = Repository()

        with self.assertRaises(ProductionBundleError) as error:
            assembler._released_step1_pillar_ids(TENANT, PROJECT)
        self.assertEqual("ERROR_STEP2_APPROVED_PILLARS_MISSING", error.exception.code)

    def test_step2_runtime_sources_include_released_topic_and_architecture_ancestors(self) -> None:
        source_bytes: dict[str, bytes] = {}

        sources, predecessor_ref, releases, requests = _runtime_sources(
            _RepositoryStub(),
            {"tenant_id": TENANT, "project_id": PROJECT, "run_id": RUN, "step_id": "2"},
            source_bytes,
        )

        self.assertEqual("runtime:artifact/artifact-step1c-design", predecessor_ref)
        self.assertEqual(3, len(releases))
        self.assertEqual(
            ["artifact-step1-0001", "artifact-step1b-0001", "artifact-step1c-template"],
            sorted(str(source["source_id"]) for source in sources if source["source_kind"] == "released_supporting_artifact"),
        )
        self.assertEqual((), requests)


    def test_context_validator_accepts_only_released_ancestor_supporting_artifacts(self) -> None:
        registry, source_bytes = _registry_and_sources()
        sources = (
            {"source_kind": "project_v2", "source_id": PROJECT, "tenant_id": TENANT, "project_id": PROJECT, "revision": 1, "logical_ref": "runtime:project/project-demo", "source_status": "released", "trust_level": "trusted"},
            {"source_kind": "released_predecessor", "source_id": "artifact-step1c-design", "tenant_id": TENANT, "project_id": PROJECT, "revision": 1, "logical_ref": "runtime:artifact/artifact-step1c-design", "source_status": "released", "trust_level": "trusted"},
            {"source_kind": "released_supporting_artifact", "source_id": "artifact-step1-0001", "tenant_id": TENANT, "project_id": PROJECT, "revision": 1, "logical_ref": "runtime:artifact/artifact-step1-0001", "source_status": "released", "trust_level": "trusted"},
            {"source_kind": "released_supporting_artifact", "source_id": "artifact-step1b-0001", "tenant_id": TENANT, "project_id": PROJECT, "revision": 1, "logical_ref": "runtime:artifact/artifact-step1b-0001", "source_status": "released", "trust_level": "trusted"},
        )
        package = build_context_package(
            {
                "context_package_id": "context-demo-step2",
                "tenant_id": TENANT,
                "project_id": PROJECT,
                "run_id": RUN,
                "step_id": "2",
                "logical_session_id": "logical-session-demo-step2",
                "logical_session_revision": 5,
                "trigger": "next_step",
                "target_revision": 1,
                "created_at": "2026-08-25T20:00:00Z",
                "created_by": "operator-demo",
                "worker_profile_ref": {"worker_profile_id": "worker-profile-demo", "profile_version": "1.0.0", "profile_sha256": "a" * 64},
            },
            sources,
            source_bytes,
            registry,
            _validator(),
        )
        records = {source["logical_ref"]: dict(source) for source in package["sources"]}
        records["runtime:artifact/artifact-step1c-design"].update({"run_id": RUN, "step_id": "1c"})
        records["runtime:artifact/artifact-step1-0001"].update({"run_id": RUN, "step_id": "1"})
        records["runtime:artifact/artifact-step1b-0001"].update({"run_id": RUN, "step_id": "1b"})
        graph = _RepositoryStub().workflow(TENANT, PROJECT)
        releases = tuple(_RepositoryStub()._releases.values())

        valid = validate_context_package(package, source_bytes, records, graph, releases, (), _validator(), registry, "2026-08-25T20:00:00Z")
        self.assertTrue(valid.valid, valid.errors)

        invalid_records = copy.deepcopy(records)
        invalid_records["runtime:artifact/artifact-step1-0001"]["step_id"] = "4a"
        invalid = validate_context_package(package, source_bytes, invalid_records, graph, releases, (), _validator(), registry, "2026-08-25T20:00:00Z")
        self.assertFalse(invalid.valid)
        self.assertIn("ERROR_CONTEXT_IDENTITY_MISMATCH", {error.code for error in invalid.errors})


if __name__ == "__main__":
    unittest.main()
