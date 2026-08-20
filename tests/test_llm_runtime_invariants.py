from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class LlmRuntimeInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from services.runtime_contracts.llm_records import RuntimeContractValidator

        cls.validator = RuntimeContractValidator(
            {name: load_json(RUNTIME_DIR / f"{name}.schema.json") for name in SCHEMA_NAMES},
            load_json(RUNTIME_DIR / "official-prompt-registry.json"),
        )

    def record(self, name: str) -> dict:
        return load_json(FIXTURE_DIR / name)

    def assert_valid(self, kind: str, value: dict) -> None:
        result = self.validator.validate(kind, value)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual((), result.errors)

    def assert_invalid(self, kind: str, value: dict) -> None:
        result = self.validator.validate(kind, value)
        self.assertFalse(result.valid)
        self.assertTrue(result.errors)
        self.assertTrue(all(error.code.startswith("LLM_RUNTIME_") for error in result.errors))

    def test_accepts_distinct_valid_records(self) -> None:
        self.assert_valid("logical-project-session", self.record("positive-logical-session-intake.json"))
        self.assert_valid("logical-project-session", self.record("positive-logical-session-project-v2.json"))
        self.assert_valid("worker-profile", self.record("positive-worker-profile.json"))
        self.assert_valid("context-package", self.record("positive-context-step0-initial.json"))
        self.assert_valid("context-package", self.record("positive-context-step1-next.json"))
        self.assert_valid("context-package", self.record("positive-context-revision.json"))
        self.assert_valid("llm-run-request", self.record("positive-request-fresh.json"))
        self.assert_valid("llm-run-request", self.record("positive-request-cache-hint-retry.json"))
        self.assert_valid("llm-run-result", self.record("positive-result-success.json"))
        self.assert_valid("llm-run-result", self.record("positive-result-failed.json"))

    def test_context_rejects_missing_project_v2_duplicate_intake_and_invalid_order(self) -> None:
        missing_project = self.record("positive-context-step1-next.json")
        missing_project["sources"] = [
            source for source in missing_project["sources"] if source["source_kind"] != "project_v2"
        ]
        self.assert_invalid("context-package", missing_project)

        duplicate_intake = self.record("positive-context-step0-initial.json")
        duplicate_intake["sources"].append(copy.deepcopy(duplicate_intake["sources"][0]))
        duplicate_intake["sources"][1]["source_id"] = "intake-demo-0002"
        duplicate_intake["sources"][1]["logical_ref"] = "runtime:intake/intake-demo-0002"
        self.assert_invalid("context-package", duplicate_intake)

        duplicate_order = self.record("positive-context-step1-next.json")
        duplicate_order["sources"][1]["include_order"] = 1
        self.assert_invalid("context-package", duplicate_order)

        noncontiguous_order = self.record("positive-context-step1-next.json")
        noncontiguous_order["sources"][1]["include_order"] = 3
        self.assert_invalid("context-package", noncontiguous_order)

        missing_source_identity = self.record("positive-context-step1-next.json")
        del missing_source_identity["sources"][0]["tenant_id"]
        self.assert_invalid("context-package", missing_source_identity)

    def test_context_rejects_stale_bindings_and_revision_equality(self) -> None:
        superseded = self.record("positive-context-step1-next.json")
        superseded["sources"][0]["source_status"] = "superseded"
        self.assert_invalid("context-package", superseded)

        wrong_prompt = self.record("positive-context-step1-next.json")
        wrong_prompt["prompt"]["prompt_id"] = "heartweb.step.2"
        self.assert_invalid("context-package", wrong_prompt)

        wrong_output = self.record("positive-context-step1-next.json")
        wrong_output["output_contracts"][0]["contract_path"] = "standards/outputs/step-2-keyword-evidence.schema.json"
        self.assert_invalid("context-package", wrong_output)

        equal_revision = self.record("positive-context-revision.json")
        equal_revision["target_revision"] = 2
        equal_revision["revision_context"]["expected_new_revision"] = 2
        self.assert_invalid("context-package", equal_revision)

    def test_context_rejects_ambiguous_logical_references_and_project_binding(self) -> None:
        double_separator = self.record("positive-context-step1-next.json")
        double_separator["sources"][0]["logical_ref"] = "runtime:project//project-v2-demo-0001"
        self.assert_invalid("context-package", double_separator)

        trailing_separator = self.record("positive-context-step1-next.json")
        trailing_separator["sources"][0]["logical_ref"] = "runtime:project/project-v2-demo-0001/"
        self.assert_invalid("context-package", trailing_separator)

        binding_mismatch = self.record("positive-context-step1-next.json")
        binding_mismatch["project_context"]["content_sha256"] = "0" * 64
        self.assert_invalid("context-package", binding_mismatch)

    def test_context_rejects_selected_project_source_policy_values(self) -> None:
        probes = (
            ("positive-context-step0-initial.json", 0, "trust_level", "operator_asserted", "/sources/0/trust_level"),
            ("positive-context-step0-initial.json", 0, "trust_level", "not_applicable", "/sources/0/trust_level"),
            ("positive-context-step0-initial.json", 0, "trust_level", "untrusted", "/sources/0/trust_level"),
            ("positive-context-step1-next.json", 0, "source_status", "active", "/sources/0/source_status"),
            ("positive-context-step1-next.json", 0, "source_status", "rejected", "/sources/0/source_status"),
            ("positive-context-step1-next.json", 0, "source_status", "historical", "/sources/0/source_status"),
        )
        for fixture_name, index, field, value, path in probes:
            with self.subTest(fixture_name=fixture_name, field=field, value=value):
                context = self.record(fixture_name)
                context["sources"][index][field] = value
                result = self.validator.validate("context-package", context)
                self.assertFalse(result.valid)
                self.assertEqual(
                    (("LLM_RUNTIME_CONTEXT_INVALID", path),),
                    tuple((error.code, error.path) for error in result.errors),
                )

    def test_context_accepts_nonselected_source_policy_values(self) -> None:
        for trust_level, source_status in (("operator_asserted", "active"), ("not_applicable", "rejected")):
            with self.subTest(trust_level=trust_level, source_status=source_status):
                context = self.record("positive-context-step1-next.json")
                context["sources"][1]["trust_level"] = trust_level
                context["sources"][1]["source_status"] = source_status
                self.assert_valid("context-package", context)

    def test_context_rejects_project_context_source_kind_swaps(self) -> None:
        intake_swap = self.record("positive-context-step0-initial.json")
        intake_swap["sources"].append(
            {
                "include_order": 2,
                "source_kind": "official_prompt",
                "source_id": "prompt-demo-0001",
                "tenant_id": "tenant-demo",
                "project_id": "project-demo",
                "revision": 1,
                "logical_ref": "prompt:heartweb-step-0",
                "content_sha256": "d" * 64,
                "source_status": "active",
                "trust_level": "trusted",
            }
        )
        intake_swap["project_context"] = {
            "binding_mode": "project_intake",
            "source_id": "prompt-demo-0001",
            "revision": 1,
            "logical_ref": "prompt:heartweb-step-0",
            "content_sha256": "d" * 64,
        }
        first = self.validator.validate("context-package", intake_swap)
        second = self.validator.validate("context-package", intake_swap)
        self.assertFalse(first.valid)
        self.assertEqual(first, second)
        self.assertEqual(
            (("LLM_RUNTIME_CONTEXT_INVALID", "/project_context/source_id"),),
            tuple((error.code, error.path) for error in first.errors),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.errors[0].code = "changed"

        project_v2_swap = self.record("positive-context-step1-next.json")
        predecessor = project_v2_swap["sources"][1]
        project_v2_swap["project_context"] = {
            field: predecessor[field]
            for field in ("source_id", "revision", "logical_ref", "content_sha256")
        } | {"binding_mode": "project_v2"}
        result = self.validator.validate("context-package", project_v2_swap)
        self.assertFalse(result.valid)
        self.assertEqual(
            (("LLM_RUNTIME_CONTEXT_INVALID", "/project_context/source_id"),),
            tuple((error.code, error.path) for error in result.errors),
        )

    def test_registry_rejects_duplicate_and_cross_step_entries(self) -> None:
        duplicate = load_json(RUNTIME_DIR / "official-prompt-registry.json")
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
        self.assert_invalid("official-prompt-registry", duplicate)

        cross_step = load_json(RUNTIME_DIR / "official-prompt-registry.json")
        cross_step["entries"][0]["prompt_id"] = "heartweb.step.1"
        self.assert_invalid("official-prompt-registry", cross_step)

    def test_worker_and_request_reject_local_policy_mismatches(self) -> None:
        outside_allowlist = self.record("positive-worker-profile.json")
        outside_allowlist["model_policy"]["default_model_id"] = "model-other"
        self.assert_invalid("worker-profile", outside_allowlist)

        mismatched_hash = self.record("positive-request-fresh.json")
        mismatched_hash["input_sha256"] = "0" * 64
        self.assert_invalid("llm-run-request", mismatched_hash)

        mismatched_provider = self.record("positive-request-cache-hint-retry.json")
        mismatched_provider["technical_session_cache_hint"]["provider_id"] = "provider-other"
        self.assert_invalid("llm-run-request", mismatched_provider)

    def test_result_rejects_output_token_and_timestamp_mismatches(self) -> None:
        wrong_revision = self.record("positive-result-success.json")
        wrong_revision["output"]["revision"] = 2
        self.assert_invalid("llm-run-result", wrong_revision)

        invalid_tokens = self.record("positive-result-success.json")
        invalid_tokens["token_usage"]["total_tokens"] = 16
        self.assert_invalid("llm-run-result", invalid_tokens)

        reverse_timestamps = self.record("positive-result-success.json")
        reverse_timestamps["started_at"] = "2026-08-20T00:00:02Z"
        self.assert_invalid("llm-run-result", reverse_timestamps)

    def test_session_rejects_binding_mode_mismatch(self) -> None:
        session = self.record("positive-logical-session-intake.json")
        session["project_source"]["logical_ref"] = "runtime:project/project-v2-demo-0001"
        self.assert_invalid("logical-project-session", session)

        source_kind_mismatch = self.record("positive-logical-session-intake.json")
        source_kind_mismatch["project_source"]["source_kind"] = "project_v2"
        self.assert_invalid("logical-project-session", source_kind_mismatch)

        ambiguous = self.record("positive-logical-session-project-v2.json")
        ambiguous["superseded_by_logical_session_id"] = ambiguous["supersedes_logical_session_id"]
        self.assert_invalid("logical-project-session", ambiguous)

    def test_assert_helper_raises_structured_immutable_result(self) -> None:
        from services.runtime_contracts.llm_records import RuntimeContractError

        value = self.record("positive-worker-profile.json")
        value["model_policy"]["default_model_id"] = "model-other"
        with self.assertRaises(RuntimeContractError) as raised:
            self.validator.assert_valid("worker-profile", value)
        self.assertFalse(raised.exception.result.valid)
        self.assertEqual("LLM_RUNTIME_WORKER_INVALID", raised.exception.result.errors[0].code)


if __name__ == "__main__":
    unittest.main()
