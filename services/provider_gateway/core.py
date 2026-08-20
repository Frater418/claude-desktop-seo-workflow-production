"""Contract-only provider evidence validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, TypeAlias


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


def _violations(request: Mapping[str, JsonValue], response: Mapping[str, JsonValue]) -> tuple[str, ...]:
    violations: list[str] = []
    for field in ("request_id", "run_id", "project_id", "deployment_id", "provider", "language", "device"):
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
    actual_cost = _mapping(response.get("cost")).get("actual")
    maximum_cost = _mapping(request.get("cost")).get("maximum")
    if not isinstance(actual_cost, int | float):
        violations.append("unknown_cost")
    elif isinstance(maximum_cost, int | float) and actual_cost > maximum_cost:
        violations.append("quota_exceeded")
    return tuple(sorted(set(violations)))


def validate_exchange(
    request: Mapping[str, JsonValue], response: Mapping[str, JsonValue]
) -> dict[str, JsonValue]:
    """Validate completed raw provider evidence without issuing a provider call."""
    violations = _violations(request, response)
    if violations:
        raise ProviderGatewayError(violations)
    return {
        "provider": response["provider"],
        "request_sha256": request["request_sha256"],
        "raw_response_sha256": _raw_response_sha256(response),
        "provider_job_id": response["provider_job_id"],
        "deployment_id": response["deployment_id"],
    }
