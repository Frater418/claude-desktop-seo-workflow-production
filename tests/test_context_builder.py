from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from services.context_builder import (
    ContextBuildError,
    TechnicalSessionDecision,
    build_context_package,
    build_llm_request,
    canonical_json_bytes,
    decide_technical_session,
    sha256,
    validate_context_package,
    validate_llm_request,
    validate_llm_result,
)
from services.runtime_contracts.llm_records import RuntimeContractValidator


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_NAMES = (
    "logical-project-session",
    "official-prompt-registry",
    "worker-profile",
    "context-package",
    "llm-run-request",
    "llm-run-result",
)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def loaded_validator() -> RuntimeContractValidator:
    runtime = ROOT / "standards" / "runtime"
    schemas = {
        name: json.loads((runtime / f"{name}.schema.json").read_text(encoding="utf-8"))
        for name in RUNTIME_NAMES
    }
    registry = json.loads((runtime / "official-prompt-registry.json").read_text(encoding="utf-8"))
    return RuntimeContractValidator(schemas, registry)


def loaded_registry() -> dict[str, object]:
    return json.loads((ROOT / "standards" / "runtime" / "official-prompt-registry.json").read_text(encoding="utf-8"))


def step_zero_inputs() -> tuple[dict[str, object], tuple[dict[str, object], ...], dict[str, bytes], dict[str, object]]:
    registry = loaded_registry()
    entry = next(item for item in registry["entries"] if item["step_id"] == "0")
    intake = b'{"project":"intake"}'
    source_bytes = {"runtime:intake/intake-demo": intake, "prompt:0": (ROOT / entry["prompt_path"]).read_bytes()}
    for index, contract in enumerate(entry["output_contracts"], start=1):
        source_bytes[f"output-contract:0/{index}"] = (ROOT / contract["contract_path"]).read_bytes()
    specification = {"context_package_id": "context-demo-0001", "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-0001", "step_id": "0", "logical_session_id": "logical-session-demo-0001", "logical_session_revision": 1, "trigger": "initial_step", "target_revision": 1, "created_at": "2026-08-20T00:00:00Z", "created_by": "operator-demo", "worker_profile_ref": {"worker_profile_id": "worker-profile-demo", "profile_version": "1.0.0", "profile_sha256": "a" * 64}}
    sources = ({"source_kind": "project_intake", "source_id": "intake-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:intake/intake-demo", "source_status": "active", "trust_level": "trusted"},)
    return specification, sources, source_bytes, registry


