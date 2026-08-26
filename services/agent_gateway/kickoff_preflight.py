from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


_DOMAIN_PATTERN = re.compile(
    r"(?<![@A-Za-z0-9_-])(?:https?://)?(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?:/[^\s<>()\[\]{}]*)?",
    re.IGNORECASE,
)
_HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+(?:wettbewerber|competitors?)\b", re.IGNORECASE)
_NEXT_HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class KickoffPreflightError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def build_kickoff_preflight(
    *,
    project_v2: Mapping[str, Any],
    accepted_intake: Mapping[str, Any],
    deployment_id: str,
    location_table_path: Path,
    manifest_schema_path: Path,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    deployment = _deployment(project_v2, deployment_id)
    country = _required_string(deployment, "country_code", "ERROR_LOCATION_UNKNOWN")
    language = _required_string(deployment, "language", "ERROR_LOCATION_UNKNOWN")
    location_registry = _json_object(location_table_path, "ERROR_LOCATION_TABLE_INVALID")
    location = _provider_target(location_registry, deployment)
    planning_capacity = _planning_capacity(project_v2)

    intake_sha256 = accepted_intake.get("source_sha256")
    markdown = accepted_intake.get("markdown")
    if not isinstance(intake_sha256, str) or _SHA256_PATTERN.fullmatch(intake_sha256) is None:
        raise KickoffPreflightError(
            "ERROR_INTAKE_BINDING_INVALID",
            "The accepted intake has no canonical source hash.",
        )
    if not isinstance(markdown, str) or not markdown.strip():
        raise KickoffPreflightError(
            "ERROR_COMPETITOR_PREFLIGHT_INPUT_MISSING",
            "The accepted intake has no readable briefing Markdown.",
        )
    competitors = _competitor_urls(markdown)
    if not competitors:
        raise KickoffPreflightError(
            "ERROR_COMPETITOR_PREFLIGHT_INPUT_MISSING",
            "The accepted intake contains no bound competitor URLs.",
        )
    if len(competitors) > 10:
        raise KickoffPreflightError(
            "ERROR_COMPETITOR_PREFLIGHT_LIMIT",
            "The accepted intake contains more than ten competitor URLs.",
        )

    manifest_schema = _json_object(manifest_schema_path, "ERROR_MANIFEST_SCHEMA_INVALID")
    artifact_paths = _artifact_defaults(manifest_schema)
    project_v2_sha256 = _canonical_sha256(project_v2)
    location_table_sha256 = hashlib.sha256(location_table_path.read_bytes()).hexdigest()
    manifest_schema_sha256 = hashlib.sha256(manifest_schema_path.read_bytes()).hexdigest()

    return {
        "deployment_id": deployment_id,
        "country": country,
        "location_code": location["location_code"],
        "language": language,
        "capacity_hours_per_week": planning_capacity,
        "deployment_binding": copy.deepcopy(dict(deployment)),
        "artifact_paths": artifact_paths,
        "competitors": list(competitors),
        "competitor_preflight": [
            _probe_competitor(url, opener)
            for url in competitors
        ],
        "source_binding": {
            "project_v2_sha256": project_v2_sha256,
            "intake_source_sha256": intake_sha256,
            "provider_location_registry_sha256": location_table_sha256,
            "manifest_schema_sha256": manifest_schema_sha256,
        },
    }


def _planning_capacity(project_v2: Mapping[str, Any]) -> dict[str, Any]:
    capacity = project_v2.get("planning_capacity")
    if not isinstance(capacity, dict):
        raise KickoffPreflightError(
            "ERROR_PLANNING_CAPACITY_REQUIRED",
            "Step 0 requires confirmed minimum and maximum weekly planning hours.",
        )
    minimum = capacity.get("min")
    maximum = capacity.get("max")
    if (
        not isinstance(minimum, (int, float))
        or isinstance(minimum, bool)
        or not isinstance(maximum, (int, float))
        or isinstance(maximum, bool)
        or maximum < minimum
        or capacity.get("source") not in {"briefing_confirmed", "operator_confirmed"}
        or capacity.get("provisional") is not False
        or not isinstance(capacity.get("confirmed_by"), str)
        or not isinstance(capacity.get("confirmed_at"), str)
    ):
        raise KickoffPreflightError(
            "ERROR_PLANNING_CAPACITY_INVALID",
            "Step 0 weekly planning capacity is invalid or not confirmed.",
        )
    return {
        "min": minimum,
        "max": maximum,
        "source": capacity["source"],
        "provisional": False,
    }


def _deployment(project_v2: Mapping[str, Any], deployment_id: str) -> Mapping[str, Any]:
    deployments = project_v2.get("market_deployments")
    matches = [
        item
        for item in deployments
        if isinstance(item, dict) and item.get("deployment_id") == deployment_id
    ] if isinstance(deployments, list) else []
    if len(matches) != 1 or matches[0].get("market_phase") != "active":
        raise KickoffPreflightError(
            "ERROR_DEPLOYMENT_MISSING",
            "The selected active Project V2 deployment is unavailable or ambiguous.",
        )
    return matches[0]


def _provider_target(registry: Mapping[str, Any], deployment: Mapping[str, Any]) -> Mapping[str, Any]:
    verification = deployment.get("provider_location_verification")
    if not isinstance(verification, dict) or verification.get("status") != "verified":
        raise KickoffPreflightError(
            "ERROR_LOCATION_UNVERIFIED",
            "The selected active deployment has no persisted verified provider target.",
        )
    target_id = verification.get("target_id")
    targets = registry.get("targets")
    matches = [
        target
        for target in targets
        if isinstance(target, dict) and target.get("target_id") == target_id
    ] if isinstance(targets, list) else []
    if len(matches) != 1:
        raise KickoffPreflightError(
            "ERROR_LOCATION_UNKNOWN",
            "The deployment provider target is unavailable or ambiguous in the canonical registry.",
        )
    target = matches[0]
    if target.get("status") != "verified":
        raise KickoffPreflightError(
            "ERROR_LOCATION_UNVERIFIED",
            "The deployment provider target is not verified in the canonical registry.",
        )
    expected = {
        "status": "verified",
        "provider_id": target.get("provider_id"),
        "target_id": target.get("target_id"),
        "target_type": target.get("target_type"),
        "location_name": target.get("location_name"),
        "provider_location_code": target.get("location_code"),
        "verified_at": target.get("verified_at"),
        "verification_source": target.get("verification_source"),
    }
    if verification != expected:
        raise KickoffPreflightError(
            "ERROR_LOCATION_BINDING_MISMATCH",
            "The persisted deployment provider binding differs from the canonical provider target.",
        )
    country = deployment.get("country_code")
    language = deployment.get("language")
    if target.get("country_code") != country or language not in target.get("languages", []):
        raise KickoffPreflightError(
            "ERROR_LOCATION_BINDING_MISMATCH",
            "The deployment market or language differs from its provider target.",
        )
    if deployment.get("seo_operating_model") in {"local", "regional", "programmatic_local"} and target.get("target_type") == "country":
        raise KickoffPreflightError(
            "ERROR_LOCATION_BINDING_MISMATCH",
            "A local or regional deployment requires a region, city or postal-code provider target.",
        )
    return target


def _competitor_urls(markdown: str) -> tuple[str, ...]:
    section: list[str] = []
    collecting = False
    for line in markdown.splitlines():
        if _HEADING_PATTERN.match(line):
            collecting = True
            continue
        if collecting and _NEXT_HEADING_PATTERN.match(line):
            break
        if collecting:
            section.append(line)
    normalized: list[str] = []
    for match in _DOMAIN_PATTERN.finditer("\n".join(section)):
        url = _normalize_url(match.group(0))
        if url not in normalized:
            normalized.append(url)
    return tuple(normalized)


def _normalize_url(raw: str) -> str:
    value = raw.rstrip(".,;:!?\"'")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.hostname.lower() == "localhost"
    ):
        raise KickoffPreflightError(
            "ERROR_COMPETITOR_URL_INVALID",
            "A competitor URL in the accepted intake is not a safe HTTP or HTTPS target.",
        )
    host = parsed.hostname.lower()
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", host, path, parsed.query, ""))


