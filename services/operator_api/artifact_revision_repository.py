from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .artifact_revision_types import ArtifactRecord, ArtifactRevisionResult, ArtifactTransaction
from .models import JsonValue
from .repository import ProjectRepository, RepositoryError
from services.owned_file_lock import OwnedFileLock, OwnedFileLockError


class ArtifactRevisionRepository:
    """Persist immutable revision transactions through artifact-recovery sidecars."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._project = repository

    @contextmanager
    def lock(self, tenant_id: str, project_id: str, run_id: str, step_id: str) -> Iterator[None]:
        path = self._project._path(tenant_id, project_id, f"artifact-revision-locks/{run_id}--{step_id}.lock")
        try:
            with OwnedFileLock(path, grace_seconds=0):
                yield
        except OwnedFileLockError as exc:
            raise RepositoryError("ERR_CONCURRENT_PARENT_CONFLICT", "The current artifact parent is being revised.") from exc

    def idempotent_result(self, transaction: ArtifactTransaction) -> ArtifactRevisionResult | None:
        payload = self._project._optional(transaction.tenant_id, transaction.project_id, self._idempotency_path(transaction), None)
        if payload is None:
            return None
        if not isinstance(payload, dict) or payload.get("payload_sha256") != transaction.payload_sha256:
            raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Artifact idempotency key conflicts with stored output.")
        records = payload.get("records")
        if not isinstance(records, list):
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact idempotency record is malformed.")
        return ArtifactRevisionResult(records=tuple(ArtifactRecord.model_validate(record) for record in records), quality_gate_runs=tuple(payload.get("quality_gate_runs", ())), derived_views=tuple(payload.get("derived_views", ())))

    def recover(self, transaction: ArtifactTransaction) -> ArtifactRevisionResult | None:
        existing = self.idempotent_result(transaction)
        payload = self._project._optional(transaction.tenant_id, transaction.project_id, self._recovery_path(transaction), None)
        if existing is not None and payload is None:
            return existing
        if payload is None:
            return None
        recovered = self._transaction_from_sidecar(payload)
        if recovered.payload_sha256 != transaction.payload_sha256:
            raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Artifact recovery conflicts with the requested output.")
        return self._materialize(recovered)

    def persist(self, transaction: ArtifactTransaction) -> ArtifactRevisionResult:
        existing = self.idempotent_result(transaction)
        if existing is not None:
            return existing
        before = {
            "artifacts": self._project.artifacts(transaction.tenant_id, transaction.project_id),
            "gates": self._project.quality_gate_runs(transaction.tenant_id, transaction.project_id),
            "run": self._project.run(transaction.tenant_id, transaction.project_id, transaction.run_id),
        }
        sidecar = self._sidecar(transaction)
        sidecar["before"] = before
        self._project._write(transaction.tenant_id, transaction.project_id, self._recovery_path(transaction), sidecar)
        try:
            return self._materialize(transaction)
        except RepositoryError:
            self._restore_visible_projections(transaction, before)
            raise

    def content_bytes(self, tenant_id: str, project_id: str, artifact_id: str) -> bytes:
        self._validate_artifact_id(artifact_id)
        path = self._content_path(tenant_id, project_id, artifact_id)
        try:
            if path.is_symlink() or not path.is_file():
                raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact content is not a regular file.")
            return path.read_bytes()
        except OSError as exc:
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact content is unavailable.") from exc

    def _materialize(self, transaction: ArtifactTransaction) -> ArtifactRevisionResult:
        try:
            for record, content in zip(transaction.records, transaction.contents, strict=True):
                self._write_once_content(transaction.tenant_id, transaction.project_id, record.artifact_id, content)
            for view in transaction.derived_views:
                self._write_once_view(transaction.tenant_id, transaction.project_id, view.artifact_id, view.name, view.content)
            existing = self._project.artifacts(transaction.tenant_id, transaction.project_id)
            records = [record.model_dump(mode="json") for record in transaction.records]
            self._project._write(transaction.tenant_id, transaction.project_id, "artifacts.json", _append_records(existing, records))
            if transaction.quality_gate_runs:
                gates = self._project.quality_gate_runs(transaction.tenant_id, transaction.project_id)
                self._project._write(transaction.tenant_id, transaction.project_id, "gates.json", _append_records(gates, list(transaction.quality_gate_runs), "quality_gate_run_id"))
            run = self._project.run(transaction.tenant_id, transaction.project_id, transaction.run_id)
            run["revision"] = transaction.target_revision
            self._project.write_run(transaction.tenant_id, transaction.project_id, run)
            self._project._write(transaction.tenant_id, transaction.project_id, self._idempotency_path(transaction), {"payload_sha256": transaction.payload_sha256, "records": records, "quality_gate_runs": list(transaction.quality_gate_runs), "derived_views": [view.model_dump(mode="json") for view in transaction.derived_views]})
            try:
                self._remove_if_present(transaction)
            except OSError:
                pass
        except RepositoryError:
            raise
        except OSError as exc:
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact transaction cannot be materialized.") from exc
        return ArtifactRevisionResult(records=transaction.records, quality_gate_runs=transaction.quality_gate_runs, derived_views=transaction.derived_views)

    def _write_once_content(self, tenant_id: str, project_id: str, artifact_id: str, content: bytes) -> None:
        path = self._content_path(tenant_id, project_id, artifact_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
                    raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Immutable artifact content conflicts with stored bytes.")
                return
            _atomic_write(path, content)
        except RepositoryError:
            raise
        except OSError as exc:
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact content cannot be written.") from exc

    def _write_once_view(self, tenant_id: str, project_id: str, artifact_id: str, name: str, content: str) -> None:
        path = self._project._path(tenant_id, project_id, f"artifact-views/{artifact_id}/{name}")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            encoded = content.encode("utf-8")
            if path.exists():
                if path.is_symlink() or not path.is_file() or path.read_bytes() != encoded:
                    raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Derived artifact view conflicts with stored bytes.")
                return
            _atomic_write(path, encoded)
        except RepositoryError:
            raise
        except OSError as exc:
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Derived artifact view cannot be written.") from exc

    def _restore_visible_projections(self, transaction: ArtifactTransaction, before: dict[str, JsonValue]) -> None:
        artifacts, gates, run = before["artifacts"], before["gates"], before["run"]
        if not isinstance(artifacts, list) or not isinstance(gates, list) or not isinstance(run, dict):
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery snapshot is malformed.")
        self._project._write(transaction.tenant_id, transaction.project_id, "artifacts.json", artifacts)
        if transaction.quality_gate_runs:
            self._project._write(transaction.tenant_id, transaction.project_id, "gates.json", gates)
        self._project.write_run(transaction.tenant_id, transaction.project_id, run)
        for view in transaction.derived_views:
            path = self._project._path(transaction.tenant_id, transaction.project_id, f"artifact-views/{view.artifact_id}/{view.name}")
            if path.exists():
                self._project._remove(transaction.tenant_id, transaction.project_id, f"artifact-views/{view.artifact_id}/{view.name}")

    def _transaction_from_sidecar(self, payload: JsonValue) -> ArtifactTransaction:
        if not isinstance(payload, dict):
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery record is malformed.")
        contents = payload.get("contents")
        if not isinstance(contents, list) or not all(isinstance(content, str) for content in contents):
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery content is malformed.")
        try:
            return ArtifactTransaction.model_validate({key: value for key, value in payload.items() if key != "before"} | {"contents": tuple(base64.b64decode(content, validate=True) for content in contents)})
        except (ValueError, TypeError) as exc:
            raise RepositoryError("ERROR_ARTIFACT_PERSISTENCE", "Artifact recovery record is malformed.") from exc

    def _sidecar(self, transaction: ArtifactTransaction) -> dict[str, JsonValue]:
        payload = transaction.model_dump(mode="json", exclude={"contents"})
        payload["contents"] = [base64.b64encode(content).decode("ascii") for content in transaction.contents]
        return payload

    def _content_path(self, tenant_id: str, project_id: str, artifact_id: str) -> Path:
        return self._project._path(tenant_id, project_id, f"artifact-content/{artifact_id}.md")

    @staticmethod
    def _validate_artifact_id(artifact_id: str) -> None:
        if not artifact_id.startswith("artifact-") or not artifact_id.replace("-", "").isalnum():
            raise RepositoryError("ERR_TENANT_ISOLATION", "Artifact identity is invalid.")

    @staticmethod
    def _transaction_key(transaction: ArtifactTransaction) -> str:
        return hashlib.sha256(f"{transaction.run_id}|{transaction.step_id}|{transaction.idempotency_key}".encode()).hexdigest()

    def _recovery_path(self, transaction: ArtifactTransaction) -> str:
        return f"artifact-recovery/{self._transaction_key(transaction)}.json"

    def _idempotency_path(self, transaction: ArtifactTransaction) -> str:
        return f"artifact-idempotency/{self._transaction_key(transaction)}.json"

    def _remove_if_present(self, transaction: ArtifactTransaction) -> None:
        path = self._project._path(transaction.tenant_id, transaction.project_id, self._recovery_path(transaction))
        if path.exists():
            self._project._remove(transaction.tenant_id, transaction.project_id, self._recovery_path(transaction))



def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _append_records(existing: list[dict[str, JsonValue]], records: list[dict[str, JsonValue]], identity: str = "artifact_id") -> list[dict[str, JsonValue]]:
    by_id = {record.get(identity): record for record in existing}
    for record in records:
        record_id = record[identity]
        current = by_id.get(record_id)
        if current is not None and current != record:
            raise RepositoryError("ERR_IDEMPOTENCY_CONFLICT", "Artifact transaction record conflicts with stored metadata.")
        by_id[record_id] = record
    existing_ids = {item.get(identity) for item in existing}
    return [*existing, *(record for record in records if record[identity] not in existing_ids)]
