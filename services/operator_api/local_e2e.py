from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.runtime_contracts.llm_records import RuntimeContractValidator

from .artifact_revisions import ArtifactRevisionService
from .artifact_revision_types import ArtifactRevisionResult
from .models import JsonValue
from .provider_outputs import ProviderOutputSet
from .repository import ProjectRepository
from .recovery_inventory import RecoveryInventory
from .runtime import LocalRuntimeService, PreparedRuntimeStep
from .step_validation import GateContext, StepValidationService
from .validated_artifacts import ValidatedArtifactService


@dataclass(frozen=True, slots=True)
class LocalWorkflowService:
    repository: ProjectRepository
    root: Path
    runtime: LocalRuntimeService
    runtime_validator: RuntimeContractValidator
    worker_profile: dict[str, JsonValue]
    artifacts: ValidatedArtifactService
    recovery_inventory: RecoveryInventory

    @classmethod
    def from_root(
        cls,
        repository: ProjectRepository,
        root: Path,
        runtime: LocalRuntimeService,
        runtime_validator: RuntimeContractValidator,
        worker_profile: dict[str, JsonValue],
        artifact_schema: dict[str, JsonValue],
        recovery_inventory: RecoveryInventory,
    ) -> LocalWorkflowService:
        if runtime.recovery_inventory is not recovery_inventory:
            raise ValueError("Local workflow mutators must share one recovery inventory.")
        revisions = ArtifactRevisionService(repository, artifact_schema, recovery_inventory)
        artifacts = ValidatedArtifactService(StepValidationService.from_root(root), revisions)
        return cls(repository, root, runtime, runtime_validator, worker_profile, artifacts, recovery_inventory)

    def prepare_and_persist(
        self,
        request: dict[str, str],
        bundle: dict[str, JsonValue],
        gate_context: GateContext,
    ) -> tuple[PreparedRuntimeStep, ArtifactRevisionResult]:
        prepared = self.runtime.prepare_step(
            self.repository,
            self.root,
            self.runtime_validator,
            self.worker_profile,
            request,
        )
        enriched_bundle = dict(bundle)
        if prepared.provider_outputs.primary.step_id == "0":
            enriched_bundle["accepted_intake"] = self.repository.intake(request["tenant_id"], request["project_id"])
        persisted = self.artifacts.persist(
            prepared.provider_outputs,
            str(prepared.context_package["package_sha256"]),
            enriched_bundle,
            gate_context,
        )
        run = self.repository.run(request["tenant_id"], request["project_id"], request["run_id"])
        run["gate_context"] = gate_context.model_dump(mode="json")
        self.repository.write_run(request["tenant_id"], request["project_id"], run)
        return prepared, persisted
