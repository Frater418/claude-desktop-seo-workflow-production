"""Closed AgentSEO dispatch behind the Heartweb Provider Gateway."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from services.agentseo_gateway.core import AgentSEOAdapterError, AgentSEOClient
from services.provider_gateway.core import (
    ProviderGatewayError,
    canonical_request_sha256,
    validate_exchange,
)


class AgentSEODispatchError(RuntimeError):
    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = dict(details or {})
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class AgentSEODispatchContext:
    run_id: str
    project_id: str
    deployment_id: str
    revision: int
    source_artifact_ids: tuple[str, ...]
    authorization_id: str
    maximum_calls: int
    maximum_items: int


@dataclass(frozen=True, slots=True)
class AgentSEODispatcher:
    root: Path
    api_key: str

    def keyword_metrics(
        self,
        *,
        context: AgentSEODispatchContext,
        keywords: Sequence[str],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        cleaned = _keywords(keywords)
        if len(cleaned) > context.maximum_items:
            raise AgentSEODispatchError(
                "ERROR_PROVIDER_ITEM_LIMIT_EXCEEDED",
                "Keyword count exceeds the versioned operation item limit.",
                {"item_count": len(cleaned), "maximum_items": context.maximum_items},
            )
        records: list[dict[str, Any]] = []
        provider_jobs: list[dict[str, Any]] = []
        for keyword in cleaned:
            try:
                outcome = self._client().keyword_metrics(keywords=[keyword], target=target)
                provider_jobs.append(_provider_job(outcome))
                raw_response = _keyword_raw_response(outcome, keyword)
                records.append(
                    self._exchange(
                        context=context,
                        operation="keyword_metrics",
                        parameters={"keyword": keyword},
                        target=target,
                        device="desktop",
                        raw_response=raw_response,
                        provider_job_id=_provider_job_id(outcome),
                    )
                )
            except (AgentSEOAdapterError, AgentSEODispatchError, ProviderGatewayError) as error:
                return {
                    "status": "failed",
                    "complete": False,
                    "provider_evidence_records": records,
                    "provider_jobs": provider_jobs,
                    "error": _error_payload(error),
                }
        return {
            "status": "completed",
            "complete": True,
            "provider_evidence_records": records,
            "provider_jobs": provider_jobs,
        }

    def serp_analysis(
        self,
        *,
        context: AgentSEODispatchContext,
        keyword: str,
        target: Mapping[str, Any],
        device: str,
    ) -> dict[str, Any]:
        cleaned = keyword.strip()
        if not cleaned:
            raise AgentSEODispatchError("ERROR_PROVIDER_QUERY_INVALID", "SERP keyword must not be blank.")
        outcome = self._client().serp_analysis(keyword=cleaned, target=target, device=device)
        raw_response = {
            "provider_payload": _mapping(outcome.get("result"), "AgentSEO SERP result"),
            "location_validation": _mapping(outcome.get("location_validation"), "AgentSEO location validation"),
        }
        record = self._exchange(
            context=context,
            operation="serp_analysis",
            parameters={"keyword": cleaned, "device": device},
            target=target,
            device=device,
            raw_response=raw_response,
            provider_job_id=_provider_job_id(outcome),
        )
        return {
            "status": "completed",
            "complete": True,
            "provider_evidence_records": [record],
            "provider_jobs": [_provider_job(outcome)],
        }

    def _exchange(
        self,
        *,
        context: AgentSEODispatchContext,
        operation: str,
        parameters: Mapping[str, Any],
        target: Mapping[str, Any],
        device: str,
        raw_response: Mapping[str, Any],
        provider_job_id: str,
    ) -> dict[str, Any]:
        seed = _sha256(
            {
                "run_id": context.run_id,
                "project_id": context.project_id,
                "deployment_id": context.deployment_id,
                "revision": context.revision,
                "source_artifact_ids": context.source_artifact_ids,
                "authorization_id": context.authorization_id,
                "operation": operation,
                "parameters": dict(parameters),
            }
        )
        request_id = f"request-{seed[:24]}"
        evidence_id = f"evidence-{seed[24:48]}"
        decision_records = [
            {
                "decision_id": f"decision-{seed[8:32]}",
                "outcome": "provider_evidence_requested",
                "evidence_ids": [evidence_id],
            }
        ]
        request: dict[str, Any] = {
            "schema_version": "2.1.0",
            "request_id": request_id,
            "run_id": context.run_id,
            "project_id": context.project_id,
            "deployment_id": context.deployment_id,
            "revision": context.revision,
            "source_artifact_ids": list(context.source_artifact_ids),
            "evidence_ids": [evidence_id],
            "decision_records": decision_records,
            "candidate_status": "candidate",
            "provider": "agentseo",
            "operation": operation,
            "idempotency_key": f"provider-idem-{seed[:32]}",
            "request_sha256": "0" * 64,
            "geo": {
                "country_code": str(target["country_code"]),
                "provider_location_code": int(target["location_code"]),
            },
            "language": str(target["language"]),
            "device": device,
            "parameters": dict(parameters),
            "cost": {
                "billing_unit": "credits",
                "provider_reported": False,
                "maximum_calls": context.maximum_calls,
                "maximum_items": context.maximum_items,
            },
            "gateway_route": "provider_gateway",
        }
        request["request_sha256"] = canonical_request_sha256(request)
        response: dict[str, Any] = {
            "schema_version": "2.1.0",
            "response_id": f"response-{_sha256({'request_id': request_id, 'provider_job_id': provider_job_id})[:24]}",
            "request_id": request_id,
            "run_id": context.run_id,
            "project_id": context.project_id,
            "deployment_id": context.deployment_id,
            "revision": context.revision,
            "source_artifact_ids": list(context.source_artifact_ids),
            "evidence_ids": [evidence_id],
            "decision_records": decision_records,
            "candidate_status": "candidate",
            "provider": "agentseo",
            "provider_job_id": provider_job_id,
            "status": "completed",
            "geo": request["geo"],
            "language": request["language"],
            "device": device,
            "cost": {
                "billing_unit": "credits",
                "provider_reported": False,
                "status": "not_reported",
            },
            "raw_response": dict(raw_response),
            "raw_response_sha256": _sha256(raw_response),
        }
        self._validate_schema("research-request.schema.json", request)
        self._validate_schema("research-response.schema.json", response)
        validation = validate_exchange(request, response)
        return {
            "evidence_id": evidence_id,
            "request": request,
            "response": response,
            "validation": validation,
        }

    def _validate_schema(self, filename: str, document: Mapping[str, Any]) -> None:
        path = self.root / "standards" / "providers" / filename
        schema = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(dict(document)),
            key=lambda error: tuple(str(part) for part in error.path),
        )
        if errors:
            raise AgentSEODispatchError(
                "ERROR_PROVIDER_EXCHANGE_SCHEMA_INVALID",
                "Provider Gateway exchange violates its closed schema.",
                {"schema": filename, "errors": [error.message for error in errors]},
            )

    def _client(self) -> AgentSEOClient:
        return AgentSEOClient(api_key=self.api_key)


def _keywords(values: Sequence[str]) -> tuple[str, ...]:
    cleaned = tuple(value.strip() for value in values if isinstance(value, str) and value.strip())
    if not cleaned or len(cleaned) != len(values) or len(set(cleaned)) != len(cleaned):
        raise AgentSEODispatchError(
            "ERROR_PROVIDER_QUERY_INVALID",
            "Keyword metrics require a non-empty, unique list of non-blank keywords.",
        )
    return cleaned


def _keyword_raw_response(outcome: Mapping[str, Any], keyword: str) -> dict[str, Any]:
    provider_payload = _mapping(outcome.get("result"), "AgentSEO keyword result")
    rows = provider_payload.get("data")
    if not isinstance(rows, list):
        raise AgentSEODispatchError(
            "ERROR_AGENTSEO_RESPONSE_INVALID",
            "AgentSEO keyword result has no data list.",
        )
    matches = [row for row in rows if isinstance(row, dict) and _keyword(row) == keyword]
    if len(matches) != 1:
        raise AgentSEODispatchError(
            "ERROR_AGENTSEO_RESPONSE_INVALID",
            "AgentSEO keyword result does not contain exactly the requested keyword.",
            {"keyword": keyword, "match_count": len(matches)},
        )
    row = matches[0]
    metrics = _mapping(row.get("metrics"), "AgentSEO keyword metrics")
    search_volume = metrics.get("search_volume")
    difficulty = metrics.get("keyword_difficulty")
    if not isinstance(search_volume, int) or isinstance(search_volume, bool) or search_volume < 0:
        raise AgentSEODispatchError("ERROR_AGENTSEO_RESPONSE_INVALID", "AgentSEO search volume is missing or invalid.")
    if not isinstance(difficulty, int | float) or isinstance(difficulty, bool) or not 0 <= difficulty <= 100:
        raise AgentSEODispatchError("ERROR_AGENTSEO_RESPONSE_INVALID", "AgentSEO keyword difficulty is missing or invalid.")
    normalized: dict[str, Any] = {
        "keyword": keyword,
        "search_volume": search_volume,
        "difficulty": difficulty,
    }
    cpc = metrics.get("cpc")
    if cpc is not None:
        if not isinstance(cpc, int | float) or isinstance(cpc, bool) or cpc < 0:
            raise AgentSEODispatchError("ERROR_AGENTSEO_RESPONSE_INVALID", "AgentSEO CPC is invalid.")
        normalized["cpc_usd"] = cpc
    return {
        "keyword_metrics": [normalized],
        "provider_payload": provider_payload,
        "location_validation": _mapping(outcome.get("location_validation"), "AgentSEO location validation"),
    }


def _keyword(row: Mapping[str, Any]) -> str:
    info = row.get("keyword_info")
    return str(info.get("keyword", "")) if isinstance(info, dict) else ""


def _provider_job_id(outcome: Mapping[str, Any]) -> str:
    value = outcome.get("provider_job_id")
    if not isinstance(value, str) or not value:
        raise AgentSEODispatchError("ERROR_AGENTSEO_JOB_ID_MISSING", "AgentSEO completed without a provider job ID.")
    return value


def _provider_job(outcome: Mapping[str, Any]) -> dict[str, Any]:
    value = outcome.get("provider_raw")
    if not isinstance(value, dict) or not value:
        raise AgentSEODispatchError("ERROR_AGENTSEO_RESPONSE_INVALID", "AgentSEO raw job payload is missing.")
    return value


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise AgentSEODispatchError("ERROR_AGENTSEO_RESPONSE_INVALID", f"{label} is missing or invalid.")
    return value


def _sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _error_payload(error: Exception) -> dict[str, Any]:
    if isinstance(error, AgentSEODispatchError):
        return {"code": error.code, "message": error.message, "details": error.details}
    if isinstance(error, AgentSEOAdapterError):
        return {
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "remediation": error.remediation,
        }
    if isinstance(error, ProviderGatewayError):
        return {
            "code": error.code,
            "message": str(error),
            "details": {"violations": list(error.violations)},
        }
    return {"code": "ERROR_PROVIDER_GATEWAY_INTERNAL", "message": "Provider dispatch failed."}
