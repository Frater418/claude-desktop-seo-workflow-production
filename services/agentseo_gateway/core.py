#!/usr/bin/env python3
"""Transportneutraler AgentSEO-Client mit strikter Geo-Validierung.

Der Gateway-Kern wird von Hermes, einer HTTP-API und spaeter n8n gemeinsam
verwendet. Er erzwingt asynchrone AgentSEO-Jobs, prueft den Zielmarkt gegen
die Heartweb-Standorttabelle und bewahrt Provider-Rohdaten unveraendert auf.

Autor: Raphael Rechberger
Version: 1.0.0
"""

from __future__ import annotations

import copy
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


class AgentSEOAdapterError(RuntimeError):
    """Strukturierter Fail-Fast-Fehler des AgentSEO-Gateways."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


def _provider_failure_code(status: int | None, payload: Any) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=True, sort_keys=True).casefold()
    except (TypeError, ValueError):
        text = str(payload).casefold()
    compact = " ".join(text.replace("_", " ").replace("-", " ").split())
    if status == 402 or any(
        marker in compact
        for marker in (
            "insufficient funds",
            "insufficient credit",
            "not enough credit",
            "payment required",
            "credit balance",
        )
    ):
        return "ERROR_PROVIDER_INSUFFICIENT_FUNDS"
    if "quota exceeded" in compact or "quota exhausted" in compact:
        return "ERROR_PROVIDER_QUOTA_EXCEEDED"
    if status == 429:
        return "ERROR_PROVIDER_RATE_LIMITED"
    return "ERROR_AGENTSEO_HTTP" if status is not None else "ERROR_AGENTSEO_FETCH_FAILED"


def _provider_failure_message(code: str, fallback: str) -> str:
    messages = {
        "ERROR_PROVIDER_INSUFFICIENT_FUNDS": "The provider rejected the tool call because the account has insufficient funds or credits.",
        "ERROR_PROVIDER_QUOTA_EXCEEDED": "The provider rejected the tool call because the account quota is exhausted.",
        "ERROR_PROVIDER_RATE_LIMITED": "The provider temporarily rate-limited the tool call.",
    }
    return messages.get(code, fallback)


def load_location_target(country: str, path: Path) -> Dict[str, Any]:
    """Lade ein verbindliches Heartweb-Zielmarktprofil."""

    normalized_country = str(country or "").strip().upper()
    if not normalized_country:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_UNKNOWN",
            "Country is required.",
        )

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_MISSING",
            f"Location table not found: {path}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Location table is invalid JSON: {path}",
            {"line": exc.lineno, "column": exc.colno},
        ) from exc

    record = data.get("countries", {}).get(normalized_country)
    if not isinstance(record, dict):
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_UNKNOWN",
            f"Country is not configured: {normalized_country}",
        )

    location_name = str(record.get("location_name") or "").strip()
    location_code = record.get("location_code")
    language = str(record.get("default_language") or "").strip()
    if not location_name or not isinstance(location_code, int) or location_code <= 0:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Country record is incomplete: {normalized_country}",
        )
    if not language:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Default language is missing: {normalized_country}",
        )

    return {
        "country": normalized_country,
        "location_name": location_name,
        "location_code": location_code,
        "language": language,
    }


def load_provider_target(target_id: str, path: Path) -> Dict[str, Any]:
    """Load one exact verified provider target by its canonical identity."""

    normalized_target_id = str(target_id or "").strip()
    if not normalized_target_id:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_UNKNOWN",
            "A provider target_id is required.",
        )
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_MISSING",
            f"Provider location registry not found: {path}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Provider location registry is invalid JSON: {path}",
            {"line": exc.lineno, "column": exc.colno},
        ) from exc

    targets = data.get("targets")
    if not isinstance(targets, list):
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            "Provider location registry must contain a targets array.",
        )
    matches = [target for target in targets if isinstance(target, dict) and target.get("target_id") == normalized_target_id]
    if len(matches) != 1:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_UNKNOWN" if not matches else "ERROR_LOCATION_TABLE_INVALID",
            f"Provider target is not configured uniquely: {normalized_target_id}",
        )
    record = matches[0]
    if record.get("provider_id") != data.get("provider_id"):
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Provider target has a conflicting provider_id: {normalized_target_id}",
        )
    if record.get("status") != "verified":
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_UNVERIFIED",
            f"Provider target is not verified: {normalized_target_id}",
            {"status": record.get("status")},
        )
    location_code = record.get("location_code")
    if not isinstance(location_code, int) or location_code <= 0:
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Verified provider target has no valid location_code: {normalized_target_id}",
        )
    languages = record.get("languages")
    if not isinstance(languages, list) or not languages or any(not isinstance(language, str) or not language for language in languages):
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_TABLE_INVALID",
            f"Provider target has no valid languages: {normalized_target_id}",
        )
    return {
        **copy.deepcopy(record),
        "country": record["country_code"],
    }


def _validate_keywords(keywords: Iterable[str]) -> List[str]:
    cleaned = [str(keyword).strip() for keyword in keywords]
    if not cleaned or len(cleaned) > 100:
        raise AgentSEOAdapterError(
            "ERROR_KEYWORD_INPUT_INVALID",
            "Between 1 and 100 keywords are required.",
        )
    if any(not keyword or len(keyword) > 80 for keyword in cleaned):
        raise AgentSEOAdapterError(
            "ERROR_KEYWORD_INPUT_INVALID",
            "Every keyword must contain 1 to 80 characters.",
        )
    return cleaned


def build_keyword_metrics_payload(
    *,
    keywords: Iterable[str],
    target: Mapping[str, Any],
    min_search_volume: int = 0,
    sort_by: str = "priority",
) -> Dict[str, Any]:
    """Baue den verbindlichen Keyword-Metrics-Request."""

    if sort_by not in {"priority", "search_volume", "cpc", "difficulty"}:
        raise AgentSEOAdapterError(
            "ERROR_KEYWORD_INPUT_INVALID",
            f"Unsupported sort order: {sort_by}",
        )
    if not isinstance(min_search_volume, int) or min_search_volume < 0:
        raise AgentSEOAdapterError(
            "ERROR_KEYWORD_INPUT_INVALID",
            "min_search_volume must be a non-negative integer.",
        )

    return {
        "keywords": _validate_keywords(keywords),
        "location": target["location_name"],
        "location_code": target["location_code"],
        "language": target["language"],
        "min_search_volume": min_search_volume,
        "sort_by": sort_by,
    }


def build_serp_analysis_payload(
    *,
    keyword: str,
    target: Mapping[str, Any],
    device: str = "desktop",
) -> Dict[str, Any]:
    """Baue den SERP-Request inklusive explizitem Provider-Code."""

    cleaned_keyword = str(keyword or "").strip()
    if not cleaned_keyword:
        raise AgentSEOAdapterError(
            "ERROR_SERP_INPUT_INVALID",
            "A keyword is required.",
        )
    if device not in {"desktop", "mobile"}:
        raise AgentSEOAdapterError(
            "ERROR_SERP_INPUT_INVALID",
            f"Unsupported device: {device}",
        )

    return {
        "keyword": cleaned_keyword,
        "location": target["location_name"],
        "location_code": target["location_code"],
        "language": target["language"],
        "device": device,
    }


def _find_provider_location(result: Mapping[str, Any]) -> Dict[str, Any]:
    location = result.get("location")
    if isinstance(location, dict):
        return location

    search_parameters = result.get("search_parameters")
    if isinstance(search_parameters, dict):
        geo_target = search_parameters.get("geo_target")
        if isinstance(geo_target, dict):
            return geo_target

    raise AgentSEOAdapterError(
        "ERROR_LOCATION_MISSING",
        "AgentSEO result does not contain location metadata.",
    )


def _find_normalized_location(result: Dict[str, Any]) -> Dict[str, Any]:
    location = result.get("location")
    if isinstance(location, dict):
        return location
    return result["search_parameters"]["geo_target"]


def normalize_agentseo_result(
    result: Mapping[str, Any],
    target: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validiere Geo-Metadaten und korrigiere nur den belegten ISO-Defekt.

    Der Providerwert bleibt als ``provider_country_iso_code`` erhalten. Eine
    Korrektur ist nur erlaubt, wenn Code und Name exakt zum verbindlichen
    Heartweb-Zielmarkt passen und der bekannte Providerwert ``US`` vorliegt.
    Jede andere Abweichung fuehrt zum harten Abbruch.
    """

    provider_location = _find_provider_location(result)
    expected_code = int(target["location_code"])
    expected_name = str(target["location_name"]).strip()
    expected_country = str(target["country"]).strip().upper()

    provider_code = provider_location.get("location_code")
    provider_name = str(provider_location.get("location_name") or "").strip()
    provider_country = str(
        provider_location.get("country_iso_code") or ""
    ).strip().upper()

    if provider_code != expected_code or provider_name.casefold() != expected_name.casefold():
        raise AgentSEOAdapterError(
            "ERROR_LOCATION_MISMATCH",
            "AgentSEO location does not match the requested target market.",
            {
                "expected": {
                    "country": expected_country,
                    "location_name": expected_name,
                    "location_code": expected_code,
                },
                "provider": {
                    "country_iso_code": provider_country or None,
                    "location_name": provider_name or None,
                    "location_code": provider_code,
                },
            },
        )

    normalized_result = copy.deepcopy(dict(result))
    normalized_location = _find_normalized_location(normalized_result)
    warnings: List[str] = []
    status = "validated"

    if provider_country != expected_country:
        if provider_country != "US" or expected_country == "US":
            raise AgentSEOAdapterError(
                "ERROR_LOCATION_MISMATCH",
                "AgentSEO country metadata does not match the requested market.",
                {
                    "expected_country": expected_country,
                    "provider_country_iso_code": provider_country or None,
                    "location_name": provider_name,
                    "location_code": provider_code,
                },
            )
        normalized_location["provider_country_iso_code"] = provider_country
        normalized_location["country_iso_code"] = expected_country
        warnings.append("WARN_AGENTSEO_COUNTRY_ISO_METADATA_CORRECTED")
        status = "validated_with_provider_metadata_correction"

    return {
        "result": normalized_result,
        "location_validation": {
            "status": status,
            "country": expected_country,
            "location_name": expected_name,
            "location_code": expected_code,
            "provider_country_iso_code": provider_country or None,
            "warnings": warnings,
        },
    }


