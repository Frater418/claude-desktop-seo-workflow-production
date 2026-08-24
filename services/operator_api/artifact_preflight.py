from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from .artifact_revision_types import ArtifactIdentity, ArtifactRecord, DerivedView, artifact_id_for
from .artifact_revisions import ArtifactRevisionError, ArtifactRevisionService
from .package4 import Package4Error
from .provider_outputs import ProviderOutput, ProviderOutputSet
from .step_validation import GateContext, StepValidationError, StepValidationService


_STEP4_IDS: Final = frozenset(("4a", "4b"))


class ArtifactValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    revision: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    supporting_documents: tuple[dict[str, JsonValue], ...]
    bundle: dict[str, JsonValue]
    gate_context: GateContext


class ArtifactPreflightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    revision: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    step_id: Literal["4a", "4b"]
    validation_mode: Literal["step_preflight"] = "step_preflight"
    valid: Literal[True] = True
    quality_gate_runs: tuple[dict[str, JsonValue], ...]
    derived_views: tuple[DerivedView, ...]


@dataclass(frozen=True, slots=True)
class ArtifactPreflightService:
    revisions: ArtifactRevisionService
    validation: StepValidationService

    def validate(
        self,
        tenant_id: str,
        project_id: str,
        artifact_id: str,
        request: ArtifactValidationRequest,
    ) -> ArtifactPreflightResponse:
        try:
            primary_record = self.revisions.artifact(tenant_id, project_id, artifact_id)
            primary_bytes = self.revisions.content_bytes(tenant_id, project_id, artifact_id)
        except ArtifactRevisionError as exc:
            raise Package4Error(exc.code, exc.message) from exc
        self._verify_primary(primary_record, primary_bytes, request)
        contracts = _contracts_for_step(self.validation.prompt_registry, primary_record.step_id)
        records, contents = self._immutable_output_set(tenant_id, project_id, primary_record, primary_bytes, contracts, request)
        output_set = _provider_outputs(self.validation.prompt_registry, primary_record, contracts, records, contents)
        try:
            result = self.validation.validate(output_set, primary_record.input_hash, request.bundle, request.gate_context)
        except StepValidationError as exc:
            raise Package4Error(exc.code, exc.message) from exc
        proposed = result.artifact_records[0]
        if (proposed.artifact_id, proposed.revision, proposed.content_sha256) != (
            primary_record.artifact_id,
            primary_record.revision,
            primary_record.content_sha256,
        ):
            raise Package4Error("ERR_STALE_REVISION", "Preflight output does not bind the requested immutable artifact.")
        return ArtifactPreflightResponse(
            artifact_id=primary_record.artifact_id,
            revision=primary_record.revision,
            content_sha256=primary_record.content_sha256,
            step_id=primary_record.step_id,
            quality_gate_runs=result.quality_gate_runs,
            derived_views=tuple(
                DerivedView(artifact_id=primary_record.artifact_id, name=name, content=content)
                for name, content in sorted(result.derived_views.items())
            ),
        )

    def _verify_primary(
        self,
        record: ArtifactRecord,
        content: bytes,
        request: ArtifactValidationRequest,
    ) -> None:
        if record.step_id not in _STEP4_IDS:
            raise Package4Error("ERROR_STEP_PREFLIGHT_UNSUPPORTED", "Artifact preflight supports Step 4A and Step 4B only.")
        if (record.revision, record.content_sha256) != (request.revision, request.content_sha256):
            raise Package4Error("ERR_STALE_REVISION", "Artifact preflight must bind the exact revision and hash.")
        if hashlib.sha256(content).hexdigest() != request.content_sha256:
            raise Package4Error("ERR_STALE_REVISION", "Artifact content does not match its immutable revision hash.")

    def _immutable_output_set(
        self,
        tenant_id: str,
        project_id: str,
        primary: ArtifactRecord,
        primary_bytes: bytes,
        contracts: tuple[str, ...],
        request: ArtifactValidationRequest,
    ) -> tuple[tuple[ArtifactRecord, ...], tuple[bytes, ...]]:
        expected_primary = artifact_id_for(ArtifactIdentity(
            contract_id=contracts[0], tenant_id=tenant_id, project_id=project_id,
            run_id=primary.run_id, step_id=primary.step_id, revision=primary.revision,
        ))
        if primary.artifact_id != expected_primary:
            raise Package4Error("ERROR_OUTPUT_CONTRACT_INVALID", "Route artifact is not the registered primary contract artifact.")
        if len(request.supporting_documents) != len(contracts) - 1:
            raise Package4Error("ERROR_OUTPUT_CONTRACT_INVALID", "Supporting documents do not match the registered output count.")
        records = [primary]
        contents = [primary_bytes]
        for contract_id, caller_document in zip(contracts[1:], request.supporting_documents, strict=True):
            sibling_id = artifact_id_for(ArtifactIdentity(contract_id=contract_id, tenant_id=primary.tenant_id, project_id=primary.project_id, run_id=primary.run_id, step_id=primary.step_id, revision=primary.revision))
            try:
                sibling = self.revisions.artifact(tenant_id, project_id, sibling_id)
                sibling_bytes = self.revisions.content_bytes(tenant_id, project_id, sibling_id)
            except ArtifactRevisionError as exc:
                raise Package4Error(exc.code, exc.message) from exc
            if not _same_revision_identity(primary, sibling) or _canonical_json_bytes(caller_document) != sibling_bytes:
                raise Package4Error("ERR_STALE_REVISION", "Supporting document does not match its immutable sibling artifact.")
            records.append(sibling)
            contents.append(sibling_bytes)
        return tuple(records), tuple(contents)


