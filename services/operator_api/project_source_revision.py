from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from services.runtime_contracts.llm_records import RuntimeContractValidator

from .models import JsonValue


class ProjectSourceRevisionError(RuntimeError):
    pass


def build_logical_session_revision(
    current: dict[str, JsonValue],
    *,
    intake_sha256: str,
    actor_id: str,
    created_at: str,
    repository_root: Path,
) -> dict[str, JsonValue]:
    project_source = current.get("project_source")
    if not isinstance(project_source, dict):
        raise ProjectSourceRevisionError("Logical project session has no canonical project source.")
    if project_source.get("content_sha256") == intake_sha256:
        result = copy.deepcopy(current)
    else:
        logical_session_id = current.get("logical_session_id")
        session_revision = current.get("session_revision")
        source_revision = project_source.get("revision")
        if (
            not isinstance(logical_session_id, str)
            or not isinstance(session_revision, int)
            or isinstance(session_revision, bool)
            or not isinstance(source_revision, int)
            or isinstance(source_revision, bool)
        ):
            raise ProjectSourceRevisionError("Logical project session revision identity is invalid.")
        source_id = f"intake-{intake_sha256[:12]}"
        result = {
            "logical_session_id": f"logical-session-{intake_sha256[:24]}",
            "schema_version": "1.0.0",
            "session_revision": session_revision + 1,
            "tenant_id": current["tenant_id"],
            "project_id": current["project_id"],
            "binding_mode": "project_intake",
            "project_source": {
                "source_kind": "project_intake",
                "source_id": source_id,
                "revision": source_revision + 1,
                "logical_ref": f"runtime:intake/{source_id}",
                "content_sha256": intake_sha256,
            },
            "created_at": created_at,
            "created_by": actor_id,
            "state_authority": "local_core",
            "technical_session_policy": copy.deepcopy(current["technical_session_policy"]),
            "supersedes_logical_session_id": logical_session_id,
        }
    schema = _read_object(repository_root / "standards/runtime/logical-project-session.schema.json")
    validation = RuntimeContractValidator({"logical-project-session": schema}, {}).validate(
        "logical-project-session",
        result,
    )
    if not validation.valid:
        codes = ", ".join(error.code for error in validation.errors)
        raise ProjectSourceRevisionError(f"Upgraded logical project session is invalid: {codes}.")
    return result


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProjectSourceRevisionError("Logical project session schema cannot be read.") from error
    if not isinstance(value, dict):
        raise ProjectSourceRevisionError("Logical project session schema is malformed.")
    return value