def _probe_competitor(url: str, opener: Callable[..., Any]) -> dict[str, Any]:
    https_result = _probe_once(url, opener)
    if https_result is not None:
        status, final_url = https_result
        return {
            "url": url,
            "status": "reachable_https",
            "http_status": status,
            "final_url": final_url,
            "warning_code": None,
            "error_code": None,
        }
    parsed = urlsplit(url)
    http_url = urlunsplit(("http", parsed.netloc, parsed.path, parsed.query, ""))
    http_result = _probe_once(http_url, opener)
    if http_result is not None:
        status, final_url = http_result
        return {
            "url": url,
            "status": "reachable_http_only",
            "http_status": status,
            "final_url": final_url,
            "warning_code": "WARN_COMPETITOR_HTTPS_UNAVAILABLE",
            "error_code": None,
        }
    return {
        "url": url,
        "status": "unavailable",
        "http_status": None,
        "final_url": None,
        "warning_code": "WARN_COMPETITOR_UNAVAILABLE",
        "error_code": None,
    }


def _probe_once(url: str, opener: Callable[..., Any]) -> tuple[int, str] | None:
    request = Request(
        url,
        method="HEAD",
        headers={"User-Agent": "Heartweb-Kickoff-Preflight/1.0"},
    )
    try:
        with opener(request, timeout=10.0) as response:
            status = getattr(response, "status", None)
            final_url = response.geturl()
    except HTTPError as error:
        status = error.code
        final_url = error.geturl()
    except (URLError, TimeoutError, OSError):
        return None
    if not isinstance(status, int) or isinstance(status, bool) or not isinstance(final_url, str):
        return None
    return status, final_url


