"""Portable loader for the repository-local JSON-LD validator."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import runpy
from typing import Callable, cast


ValidationResult = dict[str, object]
ValidationFunction = Callable[[str, bool], ValidationResult]


class JsonLdValidatorAdapterError(RuntimeError):
    """Structured failure for an unavailable local validator artifact."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@lru_cache(maxsize=8)
def _load_validator(path_text: str) -> ValidationFunction:
    path = Path(path_text)
    if not path.is_file():
        raise JsonLdValidatorAdapterError(
            "ERROR_JSONLD_VALIDATOR_UNAVAILABLE",
            "The repository-local JSON-LD validator file is unavailable.",
        )
    try:
        namespace = runpy.run_path(str(path))
    except Exception as exc:
        raise JsonLdValidatorAdapterError(
            "ERROR_JSONLD_VALIDATOR_UNAVAILABLE",
            "The repository-local JSON-LD validator could not be loaded.",
        ) from exc
    validator = namespace.get("validate_text")
    if not callable(validator):
        raise JsonLdValidatorAdapterError(
            "ERROR_JSONLD_VALIDATOR_UNAVAILABLE",
            "The repository-local JSON-LD validator has no validate_text entry point.",
        )
    return cast(ValidationFunction, validator)


def validate_local_jsonld_text(
    text: str,
    strict_geo: bool = False,
    *,
    root: Path | None = None,
) -> ValidationResult:
    """Validate text without importing through the external mcp package name."""
    project_root = root or Path(__file__).resolve().parents[1]
    validator_path = project_root / "mcp" / "tools" / "validate_schema_jsonld.py"
    validator = _load_validator(str(validator_path.resolve()))
    result = validator(text, strict_geo)
    if not isinstance(result, dict):
        raise JsonLdValidatorAdapterError(
            "ERROR_JSONLD_VALIDATOR_UNAVAILABLE",
            "The repository-local JSON-LD validator returned an invalid result.",
        )
    return result
