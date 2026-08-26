"""Contract-only provider evidence validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, TypeAlias

from .keyword_metrics import normalize_agentseo



JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(frozen=True, slots=True)
class ProviderGatewayError(Exception):
    """One consolidated error suitable for the prompt operator surface."""

    violations: tuple[str, ...]
    code: str = "ERROR_PROVIDER_GATEWAY"

    def __str__(self) -> str:
        return "Provider evidence cannot be submitted: " + ", ".join(self.violations)


def _string(value: JsonValue | None) -> str:
    return value if isinstance(value, str) else ""


def _mapping(value: JsonValue | None) -> Mapping[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _raw_response_sha256(response: Mapping[str, JsonValue]) -> str:
    raw_response = response.get("raw_response")
    if not isinstance(raw_response, dict) or not raw_response:
        return ""
    canonical = json.dumps(raw_response, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def canonical_request_sha256(request: Mapping[str, JsonValue]) -> str:
    """Return the SHA-256 for the closed provider request preimage."""
    preimage = {key: value for key, value in request.items() if key != "request_sha256"}
    canonical = json.dumps(preimage, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _violations(request: Mapping[str, JsonValue], response: Mapping[str, JsonValue]) -> tuple[str, ...]:
    violations: list[str] = []
    if _string(request.get("request_sha256")) != canonical_request_sha256(request):
        violations.append("request_hash_mismatch")
    for field in (
        "schema_version",
        "request_id",
        "run_id",
        "project_id",
        "deployment_id",
        "revision",
        "source_artifact_ids",
        "evidence_ids",
        "decision_records",
        "candidate_status",
        "provider",
        "language",
        "device",
    ):
        if response.get(field) != request.get(field):
            violations.append(f"metadata_mismatch:{field}")
    request_geo = _mapping(request.get("geo"))
    response_geo = _mapping(response.get("geo"))
    if response_geo != request_geo:
        violations.append("location_mismatch")
    if not _string(response.get("provider_job_id")):
        violations.append("missing_job_id")
    if response.get("status") == "timeout":
        violations.append("timeout")
    elif response.get("status") != "completed":
        violations.append("provider_not_completed")
    raw_response_sha256 = _raw_response_sha256(response)
    if not raw_response_sha256:
        violations.append("missing_raw_response")
    declared_raw_response_sha256 = _string(response.get("raw_response_sha256"))
    if not declared_raw_response_sha256:
        violations.append("missing_raw_response_hash")
    elif declared_raw_response_sha256 != raw_response_sha256:
        violations.append("raw_response_hash_mismatch")
    request_cost = _mapping(request.get("cost"))
    response_cost = _mapping(response.get("cost"))
    if request.get("schema_version") == "2.0.0":
        actual_cost = response_cost.get("actual")
        maximum_cost = request_cost.get("maximum")
        if not isinstance(actual_cost, int | float):
            violations.append("unknown_cost")
        elif isinstance(maximum_cost, int | float) and actual_cost > maximum_cost:
            violations.append("quota_exceeded")
    elif request.get("schema_version") == "2.1.0":
        if request_cost.get("billing_unit") != "credits" or request_cost.get("provider_reported") is not False:
            violations.append("provider_usage_contract_mismatch")
        if response_cost != {
            "billing_unit": "credits",
            "provider_reported": False,
            "status": "not_reported",
        }:
            violations.append("provider_usage_contract_mismatch")
    else:
        violations.append("provider_schema_version_unsupported")
    return tuple(sorted(set(violations)))


def validate_exchange(
    request: Mapping[str, JsonValue], response: Mapping[str, JsonValue]
) -> dict[str, JsonValue]:
    """Validate completed raw provider evidence without issuing a provider call."""
    violations = _violations(request, response)
    if violations:
        raise ProviderGatewayError(violations)
    raw_hash = _raw_response_sha256(response)
    result = {
        "provider": response["provider"],
        "request_sha256": request["request_sha256"],
        "raw_response_sha256": raw_hash,
        "provider_job_id": response["provider_job_id"],
        "deployment_id": response["deployment_id"],
    }
    if request.get("operation") != "keyword_metrics":
        return result
    if response.get("provider") != "agentseo":
        raise ProviderGatewayError(("normalization_unsupported_provider",))
    normalized, normalization_violations = normalize_agentseo(response, _string(request.get("request_sha256")), raw_hash)
    if normalization_violations:
        raise ProviderGatewayError(normalization_violations)
    return {**result, "normalized_keyword_records": normalized}
