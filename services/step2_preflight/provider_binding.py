from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, TypeAlias

from jsonschema import Draft202012Validator, FormatChecker

from services.provider_gateway.core import ProviderGatewayError, validate_exchange


JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

_ROOT = Path(__file__).resolve().parents[2]
_REQUEST_SCHEMA = json.loads((_ROOT / "standards" / "providers" / "research-request.schema.json").read_text(encoding="utf-8"))
_RESPONSE_SCHEMA = json.loads((_ROOT / "standards" / "providers" / "research-response.schema.json").read_text(encoding="utf-8"))
_REQUEST_VALIDATOR = Draft202012Validator(_REQUEST_SCHEMA, format_checker=FormatChecker())
_RESPONSE_VALIDATOR = Draft202012Validator(_RESPONSE_SCHEMA, format_checker=FormatChecker())


def _single_evidence_id(value: JsonValue | None, evidence_id: str) -> bool:
    return isinstance(value, list) and value == [evidence_id]


def _exchange_identity_is_unique(records: list[Mapping[str, JsonValue]]) -> bool:
    request_ids = [record["request"]["request_id"] for record in records]
    response_ids = [record["response"]["response_id"] for record in records]
    provider_job_ids = [record["response"]["provider_job_id"] for record in records]
    request_hashes = [record["request"]["request_sha256"] for record in records]
    raw_response_hashes = [record["response"]["raw_response_sha256"] for record in records]
    return all(
        len(values) == len(set(values))
        for values in (request_ids, response_ids, provider_job_ids, request_hashes, raw_response_hashes)
    )


def _candidate_keywords_are_unique(candidate: Mapping[str, JsonValue]) -> bool:
    pillars = candidate["pillars"]
    if not isinstance(pillars, list):
        return False
    keywords = []
    for pillar in pillars:
        if not isinstance(pillar, dict):
            return False
        rows = pillar["rows"]
        if not isinstance(rows, list):
            return False
        pillar_keywords = [row["keyword"] for row in rows if isinstance(row, dict)]
        if len(pillar_keywords) != len(rows):
            return False
        keywords.extend(pillar_keywords)
    return len(keywords) == len(set(keywords))


def _row_matches_normalized(row: Mapping[str, JsonValue], normalized: Mapping[str, JsonValue]) -> bool:
    metrics = normalized.get("metrics")
    provenance = normalized.get("provenance")
    if not isinstance(metrics, dict) or not isinstance(provenance, dict):
        return False
    search_volume = metrics.get("search_volume")
    difficulty = metrics.get("difficulty")
    return (
        row.get("keyword") == normalized.get("keyword")
        and isinstance(search_volume, dict)
        and row.get("search_volume") == search_volume.get("value")
        and isinstance(difficulty, dict)
        and row.get("difficulty") == difficulty.get("value")
        and row.get("cpc_usd") == metrics.get("cpc_usd")
        and row.get("provider") == provenance.get("provider")
        and row.get("raw_response_sha256") == provenance.get("raw_response_sha256")
    )


def validate_provider_binding(
    bundle: Mapping[str, JsonValue], candidate: Mapping[str, JsonValue], rows: list[Mapping[str, JsonValue]]
) -> str | None:
    if not _candidate_keywords_are_unique(candidate):
        return "Candidate keywords must be unique across all pillars."
    records_value = bundle.get("provider_evidence_records")
    if not isinstance(records_value, list):
        return "Provider evidence records are required for every candidate evidence_id."
    if any(not isinstance(record, dict) or not {"evidence_id", "request", "response"} <= set(record) for record in records_value):
        return "Each provider evidence record must contain evidence_id, request, and response."
    records = [record for record in records_value if isinstance(record, dict)]
    row_by_evidence = {row["evidence_id"]: row for row in rows}
    record_ids = [record["evidence_id"] for record in records]
    if (
        any(not isinstance(evidence_id, str) for evidence_id in record_ids)
        or len(records) != len(rows)
        or len(record_ids) != len(set(record_ids))
        or set(record_ids) != set(row_by_evidence)
    ):
        return "Submit exactly one provider evidence record for every candidate evidence_id."
    for record in records:
        evidence_id = record["evidence_id"]
        request = record["request"]
        response = record["response"]
        if not isinstance(evidence_id, str) or not isinstance(request, dict) or not isinstance(response, dict):
            return "Each provider evidence record requires string evidence_id and object request and response."
        if not _single_evidence_id(request.get("evidence_ids"), evidence_id) or not _single_evidence_id(response.get("evidence_ids"), evidence_id):
            return "Outer, request, and response evidence_ids must identify the same single candidate row."
        if tuple(_REQUEST_VALIDATOR.iter_errors(request)) or tuple(_RESPONSE_VALIDATOR.iter_errors(response)):
            return "Provider request or response does not satisfy its closed gateway schema."
        if response["request_id"] != request["request_id"]:
            return "Provider response request_id must match its request request_id."
        if any(
            request[field] != candidate[field] or response[field] != candidate[field]
            for field in ("run_id", "project_id", "deployment_id", "source_artifact_ids", "language", "geo")
        ):
            return "Provider run, project, deployment, source artifacts, language, or geo metadata does not match the candidate."
        try:
            exchange = validate_exchange(request, response)
        except ProviderGatewayError:
            return "Provider exchange is incomplete, malformed, or fails gateway metadata validation."
        normalized_records = exchange.get("normalized_keyword_records")
        if not isinstance(normalized_records, list):
            return "Provider exchange did not return normalized keyword records."
        matching_records = [normalized for normalized in normalized_records if isinstance(normalized, dict) and normalized.get("evidence_id") == evidence_id]
        if len(matching_records) != 1 or not _row_matches_normalized(row_by_evidence[evidence_id], matching_records[0]):
            return "Candidate row does not exactly match the provider gateway normalized keyword record."
    if not _exchange_identity_is_unique(records):
        return "Provider request IDs, response IDs, provider job IDs, request hashes, and raw response hashes must be unique across evidence records."
    return None
