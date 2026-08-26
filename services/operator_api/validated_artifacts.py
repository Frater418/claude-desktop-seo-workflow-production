from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from pydantic import JsonValue

from .artifact_revision_types import ArtifactRevisionResult
from .artifact_revisions import ArtifactRevisionService
from .provider_outputs import ProviderOutputSet
from .step_validation import GateContext, StepValidationService


@dataclass(frozen=True, slots=True)
class ValidatedArtifactService:
    validation: StepValidationService
    revisions: ArtifactRevisionService

    def persist(
        self,
        output_set: ProviderOutputSet,
        package_input_hash: str,
        bundle: Mapping[str, JsonValue],
        gate_context: GateContext,
    ) -> ArtifactRevisionResult:
        validated = self.validation.validate(output_set, package_input_hash, bundle, gate_context)
        return self.revisions._persist_validated_transaction(
            output_set,
            package_input_hash,
            validated.artifact_records,
            validated.supporting_artifacts,
            validated.quality_gate_runs,
            validated.derived_views,
            validated.next_run,
        )
