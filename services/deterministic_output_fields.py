from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping, Sequence


STEP4A_BRIEFING_CONTRACT = "https://heartweb.example/schema/outputs/step-4a-briefing.schema.json"
STEP4B_PAGE_CONTRACT = "https://heartweb.example/schema/outputs/step-4b-page-spec.schema.json"
STEP4B_STAGING_CONTRACT = "https://heartweb.example/schema/outputs/staging-evidence.schema.json"


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def bind_deterministic_output_fields(step_id: str, outputs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return Core-normalized output copies with deterministic self-hashes bound."""

    normalized = copy.deepcopy([dict(output) for output in outputs])
    by_contract = {
        output.get("contract_id"): output
        for output in normalized
        if isinstance(output.get("contract_id"), str) and isinstance(output.get("content"), dict)
    }
    if step_id == "4a":
        briefing = by_contract.get(STEP4A_BRIEFING_CONTRACT, {}).get("content")
        jsonld = briefing.get("jsonld") if isinstance(briefing, dict) else None
        graph = jsonld.get("graph") if isinstance(jsonld, dict) else None
        if isinstance(graph, dict):
            jsonld["graph_hash"] = canonical_sha256(graph)
    if step_id == "4b":
        page = by_contract.get(STEP4B_PAGE_CONTRACT, {}).get("content")
        staging = by_contract.get(STEP4B_STAGING_CONTRACT, {}).get("content")
        if isinstance(page, dict):
            jsonld = page.get("jsonld")
            graph = jsonld.get("graph") if isinstance(jsonld, dict) else None
            if isinstance(graph, dict):
                jsonld["graph_hash"] = canonical_sha256(graph)
            page_without_hash = dict(page)
            page_without_hash.pop("content_sha256", None)
            page["content_sha256"] = canonical_sha256(page_without_hash)
        if isinstance(page, dict) and isinstance(staging, dict):
            content_sha256 = page["content_sha256"]
            staging["content_sha256"] = content_sha256
            checks = staging.get("checks")
            if isinstance(checks, list):
                for check in checks:
                    if isinstance(check, dict):
                        check["content_sha256"] = content_sha256
            staging_without_hash = dict(staging)
            staging_without_hash.pop("staging_sha256", None)
            staging["staging_sha256"] = canonical_sha256(staging_without_hash)
    return normalized
