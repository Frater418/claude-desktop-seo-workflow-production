from __future__ import annotations

from dataclasses import dataclass
import json
import posixpath

from .role_packages import RolePackage
from .record_normalization import CanonicalRecord, DeliveryInventoryError


@dataclass(frozen=True, slots=True)
class RenderedRoleFile:
    path: str
    content: bytes


def render_role_package(package: RolePackage) -> tuple[RenderedRoleFile, ...]:
    prefix = f"{package.role}-handoff"
    files = (
        RenderedRoleFile(f"{prefix}/ROLE_INDEX.md", _index(package, prefix).encode("utf-8")),
        RenderedRoleFile(f"{prefix}/TASK_SUMMARY.md", _tasks(package, prefix).encode("utf-8")),
        RenderedRoleFile(f"{prefix}/role-handoff-manifest.json", (json.dumps(package.manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")),
    )
    if len({item.path for item in files}) != len(files) or {item.path for item in files}.intersection(item.output_path for item in package.artifacts):
        raise DeliveryInventoryError("ROLE_RENDER_PATH_CONFLICT", "Generated role handoff paths conflict with selected artifact paths.")
    return files


def _index(package: RolePackage, prefix: str) -> str:
    lines = [f"# {package.role.title()} Handoff", "", "This index references canonical selected delivery artifacts.", "", "| Step | Release state | Artifact | Path |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {_cell(item.step_id)} | {_cell(item.release_status)} | {_cell(item.artifact_id)} | [{_cell(item.output_path)}]({_link(prefix, item.output_path)}) |" for item in package.artifacts)
    lines.extend(["", "## Review Requirements", "", "| Review | Status | Requirements | Technical QA and Staging |", "| --- | --- | --- | --- |"])
    lines.extend(_record_row(item, ("requirements", "instructions", "description", "title"), ("technical_qa", "staging_requirements")) for item in package.reviews)
    lines.extend(["", "## Blockers", "", "| Blocker | Status | Instructions |", "| --- | --- | --- |"])
    lines.extend(_blocker_row(item) for item in package.blockers)
    return "\n".join(lines) + "\n"


def _tasks(package: RolePackage, prefix: str) -> str:
    tasks = {item.record_id: item for item in package.tasks}
    lines = [f"# {package.role.title()} Task Summary", "", "Core task status is read-only history. Assignment priority and deadline are referenced below.", "", "| Task | Status | Priority | Deadline | Assignment | Assignee |", "| --- | --- | --- | --- | --- | --- |"]
    for assignment in package.assignments:
        task = tasks[str(assignment.payload["task_id"])]
        assignee = assignment.payload.get("assignee_id")
        assignee_text = str(assignee) if isinstance(assignee, str) and assignee else f"unresolved:{assignment.record_id}"
        priority = _value(assignment, "priority") or _value(task, "priority")
        deadline = _value(assignment, "deadline") or _value(task, "due_at")
        lines.append(f"| {_cell(task.record_id)} | {_cell(_value(task, 'status'))} | {_cell(priority)} | {_cell(deadline)} | {_cell(assignment.record_id)} | {_cell(assignee_text)} |")
    lines.extend(["", "## Manifest", "", f"[role-handoff-manifest.json]({_link(prefix, f'{prefix}/role-handoff-manifest.json')})"])
    return "\n".join(lines) + "\n"


def _value(record: CanonicalRecord, name: str) -> str:
    value = record.payload.get(name)
    return value if isinstance(value, str) else ""


def _record_row(record: CanonicalRecord, requirement_fields: tuple[str, ...], qa_fields: tuple[str, ...]) -> str:
    return f"| {_cell(record.record_id)} | {_cell(_value(record, 'status'))} | {_cell(_joined(record, requirement_fields))} | {_cell(_joined(record, qa_fields))} |"


def _blocker_row(record: CanonicalRecord) -> str:
    return f"| {_cell(record.record_id)} | {_cell(_value(record, 'status'))} | {_cell(_joined(record, ('instructions', 'description', 'title')))} |"


def _joined(record: CanonicalRecord, fields: tuple[str, ...]) -> str:
    return "; ".join(value for field in fields if (value := _value(record, field)))


def _link(prefix: str, target: str) -> str:
    return posixpath.relpath(target, start=prefix)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


__all__ = ["RenderedRoleFile", "render_role_package"]
