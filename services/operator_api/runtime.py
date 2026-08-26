from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path


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
from services.operator_api.hermes_runtime_provider import (
    HermesRuntimeDispatch,
    HermesRuntimeOutput,
    HermesRuntimeProvider,
    HermesStepExecution,
)
from services.operator_api.provider_outputs import ProviderOutputSet
from services.operator_api.recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from services.operator_api.repository import ProjectRepository, RepositoryError
from services.operator_api.step_validation import StepValidationError, StepValidationService
from services.operator_api.step_agent_results import StepAgentResultError
from services.operator_api.step_agents import StepAgentContract, StepAgentContractError, StepAgentRegistry
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
class PreparedAgentDispatch:
    request: dict[str, str]
    run: dict[str, JsonValue]
    context_package: dict[str, JsonValue]
    llm_request: dict[str, JsonValue]
    dispatch: HermesRuntimeDispatch


@dataclass(frozen=True, slots=True)
class LocalRuntimeService:
    execution_mode: str
    fixture_provider: LocalFixtureProvider | None
    recovery_inventory: RecoveryInventory
    hermes_provider: HermesRuntimeProvider | None = None
    step_agent_registry: StepAgentRegistry | None = None

    def dispatch_fixture(self, fixture_id: str, fixture_sha256: str) -> ProviderOutputSet:
        if self.execution_mode != "simulated" or self.fixture_provider is None:
            raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "A local fixture provider is required in explicit simulated mode.")
        return self.fixture_provider.output(fixture_id, fixture_sha256)

    def prepare_agent_dispatch(
        self,
        repository: ProjectRepository,
        repository_root: Path,
        runtime_validator: RuntimeContractValidator,
        request: dict[str, str],
    ) -> PreparedAgentDispatch:
        if self.execution_mode != "real" or self.hermes_provider is None or self.step_agent_registry is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "A real specialized Hermes Step-agent runtime is required.",
            )
        run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
        if run.get("step_id") != request["step_id"] or run.get("status") != "in_progress":
            raise RuntimeProviderError(
                "ERROR_PRODUCTION_STATE_INVALID",
                "The canonical run is not in progress for the requested Step agent.",
            )
        try:
            contract = self.step_agent_registry.for_step(request["step_id"])
        except StepAgentContractError as error:
            raise RuntimeProviderError(error.code, error.message) from error
        worker_profile = dict(contract.worker_profile)
        registry, source_bytes = _official_sources(repository_root, request["step_id"], runtime_validator)
        package_sources, predecessor_ref, releases, revision_requests = _runtime_sources(
            repository,
            request,
            source_bytes,
        )
        specification: dict[str, JsonValue] = {
            "context_package_id": request["context_package_id"],
            "tenant_id": request["tenant_id"],
            "project_id": request["project_id"],
            "run_id": request["run_id"],
            "step_id": request["step_id"],
            "logical_session_id": repository.logical_session(request["tenant_id"], request["project_id"])["logical_session_id"],
            "logical_session_revision": repository.logical_session(request["tenant_id"], request["project_id"])["session_revision"],
            "trigger": request.get("trigger") or ("initial_step" if request["step_id"] == "0" else "next_step"),
            "target_revision": int(run["revision"]) + 1,
            "created_at": request["requested_at"],
            "created_by": request["actor_id"],
            "worker_profile_ref": {
                name: worker_profile[name]
                for name in ("worker_profile_id", "profile_version", "profile_sha256")
            },
        }
        _bind_revision_context(specification, request, run)
        try:
            package = build_context_package(specification, package_sources, source_bytes, registry, runtime_validator)
        except ContextBuildError as error:
            raise RuntimeProviderError(error.code, error.message) from error
        current_records = _current_source_records(repository, request["tenant_id"], request["project_id"], package)
        if predecessor_ref is not None:
            current_records[predecessor_ref].update(
                {"run_id": request["run_id"], "step_id": releases[0]["step_id"]}
            )
        context = validate_context_package(
            package,
            source_bytes,
            current_records,
            repository.workflow(request["tenant_id"], request["project_id"]),
            releases,
            revision_requests,
            runtime_validator,
            registry,
            request["requested_at"],
        )
        if not context.valid:
            raise RuntimeProviderError(context.errors[0].code, context.errors[0].message)
        identifiers = {
            name: request[name]
            for name in ("llm_run_request_id", "correlation_id", "idempotency_key")
        }
        try:
            llm_request = build_llm_request(
                package,
                worker_profile,
                identifiers,
                request["requested_at"],
                runtime_validator,
                context,
            )
        except ContextBuildError as error:
            raise RuntimeProviderError(error.code, error.message) from error
        request_validation = validate_llm_request(llm_request, package, worker_profile, runtime_validator)
        if not request_validation.valid:
            raise RuntimeProviderError(
                request_validation.errors[0].code,
                request_validation.errors[0].message,
            )
        dispatch = HermesRuntimeDispatch(
            context_package=package,
            llm_request=llm_request,
            worker_profile=worker_profile,
            official_prompt=source_bytes[f"prompt:{request['step_id']}"].decode("utf-8"),
            registry=registry,
            parent_revision=run["revision"],
            source_bytes=source_bytes,
            repository_root=repository_root,
            step_agent_contract=contract,
            run_deployment_id=run.get("deployment_id") if isinstance(run.get("deployment_id"), str) else None,
        )
        return PreparedAgentDispatch(
            request=dict(request),
            run=dict(run),
            context_package=package,
            llm_request=llm_request,
            dispatch=dispatch,
        )

    def prepare_agent_retry(
        self,
        source: PreparedAgentDispatch,
        runtime_validator: RuntimeContractValidator,
        request: dict[str, str],
    ) -> PreparedAgentDispatch:
        if self.execution_mode != "real" or self.hermes_provider is None or self.step_agent_registry is None:
            raise RuntimeProviderError(
                "ERROR_RUNTIME_PROVIDER_BLOCKED",
                "A real specialized Hermes Step-agent runtime is required.",
            )
        preserved_fields = ("tenant_id", "project_id", "run_id", "step_id", "context_package_id")
        if any(request.get(field) != source.request.get(field) for field in preserved_fields):
            raise RuntimeProviderError(
                "ERROR_LLM_REQUEST_INVALID",
                "A technical retry must reuse the exact source Context Package and Core identity.",
            )
        if request.get("trigger") != "retry" or request.get("llm_run_request_id") == source.request.get("llm_run_request_id"):
            raise RuntimeProviderError(
                "ERROR_LLM_REQUEST_INVALID",
                "A technical retry requires one fresh LLM request identity.",
            )
        llm_request = dict(source.llm_request)
        llm_request.update(
            {
                "llm_run_request_id": request["llm_run_request_id"],
                "correlation_id": request["correlation_id"],
                "idempotency_key": request["idempotency_key"],
                "run_mode": "retry",
                "requested_at": request["requested_at"],
            }
        )
        validation = validate_llm_request(
            llm_request,
            source.context_package,
            source.dispatch.worker_profile,
            runtime_validator,
        )
        if not validation.valid:
            raise RuntimeProviderError(validation.errors[0].code, validation.errors[0].message)
        dispatch = replace(source.dispatch, llm_request=llm_request)
        return PreparedAgentDispatch(
            request=dict(request),
            run=dict(source.run),
            context_package=dict(source.context_package),
            llm_request=llm_request,
            dispatch=dispatch,
        )

    def start_agent_dispatch(self, prepared: PreparedAgentDispatch) -> HermesStepExecution:
        if self.hermes_provider is None:
            raise RuntimeProviderError("ERROR_RUNTIME_PROVIDER_BLOCKED", "Hermes Step-agent runtime is unavailable.")
        try:
            return self.hermes_provider.start_step(prepared.dispatch)
        except HermesRunsError as error:
            raise RuntimeProviderError(error.code, str(error)) from error

    def finalize_agent_dispatch(
        self,
        repository: ProjectRepository,
        repository_root: Path,
        runtime_validator: RuntimeContractValidator,
        prepared: PreparedAgentDispatch,
        hermes: HermesRuntimeOutput,
    ) -> PreparedRuntimeStep:
        request = prepared.request
        current_run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
        if (
            current_run.get("step_id") != request["step_id"]
            or current_run.get("revision") != prepared.run.get("revision")
            or current_run.get("status") != "in_progress"
        ):
            raise RuntimeProviderError(
                "ERR_STALE_REVISION",
                "The canonical run changed after the Hermes Step agent was dispatched.",
            )
        try:
            _assert_output_set_identity(hermes.output_set, request, current_run, fixture=False)
            StepValidationService.from_root(repository_root).validate_output_contracts(hermes.output_set)
        except StepValidationError as error:
            raise RuntimeProviderError(
                "ERROR_LLM_BACKEND_RESPONSE_INVALID",
                "Hermes Runs returned an invalid response.",
            ) from error
        result = _hermes_result(request, prepared.llm_request, hermes)
        result_validation = validate_llm_result(
            result,
            prepared.llm_request,
            hermes.output_bytes_by_ref,
            runtime_validator,
        )
        if not result_validation.valid:
            raise RuntimeProviderError(
                result_validation.errors[0].code,
                result_validation.errors[0].message,
            )
        current_run["input_hash"] = prepared.context_package["package_sha256"]
        recovery = repository._optional(
            request["tenant_id"],
            request["project_id"],
            f"runtime-recovery/{request['run_id']}.json",
            None,
        )
        if recovery is None:
            self.recovery_inventory.authorize()
            repository.persist_runtime(
                request["tenant_id"],
                request["project_id"],
                current_run,
                prepared.context_package,
                prepared.llm_request,
                result,
            )
        else:
            expected = {
                "run": current_run,
                "package": prepared.context_package,
                "request": prepared.llm_request,
                "result": result,
            }
            if not isinstance(recovery, dict) or any(recovery.get(name) != value for name, value in expected.items()):
                raise RuntimeProviderError(
                    "ERR_IDEMPOTENCY_CONFLICT",
                    "Runtime recovery conflicts with the requested Step-agent result.",
                )
            self.recovery_inventory.authorize(
                RecoveryReplayIdentity(
                    request["tenant_id"],
                    request["project_id"],
                    "runtime-recovery",
                    f"runtime-recovery/{request['run_id']}.json",
                )
            )
            repository.recover_runtime_persistence(
                request["tenant_id"],
                request["project_id"],
                request["run_id"],
            )
        return PreparedRuntimeStep(
            candidate_bytes=hermes.output_bytes,
            provider_outputs=hermes.output_set,
            provider_output_sha256=hermes.output_set.canonical_sha256,
            context_package=prepared.context_package,
            llm_request=prepared.llm_request,
            llm_result=result,
        )

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
        step_agent_contract: StepAgentContract | None = None
        if self.execution_mode == "simulated":
            provider_outputs = self.dispatch_fixture(request["fixture_id"], request["fixture_sha256"])
            run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
            _assert_output_set_identity(provider_outputs, request, run)
            candidate_bytes = provider_outputs.primary.content_bytes
        else:
            run = repository.run(request["tenant_id"], request["project_id"], request["run_id"])
            if self.step_agent_registry is None:
                raise RuntimeProviderError("ERROR_STEP_AGENT_NOT_CONFIGURED", "A specialized Step agent registry is required in real execution mode.")
            try:
                step_agent_contract = self.step_agent_registry.for_step(request["step_id"])
            except StepAgentContractError as error:
                raise RuntimeProviderError(error.code, error.message) from error
            worker_profile = dict(step_agent_contract.worker_profile)
        registry, source_bytes = _official_sources(repository_root, request["step_id"], runtime_validator)
        package_sources, predecessor_ref, releases, revision_requests = _runtime_sources(
            repository,
            request,
            source_bytes,
        )
        specification: dict[str, JsonValue] = {
            "context_package_id": request["context_package_id"], "tenant_id": request["tenant_id"],
            "project_id": request["project_id"], "run_id": request["run_id"], "step_id": request["step_id"],
            "logical_session_id": repository.logical_session(request["tenant_id"], request["project_id"])["logical_session_id"],
            "logical_session_revision": repository.logical_session(request["tenant_id"], request["project_id"])["session_revision"],
            "trigger": request.get("trigger") or ("initial_step" if request["step_id"] == "0" else "next_step"), "target_revision": int(run["revision"]) + 1,
            "created_at": request["requested_at"], "created_by": request["actor_id"],
            "worker_profile_ref": {name: worker_profile[name] for name in ("worker_profile_id", "profile_version", "profile_sha256")},
        }
        _bind_revision_context(specification, request, run)
        package = build_context_package(specification, package_sources, source_bytes, registry, runtime_validator)
        current_records = _current_source_records(repository, request["tenant_id"], request["project_id"], package)
        if predecessor_ref is not None:
            current_records[predecessor_ref].update({"run_id": request["run_id"], "step_id": releases[0]["step_id"]})
        context = validate_context_package(package, source_bytes, current_records, repository.workflow(request["tenant_id"], request["project_id"]), releases, revision_requests, runtime_validator, registry, request["requested_at"])
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
            result_bytes_by_ref = {result["output"]["logical_ref"]: candidate_bytes}
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
                    repository_root=repository_root,
                    step_agent_contract=step_agent_contract,
                ))
                _assert_output_set_identity(hermes.output_set, request, run, fixture=False)
                StepValidationService.from_root(repository_root).validate_output_contracts(hermes.output_set)
            except HermesRunsError as error:
                raise RuntimeProviderError(error.code, str(error)) from error
            except StepValidationError as error:
                raise RuntimeProviderError("ERROR_LLM_BACKEND_RESPONSE_INVALID", "Hermes Runs returned an invalid response.") from error
            except StepAgentResultError as error:
                raise RuntimeProviderError(error.code, error.message) from error
            provider_outputs = hermes.output_set
            candidate_bytes = hermes.output_bytes
            result = _hermes_result(request, llm_request, hermes)
            result_bytes_by_ref = hermes.output_bytes_by_ref
        result_validation = validate_llm_result(result, llm_request, result_bytes_by_ref, runtime_validator)
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


