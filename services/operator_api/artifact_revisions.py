from __future__ import annotations

import hashlib
import json
from difflib import unified_diff
from dataclasses import dataclass, field
from typing import Mapping

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import JsonValue

from .artifact_revision_repository import ArtifactRevisionRepository
from .artifact_revision_types import ArtifactRecord, ArtifactRevisionResult, ArtifactTransaction, DerivedView, build_artifact_record, output_set_payload_sha256
from .provider_outputs import ProviderOutput, ProviderOutputSet
from .recovery_inventory import RecoveryInventory, RecoveryReplayIdentity
from .repository import ProjectRepository, RepositoryError


class ArtifactRevisionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class ArtifactRevisionService:
    repository: ProjectRepository
    artifact_schema: dict[str, JsonValue]
    recovery_inventory: RecoveryInventory
    _repository: ArtifactRevisionRepository = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_repository", ArtifactRevisionRepository(self.repository))

    def _persist_validated_transaction(self, output_set: ProviderOutputSet, package_input_hash: str, quality_gate_runs: tuple[dict[str, JsonValue], ...], derived_views: Mapping[str, str]) -> ArtifactRevisionResult:
        transaction = self._transaction(output_set, package_input_hash, quality_gate_runs, derived_views)
        try:
            self._authorize_replay(transaction)
            with self._repository.lock(transaction.tenant_id, transaction.project_id, transaction.run_id, transaction.step_id):
                recovered = self._repository.recover(transaction)
                if recovered is not None:
                    return recovered
                run = self.repository.run(transaction.tenant_id, transaction.project_id, transaction.run_id)
                self._validate_current_parent(run, transaction)
                self._reject_released_parent(transaction)
                return self._repository.persist(transaction)
        except RepositoryError as exc:
            raise ArtifactRevisionError(exc.code, exc.message) from exc

    def _authorize_replay(self, transaction: ArtifactTransaction) -> None:
        path = self._repository._recovery_path(transaction)
        payload = self.repository._optional(transaction.tenant_id, transaction.project_id, path, None)
        if payload is None:
            self.recovery_inventory.authorize()
            return
        recovered = self._repository._transaction_from_sidecar(payload)
        if recovered.payload_sha256 != transaction.payload_sha256:
            raise ArtifactRevisionError("ERR_IDEMPOTENCY_CONFLICT", "Artifact recovery conflicts with the requested output.")
        self.recovery_inventory.authorize(RecoveryReplayIdentity(transaction.tenant_id, transaction.project_id, "artifact-recovery", path))

    def recover_output_set(self, tenant_id: str, project_id: str, run_id: str, step_id: str, idempotency_key: str) -> ArtifactRevisionResult:
        transaction = self._recovery_transaction(tenant_id, project_id, run_id, step_id, idempotency_key)
        try:
            with self._repository.lock(tenant_id, project_id, run_id, step_id):
                result = self._repository.recover(transaction)
                if result is None:
                    raise ArtifactRevisionError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery record is unavailable.")
                return result
        except RepositoryError as exc:
            raise ArtifactRevisionError(exc.code, exc.message) from exc

    def list_revisions(self, tenant_id: str, project_id: str, run_id: str, step_id: str) -> tuple[ArtifactRecord, ...]:
        try:
            run = self.repository.run(tenant_id, project_id, run_id)
            if run.get("step_id") != step_id:
                raise ArtifactRevisionError("ERROR_DOMAIN_REFERENCE_UNKNOWN", "Run does not bind the requested artifact step.")
            records = tuple(ArtifactRecord.model_validate(item) for item in self.repository.artifacts(tenant_id, project_id) if item.get("run_id") == run_id and item.get("step_id") == step_id)
            return tuple(sorted(records, key=lambda record: (record.revision, record.artifact_id)))
        except RepositoryError as exc:
            raise ArtifactRevisionError(exc.code, exc.message) from exc

    def artifact(self, tenant_id: str, project_id: str, artifact_id: str) -> ArtifactRecord:
        try:
            record = next((item for item in self.repository.artifacts(tenant_id, project_id) if item.get("artifact_id") == artifact_id), None)
            if record is None or record.get("tenant_id") != tenant_id or record.get("project_id") != project_id:
                raise ArtifactRevisionError("ERROR_DOMAIN_REFERENCE_UNKNOWN", "Artifact revision is unavailable.")
            return ArtifactRecord.model_validate(record)
        except RepositoryError as exc:
            raise ArtifactRevisionError(exc.code, exc.message) from exc

    def content_bytes(self, tenant_id: str, project_id: str, artifact_id: str) -> bytes:
        try:
            content = self._repository.content_bytes(tenant_id, project_id, artifact_id)
            record = self.artifact(tenant_id, project_id, artifact_id)
            if hashlib.sha256(content).hexdigest() != record.content_sha256:
                raise ArtifactRevisionError("ERR_STALE_REVISION", "Artifact content does not match its immutable revision hash.")
            return content
        except RepositoryError as exc:
            raise ArtifactRevisionError(exc.code, exc.message) from exc

    def text_diff(self, tenant_id: str, project_id: str, left_artifact_id: str, right_artifact_id: str) -> str:
        left = self.content_bytes(tenant_id, project_id, left_artifact_id)
        right = self.content_bytes(tenant_id, project_id, right_artifact_id)
        try:
            left_text = left.decode("utf-8")
            right_text = right.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ArtifactRevisionError("ERROR_ARTIFACT_CONTENT_UNSUPPORTED", "Artifact diff supports UTF-8 text only.") from exc
        return "".join(unified_diff(left_text.splitlines(keepends=True), right_text.splitlines(keepends=True), fromfile=left_artifact_id, tofile=right_artifact_id))

    def _transaction(self, output_set: ProviderOutputSet, package_input_hash: str, quality_gate_runs: tuple[dict[str, JsonValue], ...], derived_views: Mapping[str, str]) -> ArtifactTransaction:
        reference = output_set.primary
        digest = hashlib.sha256(json.dumps({"output_set_sha256": output_set_payload_sha256(output_set, package_input_hash), "quality_gate_runs": quality_gate_runs, "derived_views": dict(derived_views)}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        parents = self._parents(output_set)
        records = tuple(build_artifact_record(output, package_input_hash, parents) for output, parents in zip(output_set.outputs, parents, strict=True))
        for record in records:
            errors = tuple(Draft202012Validator(self.artifact_schema, format_checker=FormatChecker()).iter_errors(record.model_dump(mode="json")))
            if errors:
                raise ArtifactRevisionError("ERROR_CONTEXT_SCHEMA_INVALID", "Artifact revision does not satisfy its contract.")
        if quality_gate_runs and any(qgr.get("artifact_id") != records[0].artifact_id or qgr.get("artifact_sha256") != records[0].content_sha256 or qgr.get("artifact_revision") != records[0].revision for qgr in quality_gate_runs):
            raise ArtifactRevisionError("ERROR_QUALITY_GATE_BINDING_INVALID", "Machine quality-gate runs must bind the primary artifact revision.")
        views = tuple(DerivedView(artifact_id=records[0].artifact_id, name=name, content=content) for name, content in sorted(derived_views.items()))
        return ArtifactTransaction(tenant_id=reference.tenant_id, project_id=reference.project_id, run_id=reference.run_id, step_id=reference.step_id, idempotency_key=reference.idempotency_key, payload_sha256=digest, target_revision=reference.target_revision, records=records, contents=tuple(output.content_bytes for output in output_set.outputs), quality_gate_runs=quality_gate_runs, derived_views=views)

    def _parents(self, output_set: ProviderOutputSet) -> tuple[tuple[str, ...], ...]:
        reference = output_set.primary
        prior = [record for record in self.list_revisions(reference.tenant_id, reference.project_id, reference.run_id, reference.step_id) if record.revision == reference.parent_revision]
        if not prior:
            return tuple(() for _ in output_set.outputs)
        if len(prior) != len(output_set.outputs):
            raise ArtifactRevisionError("ERR_STALE_REVISION", "Current artifact lineage does not match the provider output set.")
        return tuple((record.artifact_id,) for record in prior)

    def _validate_current_parent(self, run: dict[str, JsonValue], transaction: ArtifactTransaction) -> None:
        if run.get("step_id") != transaction.step_id or run.get("input_hash") != transaction.records[0].input_hash:
            raise ArtifactRevisionError("ERROR_CONTEXT_SOURCE_INVALID", "Run does not bind this artifact output set.")
        if run.get("revision") != transaction.target_revision - 1:
            raise ArtifactRevisionError("ERR_STALE_REVISION", "Provider output set does not target the current parent revision.")

    def _reject_released_parent(self, transaction: ArtifactTransaction) -> None:
        root = self.repository._path(transaction.tenant_id, transaction.project_id, "releases")
        if not root.exists():
            return
        parent_ids = {artifact_id for record in transaction.records for artifact_id in record.parent_artifact_ids}
        for release_path in root.glob("*.json"):
            release = self.repository._required(transaction.tenant_id, transaction.project_id, f"releases/{release_path.name}")
            if release.get("status") == "released" and release.get("artifact_id") in parent_ids:
                raise ArtifactRevisionError("ERR_RELEASED_ARTIFACT_IMMUTABLE", "Released artifacts cannot be revised.")

    def _recovery_transaction(self, tenant_id: str, project_id: str, run_id: str, step_id: str, idempotency_key: str) -> ArtifactTransaction:
        placeholder = ArtifactTransaction(tenant_id=tenant_id, project_id=project_id, run_id=run_id, step_id=step_id, idempotency_key=idempotency_key, payload_sha256="0" * 64, target_revision=1, records=(), contents=())
        path = self._repository._recovery_path(placeholder)
        payload = self.repository._optional(tenant_id, project_id, path, None)
        if not isinstance(payload, dict):
            existing = self.repository._optional(tenant_id, project_id, self._repository._idempotency_path(placeholder), None)
            if not isinstance(existing, dict) or not isinstance(existing.get("payload_sha256"), str) or not isinstance(existing.get("records"), list):
                raise ArtifactRevisionError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery record is unavailable.")
            return ArtifactTransaction(tenant_id=tenant_id, project_id=project_id, run_id=run_id, step_id=step_id, idempotency_key=idempotency_key, payload_sha256=existing["payload_sha256"], target_revision=1, records=tuple(ArtifactRecord.model_validate(record) for record in existing["records"]), contents=())
        return self._repository._transaction_from_sidecar(payload)