def step_one_inputs(historical_evidence: bool = False) -> tuple[dict[str, object], tuple[dict[str, object], ...], dict[str, bytes], dict[str, object]]:
    registry = loaded_registry()
    entry = next(item for item in registry["entries"] if item["step_id"] == "1")
    source_bytes = {"runtime:project/project-demo": b'{"project":"v2"}', "runtime:artifact/artifact-step0": b'{"artifact":"step0"}', "prompt:1": (ROOT / entry["prompt_path"]).read_bytes()}
    for index, contract in enumerate(entry["output_contracts"], start=1):
        source_bytes[f"output-contract:1/{index}"] = (ROOT / contract["contract_path"]).read_bytes()
    sources = [{"source_kind": "project_v2", "source_id": "project-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:project/project-demo", "source_status": "released", "trust_level": "trusted"}, {"source_kind": "released_predecessor", "source_id": "artifact-step0", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:artifact/artifact-step0", "source_status": "released", "trust_level": "trusted"}]
    if historical_evidence:
        source_bytes["runtime:evidence/evidence-old"] = b'{"comparison":"old"}'
        sources.append({"source_kind": "evidence", "source_id": "evidence-old", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:evidence/evidence-old", "source_status": "historical", "trust_level": "untrusted", "untrusted_reason": "historical comparison", "permitted_use": "comparison_only"})
    specification = {"context_package_id": "context-demo-step1", "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "1", "logical_session_id": "logical-session-demo-step1", "logical_session_revision": 2, "trigger": "next_step", "target_revision": 1, "created_at": "2026-08-20T00:00:00Z", "created_by": "operator-demo", "worker_profile_ref": {"worker_profile_id": "worker-profile-demo", "profile_version": "1.0.0", "profile_sha256": "a" * 64}}
    return specification, tuple(sources), source_bytes, registry


def records_for(package: dict[str, object]) -> dict[str, dict[str, object]]:
    return {source["logical_ref"]: {**source, **({"run_id": package["run_id"], "step_id": "0"} if source["source_kind"] == "released_predecessor" else {})} for source in package["sources"]}


class ContextBuilderTests(unittest.TestCase):
    def test_missing_source_bytes_fails_before_package_construction(self) -> None:
        given_spec = {"context_package_id": "context-demo-0001", "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-0001", "step_id": "0", "logical_session_id": "logical-session-demo-0001", "logical_session_revision": 1, "trigger": "initial_step", "target_revision": 1, "created_at": "2026-08-20T00:00:00Z", "created_by": "operator-demo", "worker_profile_ref": {"worker_profile_id": "worker-profile-demo", "profile_version": "1.0.0", "profile_sha256": "a" * 64}}
        given_sources = ({"source_kind": "project_intake", "source_id": "intake-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:intake/intake-demo", "source_status": "active", "trust_level": "trusted"},)

        with self.assertRaises(ContextBuildError) as then_error:
            build_context_package(given_spec, given_sources, {}, {"entries": []}, loaded_validator())

        self.assertEqual("ERROR_CONTEXT_SOURCE_INVALID", then_error.exception.code)

    def test_step_zero_build_is_canonical_and_does_not_mutate_inputs(self) -> None:
        given_specification, given_sources, given_bytes, given_registry = step_zero_inputs()
        before_specification, before_sources = copy.deepcopy(given_specification), copy.deepcopy(given_sources)

        when_first = build_context_package(given_specification, given_sources, given_bytes, given_registry, loaded_validator())
        when_second = build_context_package(given_specification, tuple(reversed(given_sources)), given_bytes, given_registry, loaded_validator())

        self.assertEqual(canonical_json_bytes(when_first), canonical_json_bytes(when_second))
        self.assertEqual(when_first["package_sha256"], when_second["package_sha256"])
        self.assertEqual(before_specification, given_specification)
        self.assertEqual(before_sources, given_sources)

    def test_semantic_hash_drift_rejects_before_dispatch(self) -> None:
        given_specification, given_sources, given_bytes, given_registry = step_zero_inputs()
        package = build_context_package(given_specification, given_sources, given_bytes, given_registry, loaded_validator())
        package["package_sha256"] = "0" * 64
        records = {source["logical_ref"]: dict(source) for source in package["sources"]}

        when_result = validate_context_package(package, given_bytes, records, {"steps": [{"step_id": "0", "requires_released_predecessor": False}]}, (), (), loaded_validator(), given_registry, "2026-08-20T00:00:00Z")

        self.assertFalse(when_result.valid)
        self.assertEqual("ERROR_CONTEXT_PACKAGE_HASH_MISMATCH", when_result.errors[0].code)

    def test_retry_cache_reuse_and_loss_are_deterministic(self) -> None:
        given_specification, given_sources, given_bytes, given_registry = step_zero_inputs()
        package = build_context_package(given_specification, given_sources, given_bytes, given_registry, loaded_validator())
        package["trigger"] = "retry"
        profile = {"profile_sha256": "a" * 64, "provider_capability_ref": {"provider_id": "provider-demo"}, "model_policy": {"default_model_id": "model-demo"}, "tool_policy": {"policy_sha256": "b" * 64, "allowed_operations": ["read_context"]}}
        cache = {"tenant_id": package["tenant_id"], "project_id": package["project_id"], "run_id": package["run_id"], "step_id": package["step_id"], "target_revision": package["target_revision"], "context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"], "prompt_sha256": package["prompt"]["prompt_sha256"], "worker_profile_sha256": "a" * 64, "provider_id": "provider-demo", "model_id": "model-demo", "tool_policy_sha256": "b" * 64, "allowed_operations": ["read_context"], "session_state": "available", "expires_at": "2026-08-21T00:00:00Z"}

        self.assertEqual(TechnicalSessionDecision.REUSE_PERMITTED, decide_technical_session(package, profile, cache, "2026-08-20T00:00:00Z", True).decision)
        self.assertEqual(TechnicalSessionDecision.RECOVER_FRESH, decide_technical_session(package, profile, None, "2026-08-20T00:00:00Z", True).decision)
        self.assertEqual(TechnicalSessionDecision.DENIED, decide_technical_session(package, profile, None, "2026-08-20T00:00:00Z", False).decision)

    def test_release_revision_and_hash_must_match_predecessor(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 99, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)

        result = validate_context_package(package, source_bytes, records_for(package), {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")

        self.assertFalse(result.valid)
        self.assertEqual("ERROR_CONTEXT_PREDECESSOR_INVALID", result.errors[0].code)

    def test_permitted_historical_comparison_is_data_not_instruction(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs(historical_evidence=True)
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)

        result = validate_context_package(package, source_bytes, records_for(package), {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")

        self.assertTrue(result.valid, result.errors)

    def test_prompt_and_output_byte_drift_use_binding_errors(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        records = records_for(package)
        graph = {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)
        source_bytes["prompt:1"] = b"drift"

        result = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")

        self.assertEqual("ERROR_CONTEXT_PROMPT_BINDING_INVALID", result.errors[0].code)
        source_bytes = step_one_inputs()[2]
        source_bytes["output-contract:1/1"] = b"drift"
        result = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
        self.assertEqual("ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID", result.errors[0].code)

    def test_current_record_step_and_revision_must_match_descriptor(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        records = records_for(package)
        records["runtime:artifact/artifact-step0"]["step_id"] = "9"
        records["runtime:artifact/artifact-step0"]["revision"] = 2
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)

        result = validate_context_package(package, source_bytes, records, {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")

        self.assertFalse(result.valid)
        self.assertEqual("ERROR_CONTEXT_IDENTITY_MISMATCH", result.errors[0].code)

    def test_json_rejection_and_cache_bound_field_matrix(self) -> None:
        with self.assertRaises(ContextBuildError) as nonfinite:
            canonical_json_bytes({"number": float("nan")})
        with self.assertRaises(ContextBuildError) as unsupported:
            canonical_json_bytes({"bytes": b"forbidden"})
        self.assertEqual("ERROR_CONTEXT_SCHEMA_INVALID", nonfinite.exception.code)
        self.assertEqual("ERROR_CONTEXT_SCHEMA_INVALID", unsupported.exception.code)
        specification, sources, source_bytes, registry = step_zero_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        package["trigger"] = "resume"
        profile = {"profile_sha256": "a" * 64, "provider_capability_ref": {"provider_id": "provider-demo"}, "model_policy": {"default_model_id": "model-demo"}, "tool_policy": {"policy_sha256": "b" * 64, "allowed_operations": ["read_context"]}}
        cache = {"tenant_id": package["tenant_id"], "project_id": package["project_id"], "run_id": package["run_id"], "step_id": package["step_id"], "target_revision": package["target_revision"], "context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"], "prompt_sha256": package["prompt"]["prompt_sha256"], "worker_profile_sha256": "a" * 64, "provider_id": "provider-demo", "model_id": "model-demo", "tool_policy_sha256": "b" * 64, "allowed_operations": ["read_context"], "session_state": "available", "expires_at": "2026-08-21T00:00:00Z"}
        for field in ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "prompt_sha256", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_sha256", "allowed_operations"):
            changed = copy.deepcopy(cache)
            changed[field] = "different" if field != "allowed_operations" else ["write_candidate_output"]
            with self.subTest(field=field):
                self.assertEqual(TechnicalSessionDecision.DENIED, decide_technical_session(package, profile, changed, "2026-08-20T00:00:00Z", True).decision)

    def test_source_revision_boundary_rejects_non_integer_values_before_sorting(self) -> None:
        specification, sources, source_bytes, registry = step_zero_inputs()
        for invalid_revision in ("not-an-integer", True, 1.0, None, 0):
            malformed = dict(sources[0])
            if invalid_revision is None:
                malformed.pop("revision")
            else:
                malformed["revision"] = invalid_revision
            with self.assertRaises(ContextBuildError) as then_error:
                build_context_package(specification, (malformed,), source_bytes, registry, loaded_validator())
            self.assertEqual(("ERROR_CONTEXT_SCHEMA_INVALID", "/sources/0/revision"), (then_error.exception.code, then_error.exception.path))

    def test_current_records_and_predecessor_release_bind_exactly(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        graph = {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)
        for field, changed_value in (("source_id", "project-substituted"), ("tenant_id", "tenant-other"), ("project_id", "project-other"), ("revision", 2), ("content_sha256", "0" * 64)):
            records = records_for(package)
            records["runtime:project/project-demo"][field] = changed_value
            result = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
            self.assertIn("ERROR_CONTEXT_IDENTITY_MISMATCH", {error.code for error in result.errors})
        for lifecycle in ("active", "rejected", "superseded", "historical"):
            records = records_for(package)
            records["runtime:project/project-demo"]["source_status"] = lifecycle
            result = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
            self.assertIn("ERROR_CONTEXT_IDENTITY_MISMATCH", {error.code for error in result.errors})
        wrong_run = ({**releases[0], "run_id": "run-wrong-0001"},)
        result = validate_context_package(package, source_bytes, records_for(package), graph, wrong_run, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
        self.assertIn("ERROR_CONTEXT_PREDECESSOR_INVALID", {error.code for error in result.errors})

    def test_rfc3339_source_freshness_and_cache_expiry_are_instant_based(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        graph = {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-step1", "step_id": "0", "status": "released"},)
        for valid_until, expected_valid in (("2026-08-20T01:00:00+01:00", False), ("2026-08-20T00:30:00+01:00", False), ("2026-08-20T02:00:00+01:00", True)):
            records = records_for(package)
            records["runtime:project/project-demo"]["valid_until"] = valid_until
            result = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
            self.assertEqual(expected_valid, result.valid, result.errors)
        records = records_for(package)
        records["runtime:project/project-demo"]["valid_until"] = "2026-08-20T00:00:00"
        malformed = validate_context_package(package, source_bytes, records, graph, releases, (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
        self.assertIn("ERROR_CONTEXT_SCHEMA_INVALID", {error.code for error in malformed.errors})
        retry = {**package, "trigger": "retry"}
        profile = {"profile_sha256": "a" * 64, "provider_capability_ref": {"provider_id": "provider-demo"}, "model_policy": {"default_model_id": "model-demo"}, "tool_policy": {"policy_sha256": "b" * 64, "allowed_operations": ["read_context"]}}
        cache = {"tenant_id": retry["tenant_id"], "project_id": retry["project_id"], "run_id": retry["run_id"], "step_id": retry["step_id"], "target_revision": retry["target_revision"], "context_package_id": retry["context_package_id"], "context_package_sha256": retry["package_sha256"], "prompt_sha256": retry["prompt"]["prompt_sha256"], "worker_profile_sha256": "a" * 64, "provider_id": "provider-demo", "model_id": "model-demo", "tool_policy_sha256": "b" * 64, "allowed_operations": ["read_context"], "session_state": "available", "expires_at": "2026-08-21T00:00:00Z"}
        for state in ("missing", "lost", "expired", "invalid"):
            unavailable = {**cache, "session_state": state}
            self.assertEqual(TechnicalSessionDecision.RECOVER_FRESH, decide_technical_session(retry, profile, unavailable, "2026-08-20T00:00:00Z", True).decision)
        self.assertEqual(TechnicalSessionDecision.DENIED, decide_technical_session(retry, profile, {**cache, "session_state": "unknown_state"}, "2026-08-20T00:00:00Z", True).decision)
        for expires_at, expected in (("2026-08-20T01:00:00+01:00", TechnicalSessionDecision.RECOVER_FRESH), ("2026-08-20T00:30:00+01:00", TechnicalSessionDecision.RECOVER_FRESH), ("2026-08-20T02:00:00+01:00", TechnicalSessionDecision.REUSE_PERMITTED)):
            self.assertEqual(expected, decide_technical_session(retry, profile, {**cache, "expires_at": expires_at}, "2026-08-20T00:00:00Z", True).decision)
        with self.assertRaises(ContextBuildError):
            decide_technical_session(retry, profile, {**cache, "expires_at": "2026-08-20T00:00:00"}, "2026-08-20T00:00:00Z", True)

    def test_request_and_result_projection_success_failure_and_conflict(self) -> None:
        specification, sources, source_bytes, registry = step_zero_inputs()
        package = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        context = validate_context_package(package, source_bytes, records_for(package), {"steps": [{"step_id": "0", "requires_released_predecessor": False}]}, (), (), loaded_validator(), registry, "2026-08-20T00:00:00Z")
        profile = json.loads((ROOT / "tests" / "fixtures" / "context_builder" / "positive-worker-profile.json").read_text(encoding="utf-8"))
        request = build_llm_request(package, profile, {"llm_run_request_id": "llm-request-demo-0001", "correlation_id": "correlation-demo", "idempotency_key": "idempotency-demo"}, "2026-08-20T00:00:00Z", loaded_validator(), context)
        changed_request = copy.deepcopy(request)
        changed_request["model_id"] = "model-other"
        request_errors = validate_llm_request(changed_request, package, profile, loaded_validator(), request)
        self.assertEqual({"ERROR_LLM_REQUEST_INVALID", "ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT"}, {error.code for error in request_errors.errors})
        output = b'{"candidate":true}'
        result = {"llm_run_result_id": "llm-result-demo-0001", "schema_version": "1.0.0", "llm_run_request_id": request["llm_run_request_id"], **{field: request[field] for field in ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "worker_profile_id", "worker_profile_version", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_id", "tool_policy_version", "tool_policy_sha256", "input_sha256")}, "status": "succeeded", "started_at": "2026-08-20T00:00:00Z", "finished_at": "2026-08-20T00:00:01Z", "token_usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}, "output": {"artifact_id": "artifact-demo-0001", "revision": 1, "content_sha256": digest(output), "logical_ref": "runtime:artifact/artifact-demo-0001"}}
        result["result_sha256"] = sha256({key: value for key, value in result.items() if key != "result_sha256"})
        self.assertTrue(validate_llm_result(result, request, {"runtime:artifact/artifact-demo-0001": output}, loaded_validator()).valid)
        multi_output_ref = "runtime:artifact/artifact-demo-0012"
        multi_result = {key: value for key, value in result.items() if key not in {"schema_version", "output", "result_sha256"}}
        multi_result.update({
            "schema_version": "1.2.0",
            "provider_run_id": "provider-run-demo-0012",
            "outputs": [{"artifact_id": "artifact-demo-0012", "revision": 1, "content_sha256": digest(output), "logical_ref": multi_output_ref, "contract_id": request["output_contracts"][0]["contract_id"]}],
            "raw_output_sha256": digest(output),
            "evidence_refs": [],
            "observed_tool_calls": [],
            "observed_delegations": [],
            "lifecycle_events": [],
        })
        multi_result["result_sha256"] = sha256({key: value for key, value in multi_result.items() if key != "result_sha256"})
        self.assertTrue(validate_llm_result(multi_result, request, {multi_output_ref: output}, loaded_validator()).valid)
        for status in ("failed", "cancelled"):
            failed = {key: value for key, value in result.items() if key != "output"}
            failed.update({"status": status, "error": {"error_class": "provider", "message": "failed", "retry_class": "retryable", "occurred_at": "2026-08-20T00:00:01Z"}})
            failed["result_sha256"] = sha256({key: value for key, value in failed.items() if key != "result_sha256"})
            self.assertTrue(validate_llm_result(failed, request, {}, loaded_validator()).valid)
            failed["result_sha256"] = "0" * 64
            self.assertEqual("ERROR_LLM_RESULT_INVALID", validate_llm_result(failed, request, {}, loaded_validator()).errors[0].code)
            failed["result_sha256"] = sha256({key: value for key, value in failed.items() if key != "result_sha256"})
            failed["output"] = result["output"]
            self.assertEqual("ERROR_LLM_RESULT_INVALID", validate_llm_result(failed, request, {"runtime:artifact/artifact-demo-0001": output}, loaded_validator()).errors[0].code)
        result["result_sha256"] = "0" * 64
        self.assertEqual("ERROR_LLM_RESULT_INVALID", validate_llm_result(result, request, {"runtime:artifact/artifact-demo-0001": output}, loaded_validator()).errors[0].code)

    def test_step_1c_multi_output_and_revision_package_are_valid(self) -> None:
        specification, sources, source_bytes, registry = step_one_inputs()
        entry = next(item for item in registry["entries"] if item["step_id"] == "1c")
        specification.update({"context_package_id": "context-demo-step1c", "run_id": "run-demo-step1c", "step_id": "1c", "logical_session_id": "logical-session-demo-step1c"})
        source_bytes.pop("prompt:1")
        source_bytes["prompt:1c"] = (ROOT / entry["prompt_path"]).read_bytes()
        source_bytes = {key: value for key, value in source_bytes.items() if not key.startswith("output-contract:")}
        for index, contract in enumerate(entry["output_contracts"], start=1):
            source_bytes[f"output-contract:1c/{index}"] = (ROOT / contract["contract_path"]).read_bytes()
        multi = build_context_package(specification, sources, source_bytes, registry, loaded_validator())
        self.assertEqual(2, len(multi["output_contracts"]))
        specification.update({"context_package_id": "context-demo-revision", "run_id": "run-demo-revision", "step_id": "1", "logical_session_id": "logical-session-demo-revision", "trigger": "revision", "target_revision": 2, "revision_context": {"revision_request_id": "revision-request-demo", "rejected_artifact_revision": 1, "expected_new_revision": 2, "finding_logical_ref": "runtime:gate/finding-demo"}})
        extra = ({"source_kind": "rejected_artifact", "source_id": "artifact-rejected", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:artifact/artifact-rejected", "source_status": "rejected", "trust_level": "trusted"}, {"source_kind": "revision_request", "source_id": "revision-request-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "operator:revision/revision-request-demo", "source_status": "active", "trust_level": "trusted"}, {"source_kind": "operator_instruction", "source_id": "instruction-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "operator:instruction/instruction-demo", "source_status": "active", "trust_level": "operator_asserted"}, {"source_kind": "quality_gate_run", "source_id": "finding-demo", "tenant_id": "tenant-demo", "project_id": "project-demo", "revision": 1, "logical_ref": "runtime:gate/finding-demo", "source_status": "active", "trust_level": "trusted"})
        source_bytes = {**step_one_inputs()[2], "runtime:artifact/artifact-rejected": b"rejected", "operator:revision/revision-request-demo": b"request", "operator:instruction/instruction-demo": b"instruction", "runtime:gate/finding-demo": b"finding"}
        revision = build_context_package(specification, (*step_one_inputs()[1], *extra), source_bytes, registry, loaded_validator())
        releases = ({"artifact_id": "artifact-step0", "artifact_sha256": digest(source_bytes["runtime:artifact/artifact-step0"]), "artifact_revision": 1, "tenant_id": "tenant-demo", "project_id": "project-demo", "run_id": "run-demo-revision", "step_id": "0", "status": "released"},)
        requests = ({"revision_request_id": "revision-request-demo", "current_artifact_id": "artifact-rejected", "current_content_sha256": digest(b"rejected")},)
        self.assertTrue(validate_context_package(revision, source_bytes, records_for(revision), {"steps": [{"step_id": "1", "requires_released_predecessor": True}], "initial_edges": [{"from_step_id": "0", "to_step_id": "1"}]}, releases, requests, loaded_validator(), registry, "2026-08-20T00:00:00Z").valid)


if __name__ == "__main__":
    unittest.main()
