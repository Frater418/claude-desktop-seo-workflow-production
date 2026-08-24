"""Provider-neutral keyword metric normalization."""

from __future__ import annotations

from typing import Mapping, TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
_NORMALIZER: dict[str, JsonValue] = {"identifier": "heartweb.keyword-metrics", "version": "1.0.0"}


def normalize_agentseo(response: Mapping[str, JsonValue], request_hash: str, raw_hash: str) -> tuple[list[dict[str, JsonValue]], tuple[str, ...]]:
    raw = response.get("raw_response")
    records = raw.get("keyword_metrics") if isinstance(raw, dict) else None
    evidence_ids = response.get("evidence_ids")
    if not isinstance(records, list) or not records:
        return [], ("normalized_metric_invalid:keyword_metrics",)
    if not isinstance(evidence_ids, list) or any(not isinstance(item, str) or not item for item in evidence_ids):
        return [], ("normalized_metric_invalid:evidence_ids",)
    if len(records) != len(evidence_ids) or len(set(evidence_ids)) != len(evidence_ids):
        return [], ("normalized_metric_invalid:evidence_ids",)
    normalized: list[dict[str, JsonValue]] = []
    violations: list[str] = []
    for evidence_id, record in zip(evidence_ids, records, strict=True):
        if not isinstance(evidence_id, str) or not isinstance(record, dict):
            violations.append("normalized_metric_invalid:keyword_metrics")
            continue
        keyword, volume, difficulty = record.get("keyword"), record.get("search_volume"), record.get("difficulty")
        if not isinstance(keyword, str) or not keyword.strip():
            violations.append("normalized_metric_invalid:keyword")
        if not isinstance(volume, int) or isinstance(volume, bool) or volume < 0:
            violations.append("normalized_metric_invalid:search_volume")
        if not isinstance(difficulty, int | float) or isinstance(difficulty, bool) or not 0 <= difficulty <= 100:
            violations.append("normalized_metric_invalid:difficulty")
        has_cpc = "cpc_usd" in record
        cpc = record.get("cpc_usd")
        if has_cpc and (not isinstance(cpc, int | float) or isinstance(cpc, bool) or cpc < 0):
            violations.append("normalized_metric_invalid:cpc_usd")
        if violations:
            continue
        cpc_value: dict[str, JsonValue] = {"availability": "available", "value": cpc} if has_cpc else {"availability": "unavailable", "reason": "not_returned_by_provider"}
        normalized.append({"evidence_id": evidence_id, "keyword": keyword, "metrics": {"search_volume": {"availability": "available", "value": volume}, "difficulty": {"availability": "available", "value": difficulty}, "cpc_usd": cpc_value}, "provenance": {"provider": response["provider"], "provider_job_id": response["provider_job_id"], "request_sha256": request_hash, "raw_response_sha256": raw_hash, "normalizer": _NORMALIZER}})
    return normalized, tuple(sorted(set(violations)))