def _bind_revision_context(
    specification: dict[str, JsonValue],
    request: dict[str, str],
    run: dict[str, JsonValue],
) -> None:
    if specification["trigger"] != "revision":
        return
    steering_ref = request.get("steering_logical_ref")
    revision_request_id = request.get("revision_request_id")
    if not isinstance(steering_ref, str) or not isinstance(revision_request_id, str):
        raise RuntimeProviderError(
            "ERROR_CONTEXT_REVISION_BINDING_INVALID",
            "Revision dispatch requires a versioned steering ref and revision request identity.",
        )
    specification["revision_context"] = {
        "revision_request_id": revision_request_id,
        "rejected_artifact_revision": int(run["revision"]),
        "expected_new_revision": int(run["revision"]) + 1,
        "finding_logical_ref": steering_ref,
    }


_SUPPORTING_RELEASE_STEPS: dict[str, tuple[str, ...]] = {
    "2": ("1", "1b"),
    "3": ("1b",),
    "4a": ("1", "1b", "1c", "2"),
    "4b": ("1", "1b", "1c", "2", "3"),
}


def _current_source_records(
    repository: ProjectRepository,
    tenant_id: str,
    project_id: str,
    package: dict[str, JsonValue],
) -> dict[str, dict[str, JsonValue]]:
    records = {str(source["logical_ref"]): dict(source) for source in package["sources"]}
    artifacts = {str(artifact.get("artifact_id")): artifact for artifact in repository.artifacts(tenant_id, project_id)}
    for source in package["sources"]:
        if source["source_kind"] != "released_supporting_artifact":
            continue
        artifact = artifacts.get(str(source["source_id"]))
        if not isinstance(artifact, dict):
            raise RuntimeProviderError("ERROR_CONTEXT_SOURCE_INVALID", "Released supporting artifact record is unavailable.")
        records[str(source["logical_ref"])].update({"run_id": artifact.get("run_id"), "step_id": artifact.get("step_id")})
    return records


