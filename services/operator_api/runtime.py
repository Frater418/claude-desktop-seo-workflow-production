from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from services.context_builder import (
    ContextBuildError,
    build_context_package,
    build_llm_request,
    sha256,
    validate_context_package,
    validate_llm_request,
    validate_llm_result,
)
from services.operator_api.models import JsonValue
from services.operator_api.hermes_runs_client import HermesRunsError
from services.operator_api.hermes_runtime_provider import HermesRuntimeDispatch, HermesRuntimeProvider
from services.operator_api.provider_outputs import ProviderOutputSet
from services.operator_api.recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from services.operator_api.repository import ProjectRepository, RepositoryError
from services.operator_api.step_validation import StepValidationError, StepValidationService
from services.runtime_contracts.llm_records import RuntimeContractValidator


class RuntimeProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class LocalFixtureProvider:
    fixture_id: str
    output_set: ProviderOutputSet

    @property
    def fixture_sha256(self) -> str:
        return self.output_set.canonical_sha256

    def output(self, fixture_id: str, fixture_sha256: str) -> ProviderOutputSet:
        if fixture_id != self.fixture_id or fixture_sha256 != self.fixture_sha256:
            raise RuntimeProviderError("ERROR_LOCAL_FIXTURE_UNAVAILABLE", "Requested fixture identity or hash is not approved.")
        return self.output_set


