"""Fail-fast validation for Step 2 keyword evidence candidates."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Mapping, TypeAlias

from jsonschema import Draft202012Validator, FormatChecker
from services.preflight_common import validate_lineage
from services.provider_gateway.core import ProviderGatewayError, validate_exchange


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


def _rows(value: JsonValue | None) -> list[Mapping[str, JsonValue]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _candidate_rows(candidate: Mapping[str, JsonValue]) -> list[Mapping[str, JsonValue]]:
    pillars = candidate.get("pillars")
    if not isinstance(pillars, list):
        return []
    return [row for pillar in pillars if isinstance(pillar, dict) for row in _rows(pillar.get("rows"))]


def _invalid(message: str) -> dict[str, JsonValue]:
    return {"valid": False, "errors": [{"code": "ERROR_STEP2_PREFLIGHT", "message": message, "path": ["candidate"], "remediation": "Submit declared, completed provider-gateway evidence for every verified row."}]}


def validate_step2_candidate(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Return one operator-surface error when keyword evidence is incomplete."""
    candidate = bundle.get("candidate") if isinstance(bundle.get("candidate"), dict) else bundle
    schema_path = Path(__file__).resolve().parents[2] / "standards" / "outputs" / "step-2-keyword-evidence.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(candidate))
    pillars = candidate.get("pillars") if isinstance(candidate, dict) else None
    if schema_errors or not isinstance(pillars, list) or not pillars:
        return _invalid("Step 2 requires a closed awaiting-gate canonical candidate with approved pillars.")
    if not isinstance(candidate, dict):
        return _invalid("Step 2 candidate must be an object.")
    rows = _candidate_rows(candidate)
    declared_evidence = candidate.get("evidence_ids")
    declared = set(declared_evidence) if isinstance(declared_evidence, list) else set()
    row_evidence = [row.get("evidence_id") for row in rows]
    if any(not isinstance(evidence_id, str) or evidence_id not in declared for evidence_id in row_evidence):
        return _invalid("Every verified keyword row must declare an evidence_id listed by the canonical candidate.")
    if len(row_evidence) != len(set(row_evidence)):
        return _invalid("Every verified keyword row must reference distinct provider evidence.")
    approved_pillar_ids = bundle.get("approved_pillar_ids")
    approved = approved_pillar_ids if isinstance(approved_pillar_ids, list) else [pillar.get("pillar_id") for pillar in pillars if isinstance(pillar, dict)]
    verified_by_pillar = Counter(
        pillar.get("pillar_id")
        for pillar in pillars
        if isinstance(pillar, dict)
        for row in _rows(pillar.get("rows"))
        if row.get("status") == "verified"
        and isinstance(row.get("keyword"), str)
        and isinstance(row.get("evidence_id"), str)
    )
    missing = [pillar for pillar in approved if not isinstance(pillar, str) or verified_by_pillar[pillar] < 25]
    if missing:
        return {
            "valid": False,
            "errors": [{
                "code": "ERROR_STEP2_PREFLIGHT",
                "message": "Each approved pillar requires at least 25 verified provider-evidence rows.",
                "path": ["rows"],
                "remediation": "Obtain complete raw provider evidence through the provider gateway before submitting awaiting_gate.",
            }],
        }
    return {"valid": True, "errors": []}


def _provider_records_valid(bundle: Mapping[str, JsonValue], candidate: Mapping[str, JsonValue]) -> bool:
    records = bundle.get("provider_evidence_records")
    if not isinstance(records, list):
        return False
    rows = _candidate_rows(candidate)
    referenced = {row.get("evidence_id") for row in rows}
    record_ids = [record.get("evidence_id") for record in records if isinstance(record, dict)]
    if len(record_ids) != len(records) or len(record_ids) != len(set(record_ids)) or set(record_ids) != referenced:
        return False
    for record in records:
        if not isinstance(record, dict):
            return False
        request = record.get("request")
        response = record.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            return False
        root = Path(__file__).resolve().parents[2]
        request_schema = json.loads((root / "standards" / "providers" / "research-request.schema.json").read_text(encoding="utf-8"))
        response_schema = json.loads((root / "standards" / "providers" / "research-response.schema.json").read_text(encoding="utf-8"))
        if list(Draft202012Validator(request_schema, format_checker=FormatChecker()).iter_errors(request)) or list(Draft202012Validator(response_schema, format_checker=FormatChecker()).iter_errors(response)):
            return False
        if any(request.get(field) != candidate.get(field) or response.get(field) != candidate.get(field) for field in ("project_id", "deployment_id", "language", "geo")):
            return False
        if request.get("language") != response.get("language") or request.get("geo") != response.get("geo"):
            return False
        try:
            validated = validate_exchange(request, response)
        except ProviderGatewayError:
            return False
        matches = [row for row in rows if row.get("evidence_id") == record["evidence_id"]]
        if len(matches) != 1 or matches[0].get("provider") != validated["provider"] or matches[0].get("raw_response_sha256") != validated["raw_response_sha256"]:
            return False
    return True


def validate_step2_preflight(bundle: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    result = validate_step2_candidate(bundle)
    lineage_errors = validate_lineage(dict(bundle), "2", "1c", "GATE-1C", candidate_schema_name="step-2-keyword-evidence.schema.json")
    if lineage_errors:
        return {"valid": False, "errors": lineage_errors}
    candidate = bundle.get("candidate")
    if not isinstance(candidate, dict) or not _provider_records_valid(bundle, candidate):
        return _invalid("Operational Step 2 preflight requires exact, completed provider-gateway evidence records for every declared row.")
    return result