def _contracts_for_step(registry: Mapping[str, JsonValue], step_id: str) -> tuple[str, ...]:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise Package4Error("ERROR_REGISTRY_INVALID", "Output-contract registry entries are unavailable.")
    selected = [entry for entry in entries if isinstance(entry, dict) and entry.get("step_id") == step_id and entry.get("active") is True]
    if len(selected) != 1 or not isinstance(selected[0].get("output_contracts"), list):
        raise Package4Error("ERROR_REGISTRY_INVALID", "Expected one active output-contract registry entry.")
    contracts = tuple(contract.get("contract_id") for contract in selected[0]["output_contracts"] if isinstance(contract, dict))
    if not contracts or len(contracts) != len(selected[0]["output_contracts"]) or not all(isinstance(contract, str) and contract for contract in contracts):
        raise Package4Error("ERROR_REGISTRY_INVALID", "Registered output contracts are invalid.")
    return contracts


def _same_revision_identity(primary: ArtifactRecord, sibling: ArtifactRecord) -> bool:
    return (
        sibling.tenant_id, sibling.project_id, sibling.run_id, sibling.step_id, sibling.revision,
        sibling.input_hash, sibling.created_at,
    ) == (
        primary.tenant_id, primary.project_id, primary.run_id, primary.step_id, primary.revision,
        primary.input_hash, primary.created_at,
    )


def _provider_outputs(
    registry: Mapping[str, JsonValue],
    primary: ArtifactRecord,
    contracts: tuple[str, ...],
    records: tuple[ArtifactRecord, ...],
    contents: tuple[bytes, ...],
) -> ProviderOutputSet:
    if primary.revision < 2:
        raise Package4Error("ERROR_ARTIFACT_PREFLIGHT_LEGACY_UNSUPPORTED", "Artifact revision cannot satisfy the provider output revision contract.")
    try:
        created_at = datetime.fromisoformat(primary.created_at.replace("Z", "+00:00"))
        key = f"preflight-{hashlib.sha256(primary.artifact_id.encode('ascii')).hexdigest()[:32]}"
        outputs = tuple(
            ProviderOutput(
                contract_id=contract_id, content_bytes=content, content_sha256=record.content_sha256,
                content_type="application/json", tenant_id=record.tenant_id, project_id=record.project_id,
                run_id=record.run_id, step_id=record.step_id, idempotency_key=key,
                parent_revision=record.revision - 1, target_revision=record.revision, created_at=created_at,
            )
            for contract_id, record, content in zip(contracts, records, contents, strict=True)
        )
        return ProviderOutputSet.from_registry(dict(registry), primary=outputs[0], supporting=outputs[1:])
    except (ValidationError, ValueError) as exc:
        raise Package4Error("ERROR_OUTPUT_CONTRACT_INVALID", "Immutable artifact cannot be reconstructed as a provider output set.") from exc


def _canonical_json_bytes(document: dict[str, JsonValue]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
