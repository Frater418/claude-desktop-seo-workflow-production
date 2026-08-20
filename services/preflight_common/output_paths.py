"""Controlled V2 derived-output destinations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_DESTINATIONS = {
    "1c_css": "v2/outputs/step1c/design-system.v1.css",
    "1c_template": "v2/outputs/step1c/templates/{identifier}.v1.html",
    "2": "v2/outputs/step2/keyword-evidence.v1.csv",
    "3": "v2/outputs/step3/plan.v1.md",
    "3b": "v2/outputs/step3b/adjustments/{identifier}.v1.md",
    "4a": "v2/outputs/step4a/briefings/{identifier}.v1.md",
    "4b": "v2/outputs/step4b/pages/{identifier}.v1.html",
}


@dataclass(frozen=True, slots=True)
class OutputPathError(RuntimeError):
    """Stable error raised for a rejected controlled output destination."""

    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def resolve_step_output(workspace_root: Path, step: str, identifier: str = "") -> Path:
    """Return the sole permitted V2 destination without creating it."""
    destination_template = _DESTINATIONS.get(step)
    if destination_template is None:
        raise OutputPathError("ERROR_OUTPUT_STEP_UNKNOWN", "Renderer step has no controlled V2 destination.")
    if "{identifier}" in destination_template and _IDENTIFIER.fullmatch(identifier) is None:
        raise OutputPathError("ERROR_OUTPUT_IDENTIFIER_INVALID", "Output identifier must be a portable lowercase slug.")
    if "{identifier}" not in destination_template and identifier:
        raise OutputPathError("ERROR_OUTPUT_IDENTIFIER_INVALID", "This renderer does not accept an output identifier.")
    try:
        root = workspace_root.resolve(strict=True)
    except OSError as exc:
        raise OutputPathError("ERROR_OUTPUT_ROOT_INVALID", "Customer workspace root must be an accessible directory.") from exc
    if not root.is_dir():
        raise OutputPathError("ERROR_OUTPUT_ROOT_INVALID", "Customer workspace root must be an existing directory.")
    output = root / destination_template.format(identifier=identifier)
    _reject_symlink_components(root, output)
    try:
        output.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise OutputPathError("ERROR_OUTPUT_PATH_ESCAPE", "Derived output escapes the controlled workspace root.") from exc
    if output.exists():
        raise OutputPathError("ERROR_OUTPUT_EXISTS", "Derived output already exists and cannot be overwritten.")
    return output


def prepare_step_output(workspace_root: Path, step: str, identifier: str = "") -> Path:
    """Create the verified controlled parent directory and return a new destination."""
    output = resolve_step_output(workspace_root, step, identifier)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _reject_symlink_components(root: Path, output: Path) -> None:
    """Reject existing symlink or Windows reparse-point components before writes."""
    current = root
    for component in output.relative_to(root).parts[:-1]:
        current = current / component
        if current.exists() and (current.is_symlink() or current.resolve() != current.absolute()):
            raise OutputPathError("ERROR_OUTPUT_PATH_ESCAPE", "Derived output traverses a symlink or reparse point.")
