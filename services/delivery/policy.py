from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .inventory import DeliveryInventory


_REQUIRED: Final = ("strategy", "architecture", "design", "keyword-research", "roadmap", "copywriter-handoff", "developer-handoff")


@dataclass(frozen=True, slots=True)
class DeliveryPolicyError:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class DeliveryPolicyResult:
    scope: str
    eligible: bool
    missing_deliverable_ids: tuple[str, ...]
    errors: tuple[DeliveryPolicyError, ...]


@dataclass(frozen=True, slots=True)
class FinalReadinessPolicy:
    allow_step_4b_staging: bool = False


@dataclass(frozen=True, slots=True)
class Step4bStagingReadiness:
    artifact_id: str
    artifact_revision: int
    artifact_sha256: str


def evaluate_checkpoint(inventory: DeliveryInventory) -> DeliveryPolicyResult:
    missing = _missing(inventory, allow_staging=False)
    return DeliveryPolicyResult("checkpoint", True, missing, ())


def evaluate_final(inventory: DeliveryInventory, readiness_policy: FinalReadinessPolicy = FinalReadinessPolicy(), staging_readiness: Step4bStagingReadiness | None = None) -> DeliveryPolicyResult:
    staging_allowed = readiness_policy.allow_step_4b_staging and _staging_matches(inventory, staging_readiness)
    staging_file = staging_allowed and staging_readiness is not None and any(item.artifact_id == staging_readiness.artifact_id for item in inventory.files)
    missing = _missing(inventory, allow_staging=staging_file)
    errors: list[DeliveryPolicyError] = []
    step_4b_ready = any(item.step_id == "4b" and item.release_status == "released" and item.output_path is not None for item in inventory.deliverables) or staging_file
    if not step_4b_ready:
        errors.append(DeliveryPolicyError("DELIVERY_FINAL_STEP_4B_NOT_READY", "Step 4b must be released or staging-ready under the final policy."))
    if missing:
        errors.append(DeliveryPolicyError("DELIVERY_FINAL_DELIVERABLE_MISSING", "Final delivery is missing required released deliverables."))
    return DeliveryPolicyResult("final", not errors, missing, tuple(errors))


def _staging_matches(inventory: DeliveryInventory, readiness: Step4bStagingReadiness | None) -> bool:
    if readiness is None:
        return False
    return any(item.step_id == "4b" and item.record_id == readiness.artifact_id and item.revision == readiness.artifact_revision and item.content_sha256 == readiness.artifact_sha256 for item in inventory.artifacts)


def _missing(inventory: DeliveryInventory, allow_staging: bool) -> tuple[str, ...]:
    present = {
        item.deliverable_id
        for item in inventory.deliverables
        if item.output_path is not None and (item.release_status == "released" or allow_staging and item.deliverable_id == "developer-handoff" and item.release_status == "staging_ready")
    }
    if allow_staging:
        present.add("developer-handoff")
    return tuple(deliverable_id for deliverable_id in _REQUIRED if deliverable_id not in present)