@dataclass(frozen=True, slots=True)
class PreparedRuntimeStep:
    candidate_bytes: bytes
    provider_outputs: ProviderOutputSet
    provider_output_sha256: str
    context_package: dict[str, JsonValue]
    llm_request: dict[str, JsonValue]
    llm_result: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class LocalRuntimeService:
    execution_mode: str
    fixture_provider: LocalFixtureProvider | None
    recovery_inventory: RecoveryInventory
    hermes_provider: HermesRuntimeProvider | None = None

    def dispatch_fixture(self, fixture_id: str, fixture_sha256: str) -> ProviderOutputSet:
        if self.execution_mode != "simulated" or self.fixture_provider is None:
            raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "A local fixture provider is required in explicit simulated mode.")
        return self.fixture_provider.output(fixture_id, fixture_sha256)

    def prepare_step(
        self,
        repository: ProjectRepository,
        repository_root: Path,
        runtime_validator: RuntimeContractValidator,
        worker_profile: dict[str, JsonValue],
        request: dict[str, str],
    ) -> PreparedRuntimeStep:
        provider_outputs: ProviderOutputSet | None = None
        candidate_bytes: bytes | None = None
        if self.execution_mode == "simulated":
            provider_outputs = self.dispatch_fixture(request["fixture_id"], request["fixture_sha256"])
            run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
            _assert_output_set_identity(provider_outputs, request, run)
            candidate_bytes = provider_outputs.primary.content_bytes
        else:
            run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
        registry, source_bytes = _official_sources(repository_root, request["step_id"], runtime_validator)
        package_sources, predecessor_ref, releases = _runtime_sources(repository, request, source_bytes)
        specification: dict[str, JsonValue] = {
            "context_package_id": request["context_package_id"], "tenant_id": request["tenant_id"],
            "project_id": request["project_id"], "run_id": request["run_id"], "step_id": request["step_id"],
            "logical_session_id": repository.logical_session(request["tenant_id"], request["project_id"])["logical_session_id"],
            "logical_session_revision": repository.logical_session(request["tenant_id"], request["project_id"])["session_revision"],
            "trigger": "initial_step" if request["step_id"] == "0" else "next_step", "target_revision": repository.run(request["tenant_id"], request["project_id"], request["run_id"])["revision"],
            "created_at": request["requested_at"], "created_by": request["actor_id"],
            "worker_profile_ref": {name: worker_profile[name] for name in ("worker_profile_id", "profile_version", "profile_sha256")},
        }
        package = build_context_package(specification, package_sources, source_bytes, registry, runtime_validator)
        current_records = {source["logical_ref"]: dict(source) for source in package["sources"]}
        if predecessor_ref is not None:
            current_records[predecessor_ref].update({"run_id": request["run_id"], "step_id": releases[0]["step_id"]})
        context = validate_context_package(package, source_bytes, current_records, repository.workflow(request["tenant_id"], request["project_id"]), releases, (), runtime_validator, registry, request["requested_at"])
        if not context.valid:
            raise RuntimeProviderError(context.errors[0].code, context.errors[0].message)
        identifiers = {name: request[name] for name in ("llm_run_request_id", "correlation_id", "idempotency_key")}
        llm_request = build_llm_request(package, worker_profile, identifiers, request["requested_at"], runtime_validator, context)
        request_validation = validate_llm_request(llm_request, package, worker_profile, runtime_validator)
        if not request_validation.valid:
            raise RuntimeProviderError(request_validation.errors[0].code, request_validation.errors[0].message)
        if self.execution_mode == "simulated":
            if provider_outputs is None or candidate_bytes is None:
                raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "A local fixture provider is required in explicit simulated mode.")
            result = _result(request, llm_request, candidate_bytes)
        else:
            if self.execution_mode != "real" or self.hermes_provider is None:
                raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "A Hermes provider is required in explicit real mode.")
            try:
                hermes = self.hermes_provider.execute(HermesRuntimeDispatch(
                    context_package=package,
                    llm_request=llm_request,
                    worker_profile=worker_profile,
                    official_prompt=source_bytes[f"prompt:{request['step_id']}"].decode("utf-8"),
                    registry=registry,
                    parent_revision=run["revision"],
                    source_bytes=source_bytes,
                ))
                _assert_output_set_identity(hermes.output_set, request, run, fixture=False)
                StepValidationService.from_root(repository_root).validate_output_contracts(hermes.output_set)
            except HermesRunsError as error:
                raise RuntimeProviderError(error.code, str(error)) from error
            except StepValidationError as error:
                raise RuntimeProviderError("ERROR_LLM_BACKEND_RESPONSE_INVALID", "Hermes Runs returned an invalid response.") from error
            provider_outputs = hermes.output_set
            candidate_bytes = hermes.output_bytes
            result = _hermes_result(request, llm_request, candidate_bytes, hermes.provider_run_id, hermes.started_at, hermes.finished_at, hermes.token_usage)
        result_validation = validate_llm_result(result, llm_request, {result["output"]["logical_ref"]: candidate_bytes}, runtime_validator)
        if not result_validation.valid:
            raise RuntimeProviderError(result_validation.errors[0].code, result_validation.errors[0].message)
        run["input_hash"] = package["package_sha256"]
        recovery = repository._optional(request["tenant_id"], request["project_id"], f"runtime-recovery/{request['run_id']}.json", None)
        if recovery is None:
            self.recovery_inventory.authorize()
            repository.persist_runtime(request["tenant_id"], request["project_id"], run, package, llm_request, result)
        else:
            if not isinstance(recovery, dict) or any(recovery.get(name) != value for name, value in {"run": run, "package": package, "request": llm_request, "result": result}.items()):
                raise RuntimeProviderError("ERR_IDEMPOTENCY_CONFLICT", "Runtime recovery conflicts with the requested step.")
            self.recovery_inventory.authorize(RecoveryReplayIdentity(request["tenant_id"], request["project_id"], "runtime-recovery", f"runtime-recovery/{request['run_id']}.json"))
            repository.recover_runtime_persistence(request["tenant_id"], request["project_id"], request["run_id"])
        if provider_outputs is None or candidate_bytes is None:
            raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "A runtime provider is required.")
        return PreparedRuntimeStep(candidate_bytes, provider_outputs, provider_outputs.canonical_sha256, package, llm_request, result)


def _assert_output_set_identity(
    outputs: ProviderOutputSet,
    request: dict[str, str],
    run: dict[str, JsonValue],
    *,
    fixture: bool = True,
) -> None:
    expected = (
        request["tenant_id"], request["project_id"], request["run_id"], request["step_id"],
        request["idempotency_key"], run.get("revision"),
    )
    for output in outputs.outputs:
        actual = (
            output.tenant_id, output.project_id, output.run_id, output.step_id,
            output.idempotency_key, output.parent_revision,
        )
        if actual != expected or output.target_revision != output.parent_revision + 1:
            if fixture:
                raise RuntimeProviderError("ERROR_LOCAL_FIXTURE_UNAVAILABLE", "Fixture output identity does not match the canonical execution.")
            raise RuntimeProviderError("ERROR_RUNTIME_OUTPUT_IDENTITY_INVALID", "Provider output identity does not match the canonical execution.")