class AgentSEOClient:
    """Asynchroner AgentSEO-REST-Client mit synchronem Polling-Interface."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://www.agentseo.dev/api/v1",
        request_timeout: float = 30.0,
        poll_interval: float = 2.0,
        max_wait: float = 180.0,
    ) -> None:
        cleaned_key = str(api_key or "").strip()
        if not cleaned_key:
            raise AgentSEOAdapterError(
                "ERROR_AGENTSEO_API_KEY_MISSING",
                "AGENTSEO_API_KEY is required.",
            )
        self.api_key = cleaned_key
        self.base_url = str(base_url).rstrip("/")
        self.request_timeout = request_timeout
        self.poll_interval = poll_interval
        self.max_wait = max_wait

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "x-api-key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                error_body: Any = json.loads(raw)
            except json.JSONDecodeError:
                error_body = raw[:1000]
            code = _provider_failure_code(exc.code, error_body)
            raise AgentSEOAdapterError(
                code,
                _provider_failure_message(code, f"AgentSEO returned HTTP {exc.code}."),
                {"status": exc.code, "response": error_body},
            ) from exc
        except urllib.error.URLError as exc:
            raise AgentSEOAdapterError(
                "ERROR_AGENTSEO_NETWORK",
                f"AgentSEO request failed: {exc.reason}",
            ) from exc

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AgentSEOAdapterError(
                "ERROR_AGENTSEO_RESPONSE_INVALID",
                "AgentSEO returned invalid JSON.",
            ) from exc
        if not isinstance(data, dict):
            raise AgentSEOAdapterError(
                "ERROR_AGENTSEO_RESPONSE_INVALID",
                "AgentSEO returned a non-object response.",
            )
        return data

    def _queue_and_poll(
        self,
        endpoint: str,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        queued = self._request_json(
            "POST",
            endpoint,
            payload=payload,
            query={"sync": "false"},
        )
        job_id = queued.get("jobId") or queued.get("job_id")
        if not job_id:
            raise AgentSEOAdapterError(
                "ERROR_AGENTSEO_JOB_ID_MISSING",
                "AgentSEO did not return a job ID.",
                {"response_keys": sorted(queued.keys())},
            )

        started = time.monotonic()
        while True:
            job = self._request_json("GET", f"/jobs/{job_id}")
            status = str(job.get("status") or "").lower()
            if status == "completed":
                if not isinstance(job.get("result"), dict):
                    raise AgentSEOAdapterError(
                        "ERROR_AGENTSEO_RESPONSE_INVALID",
                        "Completed AgentSEO job has no result object.",
                        {"job_id": job_id},
                    )
                return job
            if status in {"failed", "error", "cancelled"}:
                error_payload = job.get("error")
                code = _provider_failure_code(None, error_payload)
                raise AgentSEOAdapterError(
                    code,
                    _provider_failure_message(code, "AgentSEO job failed."),
                    {"job_id": job_id, "status": status, "error": error_payload},
                )
            if time.monotonic() - started >= self.max_wait:
                raise AgentSEOAdapterError(
                    "ERROR_AGENTSEO_TIMEOUT",
                    "AgentSEO job did not complete before the timeout.",
                    {"job_id": job_id, "max_wait_seconds": self.max_wait},
                )
            time.sleep(self.poll_interval)

    def keyword_metrics(
        self,
        *,
        keywords: Iterable[str],
        target: Mapping[str, Any],
        min_search_volume: int = 0,
        sort_by: str = "priority",
    ) -> Dict[str, Any]:
        payload = build_keyword_metrics_payload(
            keywords=keywords,
            target=target,
            min_search_volume=min_search_volume,
            sort_by=sort_by,
        )
        raw_job = self._queue_and_poll("/keyword-metrics/overview", payload)
        normalized = normalize_agentseo_result(raw_job["result"], target)
        return {
            "operation": "keyword_metrics",
            "provider": "agentseo",
            "provider_job_id": raw_job.get("jobId") or raw_job.get("job_id"),
            "target": dict(target),
            **normalized,
            "provider_raw": raw_job,
        }

    def serp_analysis(
        self,
        *,
        keyword: str,
        target: Mapping[str, Any],
        device: str = "desktop",
    ) -> Dict[str, Any]:
        payload = build_serp_analysis_payload(
            keyword=keyword,
            target=target,
            device=device,
        )
        raw_job = self._queue_and_poll("/analyze/serp", payload)
        normalized = normalize_agentseo_result(raw_job["result"], target)
        return {
            "operation": "serp_analysis",
            "provider": "agentseo",
            "provider_job_id": raw_job.get("jobId") or raw_job.get("job_id"),
            "target": dict(target),
            **normalized,
            "provider_raw": raw_job,
        }
