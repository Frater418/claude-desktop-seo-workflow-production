#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from services.runtime_contracts.llm_records import RuntimeContractValidator


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = REPO_ROOT / "standards" / "runtime"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "context_builder"
SCHEMA_NAMES = (
    "logical-project-session",
    "official-prompt-registry",
    "worker-profile",
    "context-package",
    "llm-run-request",
    "llm-run-result",
)
PROMPTS = {
    "0": "0-kickoff.xml.md",
    "1": "1-pillar-identifikation.xml.md",
    "1b": "1b-seitenarchitektur.xml.md",
    "1c": "1c-pillar-template.xml.md",
    "2": "2-cluster-recherche.xml.md",
    "3": "3-120-tage-plan.xml.md",
    "3b": "3b-performance-check.xml.md",
    "4a": "4a-content-briefing-und-schema.xml.md",
    "4b": "4b-landingpage-html.xml.md",
}
OUTPUTS = {
    "0": (("standards/manifest.schema.json", "https://heartweb.example/schema/manifest.schema.json", "1.0.0"),),
    "1": (("standards/outputs/step-1-topic-inventory.schema.json", "https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json", "2.0.0"),),
    "1b": (("standards/outputs/step-1b-architecture.schema.json", "https://heartweb.example/schema/outputs/step-1b-architecture.schema.json", "2.0.0"),),
    "1c": (("standards/outputs/step-1c-design-system.schema.json", "https://heartweb.example/schema/outputs/step-1c-design-system.schema.json", "2.0.0"), ("standards/outputs/step-1c-template.schema.json", "https://heartweb.example/schema/outputs/step-1c-template.schema.json", "2.0.0")),
    "2": (("standards/outputs/step-2-keyword-evidence.schema.json", "https://heartweb.example/schema/outputs/step-2-keyword-evidence.schema.json", "2.0.0"),),
    "3": (("standards/outputs/step-3-plan.schema.json", "https://heartweb.example/schema/outputs/step-3-plan.schema.json", "2.0.0"),),
    "3b": (("standards/outputs/step-3b-adjustment.schema.json", "https://heartweb.example/schema/outputs/step-3b-adjustment.schema.json", "2.0.0"),),
    "4a": (("standards/outputs/step-4a-briefing.schema.json", "https://heartweb.example/schema/outputs/step-4a-briefing.schema.json", "2.0.0"), ("standards/outputs/claim-ledger.schema.json", "https://heartweb.example/schema/outputs/claim-ledger.schema.json", "2.0.0")),
    "4b": (("standards/outputs/step-4b-page-spec.schema.json", "https://heartweb.example/schema/outputs/step-4b-page-spec.schema.json", "2.0.0"), ("standards/outputs/staging-evidence.schema.json", "https://heartweb.example/schema/outputs/staging-evidence.schema.json", "2.0.0")),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_closed_objects(test_case: unittest.TestCase, value: object, label: str) -> None:
    if isinstance(value, dict):
        if value.get("type") == "object":
            test_case.assertIs(value.get("additionalProperties"), False, label)
        for key, child in value.items():
            assert_closed_objects(test_case, child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_closed_objects(test_case, child, f"{label}[{index}]")


class LlmRuntimeContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: load_json(RUNTIME_DIR / f"{name}.schema.json") for name in SCHEMA_NAMES
        }
        for schema in cls.schemas.values():
            Draft202012Validator.check_schema(schema)
        registry = Registry()
        for schema in cls.schemas.values():
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        cls.validators = {
            name: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
            for name, schema in cls.schemas.items()
        }
        cls.runtime_validator = RuntimeContractValidator(
            cls.schemas,
            load_json(RUNTIME_DIR / "official-prompt-registry.json"),
        )

    def assert_valid_fixture(self, schema_name: str, fixture_name: str) -> None:
        value = load_json(FIXTURE_DIR / fixture_name)
        errors = list(self.validators[schema_name].iter_errors(value))
        self.assertEqual([], errors, [error.message for error in errors])
        result = self.runtime_validator.validate(schema_name, value)
        self.assertTrue(result.valid, result.errors)

    def assert_invalid_variant(self, schema_name: str, fixture_name: str, mutate) -> None:
        value = load_json(FIXTURE_DIR / fixture_name)
        mutate(value)
        self.assertTrue(list(self.validators[schema_name].iter_errors(value)))

    def test_schemas_are_unique_closed_draft_2020_12_contracts(self) -> None:
        ids = []
        for name, schema in self.schemas.items():
            Draft202012Validator.check_schema(schema)
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertEqual(f"https://heartweb.example/schema/runtime/{name}.schema.json", schema["$id"])
            assert_closed_objects(self, schema, name)
            ids.append(schema["$id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_runtime_validator_rejects_meta_invalid_schema_before_instance_validation(self) -> None:
        schemas = copy.deepcopy(self.schemas)
        invalid_condition = schemas["context-package"]["$defs"]["source"]["allOf"][2]["if"]
        invalid_condition["properties"]["required"] = invalid_condition.pop("required")
        with self.assertRaises(SchemaError):
            RuntimeContractValidator(
                schemas,
                load_json(RUNTIME_DIR / "official-prompt-registry.json"),
            )

    def test_official_registry_matches_current_prompts_outputs_and_workflow_steps(self) -> None:
        registry = load_json(RUNTIME_DIR / "official-prompt-registry.json")
        errors = list(self.validators["official-prompt-registry"].iter_errors(registry))
        self.assertEqual([], errors, [error.message for error in errors])
        result = self.runtime_validator.validate("official-prompt-registry", registry)
        self.assertTrue(result.valid, result.errors)
        entries = registry["entries"]
        self.assertEqual(set(PROMPTS), {entry["step_id"] for entry in entries if entry["active"]})
        self.assertEqual(len(PROMPTS), len([entry for entry in entries if entry["active"]]))
        graph = load_json(REPO_ROOT / "standards" / "workflow" / "workflow-graph.json")
        graph_steps = {step["step_id"] for step in graph["steps"]} | {"3b"}
        self.assertEqual(set(PROMPTS), graph_steps)
        actual_hashes = []
        recorded_hashes = []
        for entry in entries:
            actual_hashes.append((entry["step_id"], "prompt", sha256(REPO_ROOT / entry["prompt_path"])))
            recorded_hashes.append((entry["step_id"], "prompt", entry["prompt_sha256"]))
            for binding in entry["output_contracts"]:
                actual_hashes.append((entry["step_id"], binding["contract_path"], sha256(REPO_ROOT / binding["contract_path"])))
                recorded_hashes.append((entry["step_id"], binding["contract_path"], binding["contract_sha256"]))
        self.assertEqual(actual_hashes, recorded_hashes)
        for entry in entries:
            step_id = entry["step_id"]
            prompt_path = REPO_ROOT / entry["prompt_path"]
            prompt = prompt_path.read_text(encoding="utf-8")
            metadata = re.search(r"<prompt_metadata>(.*?)</prompt_metadata>", prompt, re.DOTALL)
            self.assertIsNotNone(metadata)
            self.assertEqual(step_id, re.search(r"<step>\s*([^<]+)\s*</step>", metadata.group(1)).group(1))
            self.assertEqual(re.search(r"<version>\s*([^<]+)\s*</version>", metadata.group(1)).group(1), entry["prompt_version"])
            self.assertEqual(PROMPTS[step_id], Path(entry["prompt_path"]).name)
            expected_outputs = OUTPUTS[step_id]
            self.assertEqual(len(expected_outputs), len(entry["output_contracts"]))
            for binding, expected in zip(entry["output_contracts"], expected_outputs, strict=True):
                path, contract_id, version = expected
                self.assertEqual(path, binding["contract_path"])
                self.assertEqual(contract_id, binding["contract_id"])
                self.assertEqual(version, binding["contract_version"])

    def test_positive_runtime_records_validate(self) -> None:
        fixtures = {
            "logical-project-session": ("positive-logical-session-intake.json", "positive-logical-session-project-v2.json"),
            "worker-profile": ("positive-worker-profile.json",),
            "context-package": ("positive-context-step0-initial.json", "positive-context-step1-next.json", "positive-context-step1c-multi-output.json", "positive-context-revision.json"),
            "llm-run-request": ("positive-request-fresh.json", "positive-request-cache-hint-retry.json"),
            "llm-run-result": ("positive-result-success.json", "positive-result-failed.json"),
        }
        for schema_name, names in fixtures.items():
            for fixture_name in names:
                with self.subTest(schema_name=schema_name, fixture_name=fixture_name):
                    self.assert_valid_fixture(schema_name, fixture_name)

    def test_context_rejects_authority_paths_wrong_bindings_and_missing_multi_output(self) -> None:
        self.assert_invalid_variant("context-package", "positive-context-step0-initial.json", lambda value: value.update(approval_id="approval-forbidden"))
        self.assert_invalid_variant("context-package", "positive-context-step0-initial.json", lambda value: value["project_context"].update(logical_ref="C:\\unsafe"))
        self.assert_invalid_variant("context-package", "positive-context-step0-initial.json", lambda value: value["project_context"].update(binding_mode="project_v2"))
        self.assert_invalid_variant("context-package", "positive-context-step1c-multi-output.json", lambda value: value.update(output_contracts=value["output_contracts"][:1]))
        self.assert_invalid_variant("context-package", "positive-context-step1-next.json", lambda value: value["sources"][0].update(trust_level="untrusted"))
        self.assert_invalid_variant("context-package", "positive-context-step0-initial.json", lambda value: value["sources"].append({"include_order": 2, "source_kind": "project_v2", "source_id": "project-v2-0001", "revision": 1, "logical_ref": "runtime:project/project-v2-0001", "content_sha256": "a" * 64, "source_status": "active", "trust_level": "trusted"}))
        self.assert_invalid_variant("context-package", "positive-context-revision.json", lambda value: value.update(sources=[source for source in value["sources"] if source["source_kind"] != "quality_gate_run"]))

    def test_requests_reject_cache_for_fresh_modes_and_raw_handles(self) -> None:
        for mode in ("initial_step", "next_step", "revision"):
            with self.subTest(mode=mode):
                self.assert_invalid_variant("llm-run-request", "positive-request-fresh.json", lambda value, mode=mode: value.update(run_mode=mode, dispatch_policy={"execution": "fresh", "technical_session_reuse": "cache_hint"}))
        self.assert_invalid_variant("llm-run-request", "positive-request-cache-hint-retry.json", lambda value: value["technical_session_cache_hint"].update(raw_session_handle="forbidden"))

    def test_hermes_model_identifiers_are_accepted_by_runtime_contracts(self) -> None:
        profile = load_json(FIXTURE_DIR / "positive-worker-profile.json")
        profile["provider_capability_ref"] = {"provider_id": "provider-hermes", "provider_kind": "gateway", "capability_id": "capability-hermes-runs"}
        profile["model_policy"] = {"allowed_model_ids": ["gpt-5.6-sol"], "default_model_id": "gpt-5.6-sol"}
        request = load_json(FIXTURE_DIR / "positive-request-fresh.json")
        request["provider_id"] = "provider-hermes"
        request["model_id"] = "gpt-5.6-sol"
        result = load_json(FIXTURE_DIR / "positive-result-success.json")
        result["provider_id"] = "provider-hermes"
        result["model_id"] = "gpt-5.6-sol"
        result["provider_run_id"] = "hermes-run-0001"

        self.assertEqual([], list(self.validators["worker-profile"].iter_errors(profile)))
        self.assertEqual([], list(self.validators["llm-run-request"].iter_errors(request)))
        self.assertEqual([], list(self.validators["llm-run-result"].iter_errors(result)))

    def test_results_enforce_success_and_failure_conditionals(self) -> None:
        self.assert_invalid_variant("llm-run-result", "positive-result-success.json", lambda value: value.pop("output"))
        self.assert_invalid_variant("llm-run-result", "positive-result-success.json", lambda value: value.update(error={"error_class": "provider", "message": "forbidden", "retry_class": "retryable", "occurred_at": "2026-08-20T00:00:02Z"}))
        self.assert_invalid_variant("llm-run-result", "positive-result-failed.json", lambda value: value.update(output={"artifact_id": "artifact-output-0001", "revision": 1, "content_sha256": "a" * 64, "logical_ref": "runtime:artifact/artifact-output-0001"}))

    def test_contract_surface_is_ascii_client_neutral_and_has_no_forbidden_dash(self) -> None:
        paths = [RUNTIME_DIR / "official-prompt-registry.json", *FIXTURE_DIR.glob("*.json")]
        forbidden = ("AHD", "ahd", chr(0x2013), chr(0x2014), "credential", "endpoint", "raw_session_handle")
        for path in paths:
            raw = path.read_bytes()
            with self.subTest(path=path.name):
                self.assertTrue(raw.isascii())
                text = raw.decode("ascii")
                self.assertTrue(all(token not in text for token in forbidden))


if __name__ == "__main__":
    unittest.main()
