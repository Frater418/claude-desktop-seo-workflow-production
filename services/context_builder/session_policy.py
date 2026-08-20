from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from services.context_builder.builder import JsonValue, parse_rfc3339_utc


class TechnicalSessionDecision(StrEnum):
    FRESH_REQUIRED = "fresh_required"
    REUSE_PERMITTED = "reuse_permitted"
    RECOVER_FRESH = "recover_fresh"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class TechnicalSessionPolicyResult:
    decision: TechnicalSessionDecision
    reason: str


def decide_technical_session(
    package: Mapping[str, JsonValue],
    profile: Mapping[str, JsonValue],
    cache_record: Mapping[str, JsonValue] | None,
    now: str,
    package_is_current: bool,
) -> TechnicalSessionPolicyResult:
    trigger = package["trigger"]
    if trigger in {"initial_step", "next_step", "revision"}:
        return TechnicalSessionPolicyResult(TechnicalSessionDecision.FRESH_REQUIRED, "run mode always requires a fresh technical session")
    if not package_is_current:
        return TechnicalSessionPolicyResult(TechnicalSessionDecision.DENIED, "stored package drift prevents retry or resume")
    if cache_record is None or cache_record.get("session_state") in {"missing", "lost", "expired", "invalid"}:
        return TechnicalSessionPolicyResult(TechnicalSessionDecision.RECOVER_FRESH, "cache is unavailable while the immutable package remains current")
    if cache_record.get("session_state") != "available":
        return TechnicalSessionPolicyResult(TechnicalSessionDecision.DENIED, "cache session state is unknown or malformed")
    expected = _cache_projection(package, profile)
    for field, value in expected.items():
        if cache_record.get(field) != value:
            return TechnicalSessionPolicyResult(TechnicalSessionDecision.DENIED, f"cache {field} differs from the stored package or profile")
    if parse_rfc3339_utc(cache_record.get("expires_at"), "/expires_at") <= parse_rfc3339_utc(now, "/now"):
        return TechnicalSessionPolicyResult(TechnicalSessionDecision.RECOVER_FRESH, "cache is expired while the immutable package remains current")
    return TechnicalSessionPolicyResult(TechnicalSessionDecision.REUSE_PERMITTED, "cache exactly matches the immutable package and profile")


def _cache_projection(package: Mapping[str, JsonValue], profile: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return {
        "tenant_id": package["tenant_id"], "project_id": package["project_id"], "run_id": package["run_id"], "step_id": package["step_id"],
        "target_revision": package["target_revision"], "context_package_id": package["context_package_id"], "context_package_sha256": package["package_sha256"],
        "prompt_sha256": package["prompt"]["prompt_sha256"], "worker_profile_sha256": profile["profile_sha256"],
        "provider_id": profile["provider_capability_ref"]["provider_id"], "model_id": profile["model_policy"]["default_model_id"],
        "tool_policy_sha256": profile["tool_policy"]["policy_sha256"], "allowed_operations": profile["tool_policy"]["allowed_operations"],
    }