def _official_sources(root: Path, step_id: str, validator: RuntimeContractValidator) -> tuple[dict[str, JsonValue], dict[str, bytes]]:
    registry = json.loads((root / "standards/runtime/official-prompt-registry.json").read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not validator.validate("official-prompt-registry", registry).valid:
        raise RuntimeProviderError("ERROR_CONTEXT_PROMPT_BINDING_INVALID", "Official prompt registry is invalid.")
    entry = next((item for item in registry["entries"] if item["step_id"] == step_id and item["active"] is True), None)
    if not isinstance(entry, dict):
        raise RuntimeProviderError("ERROR_CONTEXT_PROMPT_BINDING_INVALID", "No active official prompt exists for the requested step.")
    bytes_by_ref = {f"prompt:{step_id}": (root / entry["prompt_path"]).read_bytes()}
    for index, contract in enumerate(entry["output_contracts"], start=1):
        bytes_by_ref[f"output-contract:{step_id}/{index}"] = (root / contract["contract_path"]).read_bytes()
    return registry, bytes_by_ref


def _runtime_sources(repository: ProjectRepository, request: dict[str, str], source_bytes: dict[str, bytes]) -> tuple[tuple[dict[str, JsonValue], ...], str | None, tuple[dict[str, JsonValue], ...]]:
    tenant_id, project_id, run_id, step_id = (request[name] for name in ("tenant_id", "project_id", "run_id", "step_id"))
    if step_id == "0":
        session = repository.logical_session(tenant_id, project_id)
        source = {name: value for name, value in session["project_source"].items() if name != "content_sha256"}
        source.update({"source_kind": "project_intake", "tenant_id": tenant_id, "project_id": project_id, "source_status": "active", "trust_level": "trusted"})
        source_bytes[source["logical_ref"]] = repository.source_bytes(tenant_id, project_id, "intake")
        return (source,), None, ()
    workflow = repository.workflow(tenant_id, project_id)
    predecessor_step = next((edge["from_step_id"] for edge in workflow["initial_edges"] if edge["to_step_id"] == step_id), None)
    if not isinstance(predecessor_step, str):
        raise RuntimeProviderError("ERROR_CONTEXT_PREDECESSOR_INVALID", "The requested step has no canonical predecessor edge.")
    release = repository.released_predecessor(tenant_id, project_id, predecessor_step)
    if release is None:
        raise RuntimeProviderError("ERROR_CONTEXT_PREDECESSOR_INVALID", "A canonical released predecessor is required.")
    project_ref = f"runtime:project/{project_id}"
    artifact_ref = f"runtime:artifact/{release['artifact_id']}"
    project = {"source_kind": "project_v2", "source_id": project_id, "tenant_id": tenant_id, "project_id": project_id, "revision": 1, "logical_ref": project_ref, "source_status": "released", "trust_level": "trusted"}
    predecessor = {"source_kind": "released_predecessor", "source_id": release["artifact_id"], "tenant_id": tenant_id, "project_id": project_id, "revision": release["artifact_revision"], "logical_ref": artifact_ref, "source_status": "released", "trust_level": "trusted"}
    source_bytes[project_ref] = repository.source_bytes(tenant_id, project_id, "project_v2")
    source_bytes[artifact_ref] = repository.released_artifact_bytes(tenant_id, project_id, release)
    return (project, predecessor), artifact_ref, (release,)


def _result(request: dict[str, str], llm_request: dict[str, JsonValue], candidate_bytes: bytes) -> dict[str, JsonValue]:
    output = {"artifact_id": f"artifact-{hashlib.sha256(candidate_bytes).hexdigest()[:12]}", "revision": 1, "content_sha256": hashlib.sha256(candidate_bytes).hexdigest(), "logical_ref": f"runtime:artifact/artifact-{hashlib.sha256(candidate_bytes).hexdigest()[:12]}"}
    result = {"llm_run_result_id": request["llm_run_result_id"], "schema_version": "1.0.0", "llm_run_request_id": llm_request["llm_run_request_id"], **{name: llm_request[name] for name in ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "worker_profile_id", "worker_profile_version", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_id", "tool_policy_version", "tool_policy_sha256", "input_sha256")}, "status": "succeeded", "started_at": request["started_at"], "finished_at": request["finished_at"], "token_usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}, "output": output}
    result["result_sha256"] = sha256(result)
    return result


def _hermes_result(
    request: dict[str, str],
    llm_request: dict[str, JsonValue],
    candidate_bytes: bytes,
    provider_run_id: str,
    started_at: str,
    finished_at: str,
    token_usage: dict[str, int] | Mapping[str, int],
) -> dict[str, JsonValue]:
    result = _result(request, llm_request, candidate_bytes)
    result.update({
        "provider_run_id": provider_run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "token_usage": dict(token_usage),
    })
    result.pop("result_sha256")
    result["result_sha256"] = sha256(result)
    return result
