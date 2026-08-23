"""Fail-fast validation for Step 2 keyword evidence candidates."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Mapping, TypeAlias

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from services.preflight_common import validate_lineage
from services.step2_preflight.provider_binding import validate_provider_binding


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

_ROOT = Path(__file__).resolve().parents[2]
_CANDIDATE_SCHEMA = json.loads(
    (_ROOT / "standards" / "outputs" / "step-2-keyword-evidence.schema.json").read_text(encoding="utf-8")
)
_CANDIDATE_VALIDATOR = Draft202012Validator(_CANDIDATE_SCHEMA, format_checker=FormatChecker())
_METRIC_FIELDS = frozenset(("search_volume", "difficulty", "cpc_usd"))
_CLASSIFICATION_FIELDS = frozenset(
    ("content_type", "geo_type", "engine_target", "category", "mandatory_location_policy")
)


def _rows(value: JsonValue | None) -> list[Mapping[str, JsonValue]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _candidate_rows(candidate: Mapping[str, JsonValue]) -> list[Mapping[str, JsonValue]]:
    pillars = candidate.get("pillars")
    if not isinstance(pillars, list):
        return []
    return [row for pillar in pillars if isinstance(pillar, dict) for row in _rows(pillar.get("rows"))]


def _error(code: str, message: str, path: list[str | int], remediation: str) -> dict[str, JsonValue]:
    return {"valid": False, "errors": [{"code": code, "message": message, "path": path, "remediation": remediation}]}


def _schema_error_key(error: ValidationError) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    return (
        tuple(str(segment) for segment in error.absolute_path),
        tuple(str(segment) for segment in error.absolute_schema_path),
        error.message,
    )


def _schema_error_code(error: ValidationError) -> str:
    path = tuple(str(segment) for segment in error.absolute_path)
    if error.validator in {"minItems", "maxItems"} and path[-1:] == ("rows",):
        return "ERROR_STEP2_PREFLIGHT"
    missing_field = error.message.removeprefix("'").removesuffix("' is a required property") if error.validator == "required" else ""
    fields = frozenset(field for field in _METRIC_FIELDS | _CLASSIFICATION_FIELDS if field in path or field == missing_field)
    if fields & _METRIC_FIELDS and error.validator in {"type", "minimum", "maximum", "oneOf", "anyOf"}:
        return "ERROR_STEP2_METRIC_INVALID"
    if fields & _CLASSIFICATION_FIELDS:
        return "ERROR_STEP2_CLASSIFICATION_INVALID"
    return "ERROR_STEP2_SCHEMA_INVALID"


def _schema_result(candidate: Mapping[str, JsonValue]) -> dict[str, JsonValue] | None:
    errors = sorted(_CANDIDATE_VALIDATOR.iter_errors(candidate), key=_schema_error_key)
    if not errors:
        return None
    error = errors[0]
    return _error(
        _schema_error_code(error),
        error.message,
        ["candidate", *list(error.absolute_path)],
        "Correct the named schema field and resubmit the closed Step 2 candidate.",
    )


def _evidence_coverage_result(candidate: Mapping[str, JsonValue], rows: list[Mapping[str, JsonValue]]) -> dict[str, JsonValue] | None:
    declared = candidate["evidence_ids"]
    row_evidence = [row["evidence_id"] for row in rows]
    if len(row_evidence) != len(set(row_evidence)):
        return _error(
            "ERROR_STEP2_PREFLIGHT",
            "Every verified keyword row must reference distinct provider evidence.",
            ["candidate", "pillars"],
            "Assign one distinct declared evidence_id to each verified row.",
        )
    if set(row_evidence) != set(declared):
        return _error(
            "ERROR_STEP2_PREFLIGHT",
            "Declared evidence_ids must exactly cover the verified keyword rows.",
            ["candidate", "evidence_ids"],
            "Declare every row evidence_id once and remove unreferenced evidence_ids.",
        )
    return None


def _pillar_result(bundle: Mapping[str, JsonValue], candidate: Mapping[str, JsonValue]) -> dict[str, JsonValue] | None:
    pillars = candidate["pillars"]
    approved_value = bundle.get("approved_pillar_ids")
    approved = approved_value if isinstance(approved_value, list) else [pillar["pillar_id"] for pillar in pillars]
    verified_by_pillar = Counter(
        pillar["pillar_id"]
        for pillar in pillars
        for row in _rows(pillar["rows"])
        if row["status"] == "verified"
    )
    if any(not isinstance(pillar_id, str) or not 25 <= verified_by_pillar[pillar_id] <= 40 for pillar_id in approved):
        return _error(
            "ERROR_STEP2_PREFLIGHT",
            "Each approved pillar requires 25 to 40 verified provider-evidence rows.",
            ["candidate", "pillars"],
            "Submit 25 to 40 verified rows for every approved pillar.",
        )
    for pillar in pillars:
        approved_families = set(pillar["approved_category_families"])
        categories = {row["category"] for row in _rows(pillar["rows"])}
        if not categories <= approved_families or not approved_families <= categories:
            return _error(
                "ERROR_STEP2_CATEGORY_FAMILY_COVERAGE",
                "Every row category must be an approved family and every approved family requires a verified row.",
                ["candidate", "pillars", pillar["pillar_id"], "approved_category_families"],
                "Use only approved category families and add a verified row for each declared family.",
            )
    return None


def _candidate(bundle: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    value = bundle.get("candidate")
    return value if isinstance(value, dict) else bundle


def validate_step2_candidate(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    candidate = _candidate(bundle)
    schema_result = _schema_result(candidate)
    if schema_result is not None:
        return schema_result
    rows = _candidate_rows(candidate)
    evidence_result = _evidence_coverage_result(candidate, rows)
    if evidence_result is not None:
        return evidence_result
    pillar_result = _pillar_result(bundle, candidate)
    if pillar_result is not None:
        return pillar_result
    return {"valid": True, "errors": []}


def validate_step2_preflight(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    result = validate_step2_candidate(bundle)
    if not result["valid"]:
        return result
    lineage_errors = validate_lineage(dict(bundle), "2", "1c", "GATE-1C", candidate_schema_name="step-2-keyword-evidence.schema.json")
    if lineage_errors:
        return {"valid": False, "errors": lineage_errors}
    candidate = _candidate(bundle)
    binding_message = validate_provider_binding(bundle, candidate, _candidate_rows(candidate))
    if binding_message is not None:
        return _error(
            "ERROR_STEP2_PROVIDER_BINDING",
            binding_message,
            ["provider_evidence_records"],
            "Submit one schema-valid provider exchange per evidence_id with exact normalized row metrics and unique exchange identities.",
        )
    return result