def _runtime_sources(
    repository: ProjectRepository,
    request: dict[str, str],
    source_bytes: dict[str, bytes],
) -> tuple[
    tuple[dict[str, JsonValue], ...],
    str | None,
    tuple[dict[str, JsonValue], ...],
    tuple[dict[str, JsonValue], ...],
]:
    if request.get("trigger") == "revision":
        return _revision_runtime_sources(repository, request, source_bytes)
    tenant_id, project_id, run_id, step_id = (request[name] for name in ("tenant_id", "project_id", "run_id", "step_id"))
    if step_id == "0":
        session = repository.logical_session(tenant_id, project_id)
        source = {name: value for name, value in session["project_source"].items() if name != "content_sha256"}
        source.update({"source_kind": "project_intake", "tenant_id": tenant_id, "project_id": project_id, "source_status": "active", "trust_level": "trusted"})
        source_bytes[source["logical_ref"]] = repository.source_bytes(tenant_id, project_id, "intake")
        return (source,), None, (), ()
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
    sources = [project, predecessor]
    release_records = [release]
    artifacts = repository.artifacts(tenant_id, project_id)
    release_steps = (predecessor_step, *_SUPPORTING_RELEASE_STEPS.get(step_id, ()))
    for release_step in release_steps:
        supporting_release = release if release_step == predecessor_step else repository.released_predecessor(tenant_id, project_id, release_step)
        if not isinstance(supporting_release, dict):
            raise RuntimeProviderError("ERROR_CONTEXT_PREDECESSOR_INVALID", f"Released supporting Step {release_step} is required by Step {step_id}.")
        matching_artifacts = sorted(
            (
                artifact
                for artifact in artifacts
                if artifact.get("run_id") == supporting_release.get("run_id")
                and artifact.get("step_id") == supporting_release.get("step_id")
                and artifact.get("revision") == supporting_release.get("artifact_revision")
            ),
            key=lambda artifact: str(artifact.get("artifact_id")),
        )
        if not matching_artifacts:
            raise RuntimeProviderError("ERROR_CONTEXT_SOURCE_INVALID", f"Released Step {release_step} has no canonical artifacts for its released revision.")
        for artifact in matching_artifacts:
            artifact_id = artifact.get("artifact_id")
            if not isinstance(artifact_id, str):
                raise RuntimeProviderError("ERROR_CONTEXT_SOURCE_INVALID", "Released supporting artifact identity is malformed.")
            if artifact_id == release["artifact_id"]:
                continue
            logical_ref = f"runtime:artifact/{artifact_id}"
            source_bytes[logical_ref] = repository.artifact_bytes(tenant_id, project_id, artifact)
            sources.append(
                {
                    "source_kind": "released_supporting_artifact",
                    "source_id": artifact_id,
                    "tenant_id": tenant_id,
                    "project_id": project_id,
                    "revision": artifact["revision"],
                    "logical_ref": logical_ref,
                    "source_status": "released",
                    "trust_level": "trusted",
                }
            )
        if supporting_release not in release_records:
            release_records.append(supporting_release)

    return tuple(sources), artifact_ref, tuple(release_records), ()