def _artifact_defaults(manifest_schema: Mapping[str, Any]) -> dict[str, str]:
    properties = manifest_schema.get("properties")
    artifacts = properties.get("artifacts") if isinstance(properties, dict) else None
    if isinstance(artifacts, dict) and isinstance(artifacts.get("$ref"), str):
        reference = artifacts["$ref"]
        if not reference.startswith("#/$defs/"):
            raise KickoffPreflightError(
                "ERROR_MANIFEST_SCHEMA_INVALID",
                "The registered manifest artifact contract must use a local schema reference.",
            )
        definitions = manifest_schema.get("$defs")
        artifacts = definitions.get(reference.removeprefix("#/$defs/")) if isinstance(definitions, dict) else None
    artifact_properties = artifacts.get("properties") if isinstance(artifacts, dict) else None
    if not isinstance(artifact_properties, dict) or not artifact_properties:
        raise KickoffPreflightError(
            "ERROR_MANIFEST_SCHEMA_INVALID",
            "The registered manifest schema has no artifact path contract.",
        )
    defaults = {
        key: value.get("default")
        for key, value in artifact_properties.items()
        if isinstance(value, dict) and isinstance(value.get("default"), str)
    }
    if len(defaults) != len(artifact_properties):
        raise KickoffPreflightError(
            "ERROR_MANIFEST_SCHEMA_INVALID",
            "Every registered manifest artifact path requires one string default.",
        )
    return defaults


def _json_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise KickoffPreflightError(code, "A canonical Step 0 reference document is unreadable.") from error
    if not isinstance(value, dict):
        raise KickoffPreflightError(code, "A canonical Step 0 reference document is not an object.")
    return value


def _required_string(value: Mapping[str, Any], key: str, code: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise KickoffPreflightError(code, f"The selected deployment has no valid {key}.")
    return result


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