def _revision_runtime_sources(
    repository: ProjectRepository,
    request: dict[str, str],
    source_bytes: dict[str, bytes],
) -> tuple[
    tuple[dict[str, JsonValue], ...],
    str | None,
    tuple[dict[str, JsonValue], ...],
    tuple[dict[str, JsonValue], ...],
]:
    tenant_id, project_id, run_id, step_id = (
        request[name] for name in ("tenant_id", "project_id", "run_id", "step_id")
    )
    run = repository.run(tenant_id, project_id, run_id)
    revision_request_id = request.get("revision_request_id")
    steering_id = request.get("steering_id")
    rejected_artifact_id = request.get("rejected_artifact_id")
    rejected_artifact_sha256 = request.get("rejected_artifact_sha256")
    if not all(
        isinstance(value, str) and value
        for value in (
            revision_request_id,
            steering_id,
            rejected_artifact_id,
            rejected_artifact_sha256,
        )
    ):
        raise RuntimeProviderError(
            "ERROR_CONTEXT_REVISION_BINDING_INVALID",
            "Revision dispatch identities are incomplete.",
        )
    revision_request = repository.operator_record(
        tenant_id,
        project_id,
        "revision-request",
        str(revision_request_id),
    )
    steering = repository.operator_record(
        tenant_id,
        project_id,
        "production-steering",
        str(steering_id),
    )
    artifacts = [
        artifact
        for artifact in repository.artifacts(tenant_id, project_id)
        if artifact.get("run_id") == run_id
        and artifact.get("step_id") == step_id
        and artifact.get("revision") == run["revision"]
    ]
    primary = next(
        (
            artifact
            for artifact in artifacts
            if artifact.get("artifact_id") == rejected_artifact_id
            and artifact.get("content_sha256") == rejected_artifact_sha256
        ),
        None,
    )
    if not isinstance(primary, dict):
        raise RuntimeProviderError(
            "ERROR_CONTEXT_REVISION_BINDING_INVALID",
            "The rejected primary artifact no longer matches the canonical run revision.",
        )
    ordered_artifacts = [primary, *sorted(
        (artifact for artifact in artifacts if artifact is not primary),
        key=lambda artifact: str(artifact["artifact_id"]),
    )]
    gates = [
        gate
        for gate in repository.quality_gate_runs(tenant_id, project_id)
        if gate.get("run_id") == run_id
        and gate.get("artifact_id") == primary["artifact_id"]
        and gate.get("artifact_revision") == primary["revision"]
    ]
    if not gates:
        raise RuntimeProviderError(
            "ERROR_CONTEXT_REVISION_BINDING_INVALID",
            "Revision dispatch requires the quality-gate records for the rejected artifact.",
        )

    predecessor_ref: str | None = None
    releases: tuple[dict[str, JsonValue], ...] = ()
    sources: list[dict[str, JsonValue]] = []
    if step_id == "0":
        session = repository.logical_session(tenant_id, project_id)
        intake = {name: value for name, value in session["project_source"].items() if name != "content_sha256"}
        intake.update(
            {
                "source_kind": "project_intake",
                "tenant_id": tenant_id,
                "project_id": project_id,
                "source_status": "active",
                "trust_level": "trusted",
            }
        )
        source_bytes[intake["logical_ref"]] = repository.source_bytes(tenant_id, project_id, "intake")
        sources.append(intake)
    else:
        base_request = dict(request)
        base_request["trigger"] = "next_step"
        base_sources, predecessor_ref, releases, _ = _runtime_sources(
            repository,
            base_request,
            source_bytes,
        )
        sources.extend(base_sources)

    for artifact in ordered_artifacts:
        logical_ref = f"runtime:rejected_artifact/{artifact['artifact_id']}"
        source_bytes[logical_ref] = repository.artifact_bytes(tenant_id, project_id, artifact)
        sources.append(
            {
                "source_kind": "rejected_artifact",
                "source_id": artifact["artifact_id"],
                "tenant_id": tenant_id,
                "project_id": project_id,
                "revision": artifact["revision"],
                "logical_ref": logical_ref,
                "source_status": "rejected",
                "trust_level": "trusted",
            }
        )
    revision_ref = f"operator:revision_request/{revision_request_id}"
    steering_ref = f"operator:steering/{steering_id}"
    if request.get("steering_logical_ref") != steering_ref:
        raise RuntimeProviderError(
            "ERROR_CONTEXT_REVISION_BINDING_INVALID",
            "The requested steering logical ref is stale or mismatched.",
        )
    source_bytes[revision_ref] = _canonical_json_bytes(revision_request)
    source_bytes[steering_ref] = _canonical_json_bytes(steering)
    sources.extend(
        (
            {
                "source_kind": "revision_request",
                "source_id": revision_request_id,
                "tenant_id": tenant_id,
                "project_id": project_id,
                "revision": run["revision"],
                "logical_ref": revision_ref,
                "source_status": "active",
                "trust_level": "operator_asserted",
            },
            {
                "source_kind": "operator_instruction",
                "source_id": steering_id,
                "tenant_id": tenant_id,
                "project_id": project_id,
                "revision": int(run["revision"]) + 1,
                "logical_ref": steering_ref,
                "source_status": "active",
                "trust_level": "operator_asserted",
            },
        )
    )
    for gate in sorted(gates, key=lambda item: str(item["quality_gate_run_id"])):
        logical_ref = f"runtime:quality_gate/{gate['quality_gate_run_id']}"
        source_bytes[logical_ref] = _canonical_json_bytes(gate)
        sources.append(
            {
                "source_kind": "quality_gate_run",
                "source_id": gate["quality_gate_run_id"],
                "tenant_id": tenant_id,
                "project_id": project_id,
                "revision": gate["artifact_revision"],
                "logical_ref": logical_ref,
                "source_status": "active",
                "trust_level": "trusted",
            }
        )
    return tuple(sources), predecessor_ref, releases, (revision_request,)


def _canonical_json_bytes(value: dict[str, JsonValue]) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")


def _result(request: dict[str, str], llm_request: dict[str, JsonValue], candidate_bytes: bytes) -> dict[str, JsonValue]:
    output = {"artifact_id": f"artifact-{hashlib.sha256(candidate_bytes).hexdigest()[:12]}", "revision": llm_request["target_revision"], "content_sha256": hashlib.sha256(candidate_bytes).hexdigest(), "logical_ref": f"runtime:artifact/artifact-{hashlib.sha256(candidate_bytes).hexdigest()[:12]}"}
    result = {"llm_run_result_id": request["llm_run_result_id"], "schema_version": "1.0.0", "llm_run_request_id": llm_request["llm_run_request_id"], **{name: llm_request[name] for name in ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "worker_profile_id", "worker_profile_version", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_id", "tool_policy_version", "tool_policy_sha256", "input_sha256")}, "status": "succeeded", "started_at": request["started_at"], "finished_at": request["finished_at"], "token_usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}, "output": output}
    result["result_sha256"] = sha256(result)
    return result


def _hermes_result(
    request: dict[str, str],
    llm_request: dict[str, JsonValue],
    hermes: HermesRuntimeOutput,
) -> dict[str, JsonValue]:
    logical_refs = tuple(hermes.output_bytes_by_ref)
    outputs = hermes.output_set.outputs
    if len(logical_refs) != len(outputs):
        raise RuntimeProviderError("ERROR_LLM_RESULT_INVALID", "Hermes output references do not match the atomic output set.")
    output_records: list[dict[str, JsonValue]] = []
    for logical_ref, output in zip(logical_refs, outputs, strict=True):
        artifact_seed = hashlib.sha256(output.contract_id.encode("utf-8") + b"\0" + output.content_bytes).hexdigest()
        output_records.append({
            "artifact_id": f"artifact-{artifact_seed[:12]}",
            "revision": llm_request["target_revision"],
            "content_sha256": output.content_sha256,
            "logical_ref": logical_ref,
            "contract_id": output.contract_id,
        })
    result: dict[str, JsonValue] = {
        "llm_run_result_id": request["llm_run_result_id"],
        "schema_version": "1.2.0",
        "llm_run_request_id": llm_request["llm_run_request_id"],
        **{name: llm_request[name] for name in ("tenant_id", "project_id", "run_id", "step_id", "target_revision", "context_package_id", "context_package_sha256", "worker_profile_id", "worker_profile_version", "worker_profile_sha256", "provider_id", "model_id", "tool_policy_id", "tool_policy_version", "tool_policy_sha256", "input_sha256")},
        "provider_run_id": hermes.provider_run_id,
        "status": "succeeded",
        "started_at": hermes.started_at,
        "finished_at": hermes.finished_at,
        "token_usage": dict(hermes.token_usage),
        "outputs": output_records,
        "raw_output_sha256": hermes.raw_output_sha256,
        "evidence_refs": [dict(reference) for reference in hermes.evidence_refs],
        "observed_tool_calls": [
            {
                "call_id": call.call_id,
                "operation_id": call.operation_id,
                "tool_name": call.tool_name,
                "evidence_refs": [dict(reference) for reference in call.evidence_refs],
            }
            for call in hermes.observed_tool_calls
        ],
        "observed_delegations": [
            {
                "subagent_id": delegation.subagent_id,
                "purpose": delegation.purpose,
                "status": delegation.status,
            }
            for delegation in hermes.observed_delegations
        ],
        "lifecycle_events": [dict(event) for event in hermes.lifecycle_events],
    }
    result["result_sha256"] = sha256(result)
    return result
